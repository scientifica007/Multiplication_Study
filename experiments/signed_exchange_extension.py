"""Round 20: optional signed role-exchange on full typed receipts.

Native multiplication: A x B -> C ONLY; outputs retain both typed inputs.
Rotation on C is an ADDITIONAL unary map, not the original multiplication.
The quadratic ring below is a separate algebra of readings, not a new
native C x C product. All arithmetic is exact, over rational labels.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Factor:
    sort: str
    value: Fraction

    def __post_init__(self):
        if self.sort not in ('A', 'B'):
            raise ValueError('Factors must be of sorts A or B')
        object.__setattr__(self, 'value', Fraction(self.value))


@dataclass(frozen=True)
class Receipt:
    a: Factor
    b: Factor

    def __post_init__(self):
        if self.a.sort != 'A' or self.b.sort != 'B':
            raise ValueError('A first, B second')


@dataclass(frozen=True)
class CQuantity:
    terms: tuple[Receipt, ...]
    sort: str = 'C'

    def __post_init__(self):
        if self.terms != tuple(sorted(self.terms, key=receipt_key)):
            raise ValueError('Canonical finite multiset of complete receipts needed')


def receipt_key(p: Receipt):
    return p.a.value, p.b.value


def make(a, b) -> CQuantity:
    return CQuantity((Receipt(Factor('A', a), Factor('B', b)),))


def star(a: Factor, b: Factor) -> CQuantity | None:
    if not isinstance(a, Factor) or not isinstance(b, Factor):
        return None
    if a.sort != 'A' or b.sort != 'B':
        return None
    return CQuantity((Receipt(a, b),))


def unpack(x: CQuantity):
    if not isinstance(x, CQuantity) or len(x.terms) != 1:
        return None
    p = x.terms[0]
    return p.a, p.b


def add(x, y):
    if isinstance(x, Factor) and isinstance(y, Factor) and x.sort == y.sort:
        return Factor(x.sort, x.value + y.value)
    if isinstance(x, CQuantity) and isinstance(y, CQuantity):
        return CQuantity(tuple(sorted(x.terms + y.terms, key=receipt_key)))
    return None


def native_reading(x: CQuantity) -> Fraction:
    return sum((p.a.value * p.b.value for p in x.terms), Fraction())


def signed_exchange(x: CQuantity, kappa: int = -1) -> CQuantity:
    """Optional role-transport P(a,b) -> P(kappa*b,a), extended additively.

    For kappa=-1 it has fourth power identity on C; for kappa=+1,
    second power identity; for kappa=0 it is not bijective.
    """
    if not isinstance(x, CQuantity) or kappa not in (-1, 0, 1):
        raise ValueError('Valid C receipt and kappa=-1,0,1 required')
    return CQuantity(tuple(sorted((Receipt(Factor('A', kappa*p.b.value),
                                           Factor('B', p.a.value))
                                   for p in x.terms), key=receipt_key)))


def iterate_exchange(x: CQuantity, n: int, kappa: int = -1) -> CQuantity:
    if not isinstance(n, int) or n < 0:
        raise ValueError('Nonnegative integer iteration required')
    for _ in range(n):
        x = signed_exchange(x, kappa)
    return x


@dataclass(frozen=True)
class Pair:
    x: Fraction
    y: Fraction

    def __post_init__(self):
        object.__setattr__(self, 'x', Fraction(self.x))
        object.__setattr__(self, 'y', Fraction(self.y))

    def __add__(self, other: 'Pair') -> 'Pair':
        return Pair(self.x + other.x, self.y + other.y)

    def __neg__(self) -> 'Pair':
        return Pair(-self.x, -self.y)

    def __sub__(self, other: 'Pair') -> 'Pair':
        return self + -other

    def __rmul__(self, scalar: int | Fraction) -> 'Pair':
        return Pair(Fraction(scalar)*self.x, Fraction(scalar)*self.y)


def multiply_pair(a: Pair, b: Pair, kappa: int) -> Pair:
    """Product in external quadratic algebra Q[u]/(u^2-kappa)."""
    if kappa not in (-1, 0, 1):
        raise ValueError('Only the three comparison algebras are implemented')
    return Pair(a.x*b.x + kappa*a.y*b.y, a.x*b.y + a.y*b.x)


def pair_exchange(a: Pair, kappa: int) -> Pair:
    return Pair(kappa*a.y, a.x)


def coordinate_reading(x: CQuantity) -> Pair:
    """Optional additive *coordinate* reading; NOT the product reading ab."""
    return Pair(sum((p.a.value for p in x.terms),Fraction()),
                sum((p.b.value for p in x.terms),Fraction()))


def real_embed_product_reading(x: CQuantity) -> Pair:
    return Pair(native_reading(x), 0)


J = Pair(0, 1)
ONE = Pair(1, 0)
ZERO = Pair(0, 0)


def demo():
    p = make(1, 1)
    for kappa in (-1, 0, 1):
        print('kappa', kappa, 'signed orbit',
              [unpack(iterate_exchange(p, i, kappa)) for i in range(5)])
        print('  u*u = ', multiply_pair(J, J, kappa))
    p = make(-1, -1)
    print('P(-1,-1) native product reading',native_reading(p),
          '; coordinate reading',coordinate_reading(p))


if __name__ == '__main__':
    demo()
