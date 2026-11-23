"""Optional oriented-area structure on two typed-factor coordinate axes.

The native product A x B -> C stores ordered operands.  An alternating area
form on V=A⊕B and any coordinate transport are EXTRA assumptions, not
consequences of the founding typed-multiplication axioms.

All numerical work is exact over the rationals.  The signed free abelian
receipt group is separate from the original commutative monoid of histories.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Vector:
    a: Fraction
    b: Fraction

    def __post_init__(self):
        object.__setattr__(self, 'a', Fraction(self.a))
        object.__setattr__(self, 'b', Fraction(self.b))

    def __add__(self, other: Vector) -> Vector:
        return Vector(self.a + other.a, self.b + other.b)

    def __neg__(self) -> Vector:
        return Vector(-self.a, -self.b)

    def __rmul__(self, scalar: Fraction | int) -> Vector:
        return Vector(Fraction(scalar) * self.a, Fraction(scalar) * self.b)


EA, EB = Vector(1, 0), Vector(0, 1)


def omega(u: Vector, v: Vector, scale: Fraction | int = 1) -> Fraction:
    """External nondegenerate alternating bilinear form if scale != 0."""
    return Fraction(scale) * (u.a * v.b - u.b * v.a)


@dataclass(frozen=True)
class Matrix:
    a: Fraction
    b: Fraction
    c: Fraction
    d: Fraction

    def __post_init__(self):
        for key in ('a', 'b', 'c', 'd'):
            object.__setattr__(self, key, Fraction(getattr(self, key)))

    @property
    def determinant(self) -> Fraction:
        return self.a * self.d - self.b * self.c

    def __call__(self, v: Vector) -> Vector:
        return Vector(self.a * v.a + self.b * v.b,
                      self.c * v.a + self.d * v.b)

    def __matmul__(self, other: Matrix) -> Matrix:
        return Matrix(self.a * other.a + self.b * other.c,
                      self.a * other.b + self.b * other.d,
                      self.c * other.a + self.d * other.c,
                      self.c * other.b + self.d * other.d)

    def inverse(self) -> Matrix:
        det = self.determinant
        if det == 0:
            raise ZeroDivisionError('Singular transformation')
        return Matrix(self.d / det, -self.b / det,
                      -self.c / det, self.a / det)

    def signed_area_preserving(self) -> bool:
        return self.determinant == 1

    def absolute_area_preserving(self) -> bool:
        return abs(self.determinant) == 1

    def orientation_preserving(self) -> bool:
        return self.determinant > 0

    def euclidean_metric_preserving(self) -> bool:
        # Columns are orthonormal in the separately added standard metric.
        return (self.a * self.a + self.c * self.c == 1
                and self.b * self.b + self.d * self.d == 1
                and self.a * self.b + self.c * self.d == 0)


IDENTITY = Matrix(1, 0, 0, 1)
MINUS_IDENTITY = Matrix(-1, 0, 0, -1)
J_STANDARD = Matrix(0, -1, 1, 0)


def swap(alpha: Fraction | int, beta: Fraction | int) -> Matrix:
    """Extra role transport: (a,b) -> (alpha*b, beta*a)."""
    return Matrix(0, alpha, beta, 0)


def normalized_swap(kappa: Fraction | int) -> Matrix:
    return swap(kappa, 1)


@dataclass(frozen=True, order=True)
class TypedFactor:
    sort: str
    amount: Fraction

    def __post_init__(self):
        if self.sort not in ('A', 'B'):
            raise ValueError('Only A or B factor is admitted')
        object.__setattr__(self, 'amount', Fraction(self.amount))


@dataclass(frozen=True, order=True)
class Receipt:
    left: TypedFactor
    right: TypedFactor

    def __post_init__(self):
        if self.left.sort != 'A' or self.right.sort != 'B':
            raise ValueError('Native product only from A to B')

    @property
    def reading(self) -> Fraction:
        return self.left.amount * self.right.amount

    def unpack(self) -> tuple[TypedFactor, TypedFactor]:
        return self.left, self.right


def product(x: TypedFactor, y: TypedFactor) -> Receipt | None:
    if not isinstance(x, TypedFactor) or not isinstance(y, TypedFactor):
        return None
    return Receipt(x, y) if (x.sort, y.sort) == ('A', 'B') else None


def receipt(a, b) -> Receipt:
    return Receipt(TypedFactor('A', a), TypedFactor('B', b))


def transform_receipt(p: Receipt, t: Matrix) -> Receipt:
    """Only valid if the matrix interchanges the pure A and B axes."""
    if t.a != 0 or t.d != 0:
        raise ValueError('This operation models a role exchange only')
    return receipt(t.b * p.right.amount, t.c * p.left.amount)


@dataclass(frozen=True)
class FormalReceiptSum:
    """Free ABELIAN group of signed *formal* receipt generators.

    A negative coefficient is not a native C multiset subtraction.
    """
    coefficients: tuple[tuple[Receipt, int], ...]

    @classmethod
    def from_items(cls, items) -> FormalReceiptSum:
        d: dict[Receipt, int] = {}
        for p, n in items:
            if type(n) is not int:
                raise TypeError('Formal coefficient must be integer')
            d[p] = d.get(p, 0) + n
        return cls(tuple(sorted((p, n) for p, n in d.items() if n)))

    def __add__(self, other: FormalReceiptSum) -> FormalReceiptSum:
        return self.from_items(self.coefficients + other.coefficients)

    def __neg__(self) -> FormalReceiptSum:
        return self.from_items((p, -n) for p, n in self.coefficients)

    def __sub__(self, other: FormalReceiptSum) -> FormalReceiptSum:
        return self + -other

    def read(self) -> Fraction:
        return sum((n * p.reading for p, n in self.coefficients), Fraction())


def formal_basis(a, b) -> FormalReceiptSum:
    return FormalReceiptSum.from_items(((receipt(a, b), 1),))


def formal_wedge(u: Vector, v: Vector) -> FormalReceiptSum:
    """Alternating, but NOT bilinear before quotienting receipt provenance."""
    return formal_basis(u.a, v.b) - formal_basis(v.a, u.b)


def demo() -> None:
    for alpha, beta in ((-1, 1), (1, 1), (-2, 1), (-2, Fraction(1, 2))):
        t = swap(alpha, beta)
        print(f'alpha={alpha}, beta={beta}: det={t.determinant}, '
              f'area={t.signed_area_preserving()}, square={t@t}')
    print('base oriented area', omega(EA, EB))
    print('standard rotation preserves numeric area',
          omega(J_STANDARD(EA), J_STANDARD(EB)))
    print('but formal receipt areas differ',
          formal_wedge(EA, EB) != formal_wedge(J_STANDARD(EA), J_STANDARD(EB)))


if __name__ == '__main__':
    demo()
