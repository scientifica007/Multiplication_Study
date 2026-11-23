"""Exact provenance-to-bilinearity quotient certificates (round 22).

Native typed A x B -> C receipts are independent symbols. F is an EXTRA
free Q-vector space on these symbols, not the native commutative monoid C.

Raw W(u,v) = [P(u.a,v.b)] - [P(v.a,u.b)] is alternating but NOT
bilinear in F. The least linear quotient making W bilinear is F/ker(chi),
where chi([P(a,b)])=(1,ab), a two-dimensional AFFINE-RECEIPT quotient.
If P itself must be bilinear, the least quotient is F/ker(value) ~= Q.

These are proof-motivated, exact rational computations, not general proof
checkers for unbounded spaces; see accompanying mathematical document.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from itertools import product


@dataclass(frozen=True)
class TypedFactor:
    sort: str
    amount: Fraction
    def __post_init__(self):
        if self.sort not in ('A', 'B'):
            raise ValueError('Expected A or B typed input')
        object.__setattr__(self, 'amount', Fraction(self.amount))


@dataclass(frozen=True, order=True)
class Receipt:
    a: Fraction
    b: Fraction
    def __post_init__(self):
        object.__setattr__(self, 'a', Fraction(self.a))
        object.__setattr__(self, 'b', Fraction(self.b))
    def unpack(self):
        return TypedFactor('A', self.a), TypedFactor('B', self.b)
    @property
    def reading(self):
        return self.a * self.b


def native_star(a: TypedFactor, b: TypedFactor) -> Receipt | None:
    if not isinstance(a, TypedFactor) or not isinstance(b, TypedFactor):
        return None
    return Receipt(a.amount, b.amount) if (a.sort, b.sort) == ('A', 'B') else None


@dataclass(frozen=True)
class FreeQ:
    """Finite formal Q-linear combinations of *distinct complete* receipts."""
    coefficients: tuple[tuple[Receipt, Fraction], ...]

    @staticmethod
    def from_terms(items) -> FreeQ:
        d: dict[Receipt, Fraction] = {}
        for p, c in items:
            if not isinstance(p, Receipt):
                raise TypeError('Only complete typed receipts are permitted')
            d[p] = d.get(p, Fraction(0)) + Fraction(c)
        return FreeQ(tuple(sorted((p, c) for p, c in d.items() if c)))

    def __add__(self, other: FreeQ) -> FreeQ:
        return FreeQ.from_terms(self.coefficients + other.coefficients)

    def __neg__(self) -> FreeQ:
        return FreeQ.from_terms((p, -c) for p, c in self.coefficients)

    def __sub__(self, other: FreeQ) -> FreeQ:
        return self + -other

    def scale(self, scalar) -> FreeQ:
        return FreeQ.from_terms((p, Fraction(scalar) * c) for p, c in self.coefficients)

    def __rmul__(self, scalar) -> FreeQ:
        return self.scale(scalar)

    @property
    def augmentation(self) -> Fraction:
        return sum((c for _, c in self.coefficients), Fraction(0))

    @property
    def product_reading(self) -> Fraction:
        return sum((c * p.reading for p, c in self.coefficients), Fraction(0))


FREE_ZERO = FreeQ.from_terms(())


def basis(a, b) -> FreeQ:
    return FreeQ.from_terms(((Receipt(a, b), 1),))


@dataclass(frozen=True)
class Vector:
    a: Fraction
    b: Fraction
    def __post_init__(self):
        object.__setattr__(self, 'a', Fraction(self.a))
        object.__setattr__(self, 'b', Fraction(self.b))
    def __add__(self, other: Vector) -> Vector:
        return Vector(self.a + other.a, self.b + other.b)
    def __rmul__(self, scalar) -> Vector:
        return Vector(Fraction(scalar) * self.a, Fraction(scalar) * self.b)


def raw_wedge(u: Vector, v: Vector) -> FreeQ:
    return basis(u.a, v.b) - basis(v.a, u.b)


def area(u: Vector, v: Vector) -> Fraction:
    return u.a * v.b - v.a * u.b


def affine_class(x: FreeQ) -> tuple[Fraction, Fraction]:
    """Universal quotient for bilinearity of W only: (receipt count, value)."""
    return x.augmentation, x.product_reading


def strict_bilinear_class(x: FreeQ) -> Fraction:
    """Universal quotient when P(a,b) itself must be Q-bilinear."""
    return x.product_reading


def affine_normal_form(x: FreeQ) -> FreeQ:
    """Representative e*count + t*value, e=P00, t=P11-P00."""
    n, v = affine_class(x)
    e = basis(0, 0)
    t = basis(1, 1) - e
    return n * e + v * t


def bilinear_p_relation(a, a2, b) -> FreeQ:
    return basis(Fraction(a) + Fraction(a2), b) - basis(a, b) - basis(a2, b)


def wedge_additivity_defect(u: Vector, u2: Vector, v: Vector) -> FreeQ:
    return raw_wedge(u + u2, v) - raw_wedge(u, v) - raw_wedge(u2, v)


def wedge_homogeneity_defect(scalar, u: Vector, v: Vector) -> FreeQ:
    return raw_wedge(Fraction(scalar) * u, v) - Fraction(scalar) * raw_wedge(u, v)


def universal_affine_relation(a, b) -> FreeQ:
    """Relation forced by Q-bilinearity of W; it vanishes in the quotient."""
    x = basis(a, b)
    e = basis(0, 0)
    t = basis(1, 1) - e
    return x - e - Fraction(a) * Fraction(b) * t


def matrix_rank(rows, cols: int) -> int:
    """Fraction-exact Gauss elimination; independent finite certificate."""
    m = [list(map(Fraction, row)) for row in rows]
    if any(len(row) != cols for row in m):
        raise ValueError('Wrong row width')
    rank = 0
    for j in range(cols):
        pivot = next((i for i in range(rank, len(m)) if m[i][j] != 0), None)
        if pivot is None:
            continue
        m[rank], m[pivot] = m[pivot], m[rank]
        leading = m[rank][j]
        m[rank] = [x / leading for x in m[rank]]
        for i in range(rank + 1, len(m)):
            factor = m[i][j]
            if factor:
                m[i] = [x - factor * y for x, y in zip(m[i], m[rank])]
        rank += 1
    return rank


def finite_presentation_ranks(labels=(-2, -1, 0, 1, 2)) -> tuple[int, int, int]:
    """Finite sample: rank of affine W-relations, and after P00=0.

    Relations come from the universal algebraic proof; their finite ranks
    verify consistency of 2D vs 1D presentations on the selected grid.
    """
    labels = tuple(Fraction(x) for x in labels)
    if 0 not in labels or 1 not in labels or len(labels) != len(set(labels)):
        raise ValueError('Distinct grid labels including 0 and 1 required')
    receipts = tuple(Receipt(a, b) for a, b in product(labels, repeat=2))
    indices = {p: i for i, p in enumerate(receipts)}
    def row(x):
        ans = [Fraction(0)] * len(receipts)
        for p, c in x.coefficients:
            ans[indices[p]] += c
        return ans
    relations = [row(universal_affine_relation(a,b))
                 for a,b in product(labels, repeat=2)]
    affine_rank = matrix_rank(relations, len(receipts))
    strict_rank = matrix_rank(relations + [row(basis(0,0))], len(receipts))
    return len(receipts), affine_rank, strict_rank


def demo():
    x, y = basis(2, 3), basis(1, 6)
    print('Complete records distinct:', x != y)
    print('Affine W quotient collision:', affine_class(x), affine_class(y))
    print('P-bilinear quotient collision:', strict_bilinear_class(x), strict_bilinear_class(y))
    print('Pure zero-source receipt versus empty in affine quotient:',
          affine_class(basis(0, 7)), affine_class(FREE_ZERO))
    n, r1, r2 = finite_presentation_ranks()
    print(f'Finite grid generators={n}, relation ranks={r1},{r2}, quotient dimensions={n-r1},{n-r2}')


if __name__ == '__main__':
    demo()
