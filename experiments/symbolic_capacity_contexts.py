"""Exact symbolic contextual quotients for bounded typed signed-product sums.

C consists of commutative multisets of at most capacity first-stage records
A_a * B_b, retaining their ordered signed operands. Addition is partial at
capacity. Four optional C*D partial guards (seal/inspect/homA/homB) and an
E*F confirm guard are observable, but full product unpacking is not.

The cap is an EXTRA experimental assumption; these results are not deduced
from the project's founding axioms. Unlimited-sum quotient is separate.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from itertools import combinations_with_replacement
from typing import TypeAlias

A_VALUES = (-3, -2, -1, 1, 2, 3)
B_VALUES = (-6, -3, -2, 2, 3, 6)

@dataclass(frozen=True)
class SourceReceipt:
    a: int
    b: int
    @property
    def reading(self) -> int:
        return self.a * self.b
    def unpack(self) -> tuple[tuple[str, int], tuple[str, int]]:
        return (('A', self.a), ('B', self.b))

ATOMS = tuple(SourceReceipt(a,b) for a in A_VALUES for b in B_VALUES)
Hist: TypeAlias = tuple[int, ...]  # Sorted atom indices; repeated indices allowed
Status: TypeAlias = tuple[str, ...]
Summary: TypeAlias = tuple[int, Status, Status, bool | None, bool | None]
EMPTY: Hist = ()


def histories_by_length(capacity: int) -> tuple[tuple[Hist, ...], ...]:
    if type(capacity) is not int or capacity < 0:
        raise ValueError('Capacity must be a nonnegative integer')
    return tuple(tuple(combinations_with_replacement(range(len(ATOMS)), length))
                 for length in range(capacity + 1))


def append_atom(hist: Hist, index: int, *, capacity: int | None = None) -> Hist | None:
    if type(index) is not int or not 0 <= index < len(ATOMS):
        raise ValueError('Unknown signed typed product')
    if capacity is not None and len(hist) >= capacity:
        return None
    at = 0
    while at < len(hist) and hist[at] <= index:
        at += 1
    return hist[:at] + (index,) + hist[at:]


def add_hist(x: Hist, y: Hist, *, capacity: int | None = None) -> Hist | None:
    if capacity is not None and len(x) + len(y) > capacity:
        return None
    # Canonical multiset addition; no order-of-summation provenance is claimed.
    return tuple(sorted(x+y))


def direct_profile(hist: Hist, *, source_probes: bool = True) -> tuple:
    """Observable C reading, four C*D guards and subsequent confirm legality."""
    receipts = tuple(ATOMS[i] for i in hist)
    reading = sum(c.reading for c in receipts)
    source_a = {c.a for c in receipts}
    source_b = {c.b for c in receipts}
    hom_a = len(source_a) == 1
    hom_b = len(source_b) == 1
    seal = hom_a and all(c.b % 2 == 0 for c in receipts)
    inspect = hom_b and all(c.a % 2 == 0 for c in receipts)
    confirm = seal and source_a == {1}
    if source_probes:
        return (reading, seal, inspect, hom_a, hom_b, confirm)
    return (reading, seal, inspect, confirm)


def source_status(sources: set[int]) -> Status:
    if not sources:
        return ('empty',)
    if len(sources) == 1:
        return ('single', next(iter(sources)))
    return ('mixed',)


def unlimited_summary(hist: Hist) -> Summary:
    """Minimal contextual quotient for UNBOUNDED C addition and the four probes."""
    receipts = tuple(ATOMS[i] for i in hist)
    sa = source_status({p.a for p in receipts})
    sb = source_status({p.b for p in receipts})
    even_a = all(p.a % 2 == 0 for p in receipts) if sb[0] == 'single' else None
    even_b = all(p.b % 2 == 0 for p in receipts) if sa[0] == 'single' else None
    return (sum(p.reading for p in receipts), sa, sb, even_a, even_b)


def merge_status(a: Status, b: Status) -> Status:
    if a[0] == 'empty':
        return b
    if b[0] == 'empty':
        return a
    if a[0] == 'mixed' or b[0] == 'mixed':
        return ('mixed',)
    return a if a == b else ('mixed',)


def merge_even(xstatus: Status, ystatus: Status,
               xeven: bool | None, yeven: bool | None, merged_status: Status):
    if merged_status[0] != 'single':
        return None
    if xstatus[0] == 'empty':
        return yeven
    if ystatus[0] == 'empty':
        return xeven
    if xeven is None or yeven is None:
        raise AssertionError('Missing relevant parity information')
    return xeven and yeven


def merge_unlimited_summaries(q: Summary, r: Summary) -> Summary:
    """Monoid addition on reachable unbounded provenance summaries."""
    v, sa, sb, ea, eb = q
    w, ta, tb, fa, fb = r
    na, nb = merge_status(sa,ta), merge_status(sb,tb)
    return (v+w, na, nb,
            merge_even(sb, tb, ea, fa, nb),
            merge_even(sa, ta, eb, fb, na))


def profile_from_unlimited_summary(q: Summary, *, source_probes=True) -> tuple:
    v, sa, sb, ea, eb = q
    ha = sa[0] == 'single'; hb = sb[0] == 'single'
    seal = ha and eb is True
    inspect = hb and ea is True
    conf = seal and sa == ('single',1)
    return (v,seal,inspect,ha,hb,conf) if source_probes else (v,seal,inspect,conf)


@dataclass
class Quotient:
    capacity: int
    source_probes: bool
    layers: tuple[tuple[Hist,...],...]
    block: dict[Hist, tuple[int,int]]
    counts: tuple[int,...]

    @property
    def total(self) -> int:
        return sum(self.counts)

    @property
    def state_count(self) -> int:
        return sum(len(layer) for layer in self.layers)

    def same(self, x: Hist, y: Hist) -> bool:
        return self.block[x] == self.block[y]


def bounded_contextual_quotient(capacity: int, *, source_probes=True) -> Quotient:
    """Exact bottom-up Myhill-Nerode-style quotient for a capacity-limited sum.

    A state of length n is classified by current probe observations plus the
    36 equivalence classes reached by appending one signed typed receipt.
    Full states have no nonempty append transitions. Length itself is
    observable under repeated definedness testing and is included in ID.
    """
    layers = histories_by_length(capacity)
    ids: dict[Hist, tuple[int,int]] = {}
    counts = [0]*(capacity+1)
    for n in range(capacity,-1,-1):
        seen: dict[tuple,int] = {}
        for x in layers[n]:
            observation = direct_profile(x,source_probes=source_probes)
            next_ids = (tuple(ids[append_atom(x,i)] for i in range(len(ATOMS)))
                        if n < capacity else ())
            key = (observation,next_ids)
            if key not in seen:
                seen[key] = len(seen)
            ids[x] = (n,seen[key])
        counts[n] = len(seen)
    return Quotient(capacity,source_probes,layers,ids,tuple(counts))


def verify_generator_congruence(q: Quotient) -> bool:
    """Independent quotient validity check for every single-atom context."""
    groups: dict[tuple[int,int],list[Hist]] = defaultdict(list)
    for layer in q.layers:
        for x in layer:
            groups[q.block[x]].append(x)
    for group in groups.values():
        representative = group[0]
        old_reading = direct_profile(representative,source_probes=q.source_probes)
        for x in group:
            if direct_profile(x,source_probes=q.source_probes) != old_reading:
                return False
        for i in range(len(ATOMS)):
            target = append_atom(representative,i,capacity=q.capacity)
            ref = None if target is None else q.block[target]
            for x in group[1:]:
                candidate = append_atom(x,i,capacity=q.capacity)
                got = None if candidate is None else q.block[candidate]
                if got != ref:
                    return False
    return True


def distinguish_by_capacity(x: Hist, y: Hist, capacity: int) -> tuple[int,...] | None:
    """Shortest sufficiency witness for differing lengths, via append legality."""
    if len(x) == len(y):
        return None
    larger = max(len(x),len(y))
    return (0,)*(capacity-larger+1)


def summary_classes_on_prefix(capacity: int) -> int:
    layers = histories_by_length(capacity)
    return len({unlimited_summary(x) for layer in layers for x in layer})


def report():
    for c in (1,2,3):
        layers = histories_by_length(c)
        for probes in (False,True):
            q = bounded_contextual_quotient(c,source_probes=probes)
            assert verify_generator_congruence(q)
            print(f'H={c} source_probes={probes} states={q.state_count} '
                  f'classes={q.total} by_length={q.counts}')
        print(f'  unbounded_summary_distinct_on_this_finite_prefix={summary_classes_on_prefix(c)}')

if __name__ == '__main__':
    report()
