"""Finite typed records; observationally minimal quotients for partial operations.

This is an ADDITIONAL model for research. It does not add distributivity to the
full receipt identity. A public measurement is not a full record equality.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product, combinations_with_replacement

A_LABELS = (-2, -1, 1, 2)
B_LABELS = (-3, -2, 2, 3)


@dataclass(frozen=True)
class Atom:
    sort: str
    value: int


@dataclass(frozen=True)
class FirstReceipt:
    left: Atom
    right: Atom
    sort: str = 'C'

    @property
    def amount(self) -> int:
        return self.left.value * self.right.value


@dataclass(frozen=True)
class CQuantity:
    terms: tuple[FirstReceipt, ...]
    sort: str = 'C'

    def __post_init__(self) -> None:
        if not all(isinstance(t, FirstReceipt) for t in self.terms):
            raise ValueError('A C sum consists only of complete A times B receipts')
        if self.terms != tuple(sorted(self.terms, key=lambda t: (t.left.value, t.right.value))):
            raise ValueError('C sums have canonical commutative term order')

    @property
    def amount(self) -> int:
        return sum(t.amount for t in self.terms)


@dataclass(frozen=True)
class Probe:
    name: str
    amount: int
    sort: str = 'D'


@dataclass(frozen=True)
class SecondReceipt:
    left: CQuantity
    right: Probe
    sort: str = 'E'

    @property
    def amount(self) -> int:
        return self.left.amount * self.right.amount


PROBES = (Probe('homogeneous-A', 2), Probe('homogeneous-B', 3))


def first_product(a: Atom, b: Atom) -> FirstReceipt:
    if not isinstance(a, Atom) or not isinstance(b, Atom) or a.sort != 'A' or b.sort != 'B':
        raise TypeError('Only differently typed A times B is defined')
    if a.value not in A_LABELS or b.value not in B_LABELS:
        raise ValueError('Operand value outside the finite model')
    return FirstReceipt(a, b)


def atomic(a: int, b: int) -> CQuantity:
    return quantity(first_product(Atom('A', a), Atom('B', b)))


def quantity(*terms: FirstReceipt) -> CQuantity:
    return CQuantity(tuple(sorted(terms, key=lambda t: (t.left.value, t.right.value))))


def add_c(x: CQuantity, y: CQuantity) -> CQuantity:
    if not isinstance(x, CQuantity) or not isinstance(y, CQuantity):
        raise TypeError('Addition requires two C quantities')
    return quantity(*(x.terms + y.terms))


def sources(x: CQuantity, which: str) -> frozenset[int]:
    if not isinstance(x, CQuantity) or which not in ('A', 'B'):
        raise TypeError('C quantity and A/B side required')
    if which == 'A':
        return frozenset(t.left.value for t in x.terms)
    return frozenset(t.right.value for t in x.terms)


def source_class(source: frozenset[int]) -> tuple:
    if not source:
        return ('empty',)
    if len(source) == 1:
        return ('single', next(iter(source)))
    return ('mixed',)


def merge_classes(left: tuple, right: tuple) -> tuple:
    if left == ('empty',):
        return right
    if right == ('empty',):
        return left
    if left == ('mixed',) or right == ('mixed',):
        return ('mixed',)
    return left if left == right else ('mixed',)


def summary(x: CQuantity) -> tuple:
    """The least public contextual quotient for the operations below."""
    return (x.amount, source_class(sources(x, 'A')), source_class(sources(x, 'B')))


def add_summaries(x: tuple, y: tuple) -> tuple:
    return (x[0] + y[0], merge_classes(x[1], y[1]), merge_classes(x[2], y[2]))


def second_product(x: CQuantity, d: Probe) -> SecondReceipt | None:
    """Definedness is observable; the FULL result retains (x,d) for unpacking."""
    if not isinstance(x, CQuantity) or not isinstance(d, Probe) or d not in PROBES:
        return None
    side = 'A' if d.name == 'homogeneous-A' else 'B'
    if len(sources(x, side)) != 1:
        return None
    return SecondReceipt(x, d)


def public_test(x: CQuantity, d: Probe) -> tuple[bool, int | None]:
    result = second_product(x, d)
    return (result is not None, None if result is None else result.amount)


def direct_signature(x: CQuantity) -> tuple:
    return (x.amount, tuple(public_test(x, p) for p in PROBES))


def probe_after_add(x: CQuantity, z: CQuantity) -> tuple:
    return direct_signature(add_c(x, z))


def unpack_product(result: FirstReceipt | SecondReceipt):
    if isinstance(result, (FirstReceipt, SecondReceipt)):
        return result.left, result.right
    raise ValueError('Only product receipts can be unpacked')


def all_atoms() -> tuple[CQuantity, ...]:
    return tuple(atomic(a, b) for a, b in product(A_LABELS, B_LABELS))


def finite_histories(generators: tuple[FirstReceipt, ...], max_length: int) -> tuple[CQuantity, ...]:
    if max_length < 0:
        raise ValueError('Nonnegative maximum required')
    return (quantity(),) + tuple(
        quantity(*terms) for length in range(1, max_length + 1)
        for terms in combinations_with_replacement(generators, length))


def quotient_is_safe_on_sample(values: tuple[CQuantity, ...], q, operations) -> bool:
    """Finite representative test of the exact definedness + output conditions.

    operations: iterable of (name, domain_function, public_output_function),
    which use the same C value as their argument. A returned None from domain
    means undefined. Public result is checked only when domain returns true.
    """
    for x, y in product(values, repeat=2):
        if q(x) != q(y):
            continue
        for _, admissible, outcome in operations:
            ax, ay = admissible(x), admissible(y)
            if ax != ay:
                return False
            if ax and outcome(x) != outcome(y):
                return False
    return True
