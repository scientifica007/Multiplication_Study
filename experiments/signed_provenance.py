"""Typed signed multiplication and provenance: finite checks, not proofs.

Research branch: research/signs-inverse-complex-2026-11-22.
Only A x B products are defined. Free additive receipt groups are separate.
"""
from dataclasses import dataclass
from math import isqrt


@dataclass(frozen=True, order=True)
class Atom:
    sort: str
    amount: int

    def __post_init__(self):
        if self.sort not in ('A', 'B') or not isinstance(self.amount, int):
            raise ValueError('Expected a typed integer of sort A or B')


@dataclass(frozen=True, order=True)
class Receipt:
    left: Atom
    right: Atom

    def __post_init__(self):
        if self.left.sort != 'A' or self.right.sort != 'B':
            raise ValueError('Only ordered products A x B are admissible')


def typed_add(a: Atom, b: Atom) -> Atom:
    if a.sort != b.sort:
        raise ValueError('Cross-sort addition is undefined')
    return Atom(a.sort, a.amount + b.amount)


def multiply(a: Atom, b: Atom) -> Receipt:
    return Receipt(a, b)


def unpack(receipt: Receipt) -> tuple[Atom, Atom]:
    if not isinstance(receipt, Receipt):
        raise TypeError('Only a single elementary receipt can be unpacked')
    return receipt.left, receipt.right


def measure(receipt: Receipt) -> int:
    return receipt.left.amount * receipt.right.amount


def basis(receipt: Receipt) -> dict[Receipt, int]:
    return {receipt: 1}


def formal_add(x: dict, y: dict) -> dict:
    out = dict(x)
    for key, coefficient in y.items():
        out[key] = out.get(key, 0) + coefficient
        if not out[key]:
            del out[key]
    return out


def formal_neg(x: dict) -> dict:
    return {key: -coefficient for key, coefficient in x.items() if coefficient}


def formal_measure(x: dict[Receipt, int]) -> int:
    return sum(coefficient * measure(r) for r, coefficient in x.items())


def signed_factor_pairs(p: int) -> tuple[tuple[int, int], ...]:
    """All integer pairs (m,n) with m*n=p; p must be nonzero."""
    if p == 0:
        raise ValueError('Zero has infinitely many factor pairs over Z')
    positive_divisors = set()
    for d in range(1, isqrt(abs(p)) + 1):
        if p % d == 0:
            positive_divisors.add(d)
            positive_divisors.add(abs(p) // d)
    pairs = [(sign * d, p // (sign * d))
             for d in sorted(positive_divisors) for sign in (-1, 1)]
    return tuple(pairs)


def aggregate_fiber_size(k: int, observed: int) -> int:
    """Unordered k unit-sign receipts; observe (number k, signed sum)."""
    if k < 0 or abs(observed) > k or (k - observed) % 2:
        return 0
    positives = (k + observed) // 2
    negatives = k - positives
    return (positives + 1) * (negatives + 1)


def one_sided_multiply(a: Atom, b: Atom) -> dict[int, int]:
    """Injective if b != 0, additive in B where every term is defined.

    Each key is an A value, each coefficient a B value.
    This is a second model, not the same receipt constructor as multiply().
    """
    if a.sort != 'A' or b.sort != 'B' or b.amount == 0:
        raise ValueError('Requires A x (B without zero)')
    return {a.amount: b.amount}


def one_sided_unpack(result: dict[int, int]) -> tuple[Atom, Atom]:
    if len(result) != 1:
        raise ValueError('Requires one nonzero basis coefficient')
    (a, b), = result.items()
    if not b:
        raise ValueError('Zero cannot be decoded')
    return Atom('A', a), Atom('B', b)


if __name__ == '__main__':
    for a in (-1, 1):
        for b in (-1, 1):
            print(f'{a:+d}_A * {b:+d}_B -> receipt ({a:+d},{b:+d}), measure {a*b:+d}')
    print('signed factors of 12:', len(signed_factor_pairs(12)))
    print('two receipts, observed zero:', aggregate_fiber_size(2, 0))
