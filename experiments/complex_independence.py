"""Typed multiplication receipts over Q or Q(i), without changing core axioms.

The operation 'star' is ONLY A x B -> C. Scalar-field multiplication is
an additional algebra of READINGS, NOT the native typed 'star' operation.
The construction works for every field K of characteristic zero, with C the
free commutative monoid of finite multisets of receipts from K x K.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True, order=True)
class GaussQ:
    real: Fraction = Fraction(0)
    imag: Fraction = Fraction(0)

    def __post_init__(self):
        object.__setattr__(self, 'real', Fraction(self.real))
        object.__setattr__(self, 'imag', Fraction(self.imag))

    def __add__(self, other: 'GaussQ') -> 'GaussQ':
        return GaussQ(self.real + other.real, self.imag + other.imag)

    def __neg__(self) -> 'GaussQ':
        return GaussQ(-self.real, -self.imag)

    def __sub__(self, other: 'GaussQ') -> 'GaussQ':
        return self + -other

    def __mul__(self, other: 'GaussQ') -> 'GaussQ':
        return GaussQ(self.real*other.real - self.imag*other.imag,
                      self.real*other.imag + self.imag*other.real)

    def inverse(self) -> 'GaussQ':
        norm2 = self.real*self.real + self.imag*self.imag
        if norm2 == 0:
            raise ZeroDivisionError('Zero scalar has no multiplicative inverse')
        return GaussQ(self.real/norm2, -self.imag/norm2)

    def __truediv__(self, other: 'GaussQ') -> 'GaussQ':
        return self * other.inverse()

ZERO, ONE, MINUS_ONE, I = GaussQ(), GaussQ(1), GaussQ(-1), GaussQ(0,1)


@dataclass(frozen=True)
class ScalarField:
    name: str  # 'Q' or 'Qi'

    def __post_init__(self):
        if self.name not in ('Q','Qi'):
            raise ValueError('Choose Q (rationals) or Qi (Gaussian rationals)')

    def member(self, z: GaussQ) -> bool:
        return isinstance(z, GaussQ) and (self.name == 'Qi' or z.imag == 0)

    def require(self, z: GaussQ) -> GaussQ:
        if not self.member(z):
            raise ValueError('Scalar not contained in this reading field')
        return z

    def root_of_minus_one(self) -> GaussQ | None:
        """Mathematically certified by the proofs in the companion report.

        Q has no such root (a rational square is nonnegative); Qi has I.
        This is not a finite-search decision procedure for arbitrary fields.
        """
        return I if self.name == 'Qi' else None


@dataclass(frozen=True)
class Factor:
    sort: str
    scalar: GaussQ

    def __post_init__(self):
        if self.sort not in ('A','B'):
            raise ValueError('A native factor must have type A or B')


@dataclass(frozen=True, order=True)
class Receipt:
    left: Factor
    right: Factor

    def __post_init__(self):
        if self.left.sort != 'A' or self.right.sort != 'B':
            raise ValueError('Only ordered A x B products are native')


@dataclass(frozen=True)
class CQuantity:
    terms: tuple[Receipt,...]
    sort: str = 'C'

    def __post_init__(self):
        if not all(isinstance(r,Receipt) for r in self.terms):
            raise ValueError('C sums contain complete A x B receipts')
        if self.terms != tuple(sorted(self.terms, key=receipt_sort_key)):
            raise ValueError('C multiset terms must be in canonical order')


def receipt_sort_key(r: Receipt) -> tuple[Fraction,...]:
    return (r.left.scalar.real,r.left.scalar.imag,
            r.right.scalar.real,r.right.scalar.imag)


class NativeTypedModel:
    def __init__(self, field: ScalarField):
        self.field = field

    def factor(self, sort: str, value: GaussQ) -> Factor:
        if sort not in ('A','B'):
            raise ValueError('Only A and B factor sorts exist')
        return Factor(sort,self.field.require(value))

    def empty_c(self) -> CQuantity:
        return CQuantity(())

    def star(self, x: object, y: object) -> CQuantity | None:
        if not isinstance(x,Factor) or not isinstance(y,Factor):
            return None
        if x.sort != 'A' or y.sort != 'B':
            return None
        self.field.require(x.scalar)
        self.field.require(y.scalar)
        return CQuantity((Receipt(x,y),))

    def add(self, x: object, y: object) -> Factor | CQuantity | None:
        if isinstance(x,Factor) and isinstance(y,Factor) and x.sort == y.sort:
            return self.factor(x.sort,self.field.require(x.scalar + y.scalar))
        if isinstance(x,CQuantity) and isinstance(y,CQuantity):
            return CQuantity(tuple(sorted(x.terms+y.terms,key=receipt_sort_key)))
        return None

    def unpack(self, x: object) -> tuple[Factor,Factor] | None:
        if isinstance(x,CQuantity) and len(x.terms)==1:
            return (x.terms[0].left,x.terms[0].right)
        return None

    def read(self, x: Factor | CQuantity) -> GaussQ:
        if isinstance(x,Factor):
            return self.field.require(x.scalar)
        if isinstance(x,CQuantity):
            total = ZERO
            for r in x.terms:
                total += r.left.scalar*r.right.scalar
            return self.field.require(total)
        raise TypeError('Unrecognised quantity')

    def scalar_multiply(self, x: GaussQ, y: GaussQ) -> GaussQ:
        """An external operation on readings, NOT original native star."""
        return self.field.require(self.field.require(x)*self.field.require(y))


def signed_receipts(model: NativeTypedModel) -> tuple[CQuantity,...]:
    return tuple(model.star(model.factor('A',GaussQ(a)),model.factor('B',GaussQ(b)))
                 for a in (1,-1) for b in (1,-1))


def demonstration() -> None:
    for name in ('Q','Qi'):
        m=NativeTypedModel(ScalarField(name))
        pairs=signed_receipts(m)
        assert len(set(pairs))==4
        print(f'{name}: four distinct signed records, readings {[m.read(x) for x in pairs]}')
        root=m.field.root_of_minus_one()
        print(f'{name}: root of x^2=-1 in reading field? {root is not None}')
        if root is not None:
            full=m.star(m.factor('A',root),m.factor('B',root))
            print('  typed A_i star B_i is fully unpackable, reading=',m.read(full))
            assert m.read(full)==MINUS_ONE


if __name__=='__main__':
    demonstration()
