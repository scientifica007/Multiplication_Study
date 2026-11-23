"""Typed free-sum provenance and a partial homogeneous batch product.

This is an ADDITIONAL finite model, not a claimed derivation of the core axioms.
C-values are commutative multisets of complete first-product receipts. The
batch D operation checks left-factor homogeneity and preserves its C input.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product, combinations_with_replacement

A_LABELS = (-3, -2, -1, 1, 2, 3)
B_LABELS = (-6, -3, -2, 2, 3, 6)

@dataclass(frozen=True)
class Atom:
    sort: str
    label: int | str
    amount: int

@dataclass(frozen=True)
class CProduct:
    left: Atom
    right: Atom
    amount: int
    sort: str = 'C'

@dataclass(frozen=True)
class CValue:
    terms: tuple[CProduct, ...]
    sort: str = 'C'
    def __post_init__(self):
        if not all(isinstance(t, CProduct) for t in self.terms):
            raise ValueError('Only complete C product receipts are summable')
        if self.terms != tuple(sorted(self.terms, key=lambda t: (t.left.amount, t.right.amount))):
            raise ValueError('Use canonical commutative order for C-sums')
    @property
    def amount(self):
        return sum(t.amount for t in self.terms)

@dataclass(frozen=True)
class EProduct:
    left: CValue
    right: Atom
    amount: int
    sort: str = 'E'

@dataclass(frozen=True)
class ESum:
    terms: tuple[EProduct, ...]
    sort: str = 'E'
    @property
    def amount(self):
        return sum(t.amount for t in self.terms)


def atom_a(a: int) -> Atom:
    if type(a) is not int or a not in A_LABELS:
        raise ValueError('Invalid A label')
    return Atom('A', a, a)

def atom_b(b: int) -> Atom:
    if type(b) is not int or b not in B_LABELS:
        raise ValueError('Invalid B label')
    return Atom('B', b, b)

def atom_d() -> Atom:
    return Atom('D', 'homogeneous-batch', 2)


def first_product(a: Atom, b: Atom) -> CProduct | None:
    if not isinstance(a, Atom) or not isinstance(b, Atom) or a.sort != 'A' or b.sort != 'B':
        return None
    if a != atom_a(a.label) or b != atom_b(b.label):
        return None
    return CProduct(a, b, a.amount * b.amount)


def unpack_product(p: CProduct | EProduct):
    if not isinstance(p, (CProduct, EProduct)):
        raise ValueError('Only a product receipt has two product inputs')
    return p.left, p.right


def quantity(*receipts: CProduct) -> CValue:
    return CValue(tuple(sorted(receipts, key=lambda t: (t.left.amount, t.right.amount))))


def atomic(a: int, b: int) -> CValue:
    return quantity(first_product(atom_a(a), atom_b(b)))


def add_c(x: CValue, y: CValue) -> CValue:
    if not isinstance(x, CValue) or not isinstance(y, CValue):
        raise TypeError('Only equal-sort C quantities can be added')
    return quantity(*(x.terms + y.terms))


def support(x: CValue) -> frozenset[int]:
    return frozenset(t.left.label for t in x.terms)


def batch_product(x: CValue, d: Atom) -> EProduct | None:
    if not isinstance(x, CValue) or d != atom_d():
        return None
    if len(support(x)) != 1:
        return None
    return EProduct(x, d, x.amount * d.amount)


def add_e(x: EProduct, y: EProduct) -> ESum:
    if not isinstance(x, EProduct) or not isinstance(y, EProduct):
        raise TypeError('Only two E-product receipts are supported in this test')
    return ESum((x, y))


def direct_signature(x: CValue):
    """Reading and accept/deny of a direct homogeneous D product."""
    e = batch_product(x, atom_d())
    return x.amount, None if e is None else e.amount


def support_kind(x: CValue) -> tuple:
    identities = support(x)
    if not identities:
        return ('empty',)
    if len(identities) == 1:
        return ('single', next(iter(identities)))
    return ('mixed',)


def merge_kinds(x: tuple, y: tuple) -> tuple:
    if x == ('empty',): return y
    if y == ('empty',): return x
    if x == ('mixed',) or y == ('mixed',): return ('mixed',)
    return x if x == y else ('mixed',)


def sufficient_summary(x: CValue) -> tuple:
    return x.amount, support_kind(x)


def add_summaries(x: tuple, y: tuple) -> tuple:
    return x[0] + y[0], merge_kinds(x[1], y[1])


def finite_histories(generators: tuple[CProduct, ...], max_length: int) -> tuple[CValue, ...]:
    return (quantity(),) + tuple(
        quantity(*indices) for n in range(1, max_length + 1)
        for indices in combinations_with_replacement(generators, n))


def universe() -> tuple[CValue, ...]:
    return tuple(atomic(a,b) for a,b in product(A_LABELS, B_LABELS))


if __name__ == '__main__':
    x, y, z = atomic(3,2), atomic(-3,-2), atomic(3,2)
    print('x,y directly equal?', direct_signature(x) == direct_signature(y))
    print('x+z and y+z:', direct_signature(add_c(x,z)), direct_signature(add_c(y,z)))
    print('primary number of readings:', len({direct_signature(v) for v in universe()}))
    print('all-additive-context classes:', len({sufficient_summary(v) for v in universe()}))
