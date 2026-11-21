"""Count ordered binary multiplication trees of a fixed positive typed reading."""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from graphlib import CycleError, TopologicalSorter
from math import inf

from history_codes import divisors

State = tuple[str, int]
Pair = tuple[State, State]


def count_histories(target: State, atoms: Iterable[State],
                    rules: Mapping[tuple[str, str], str]) -> int | float:
    """Return zero, a finite exact count, or math.inf. Each given atom is one leaf."""
    candidate_amounts = set(divisors(target[1]))
    leaves = set(atoms)
    if any(type(n) is not int or n <= 0 for _, n in leaves):
        raise ValueError("This classification requires positive integer amounts")
    leaves = {s for s in leaves if s[1] in candidate_amounts}
    productions: dict[State, list[Pair]] = defaultdict(list)
    for (left, right), result in rules.items():
        if left == right:
            raise ValueError("A product requires different operand kinds")
        for n in candidate_amounts:
            for a in divisors(n):
                productions[result, n].append(((left, a), (right, n // a)))

    # Least fixed point: a cycle with no finished tree cannot be traversed.
    productive = leaves.copy()
    while True:
        new = {parent for parent, pairs in productions.items() if parent not in productive
               and any(a in productive and b in productive for a, b in pairs)}
        if not new:
            break
        productive.update(new)
    if target not in productive:
        return 0

    available: dict[State, list[Pair]] = {}
    dependencies: dict[State, set[State]] = {}
    pending = [target]
    while pending:
        parent = pending.pop()
        if parent in available:
            continue
        available[parent] = [(a, b) for a, b in productions[parent]
                             if a in productive and b in productive]
        children = {child for pair in available[parent] for child in pair}
        dependencies[parent] = children
        pending.extend(children - available.keys())

    try:
        order = tuple(TopologicalSorter(dependencies).static_order())
    except CycleError:
        return inf
    counts: dict[State, int] = {}
    for state in order:
        counts[state] = int(state in leaves) + sum(counts[a] * counts[b] for a, b in available[state])
    return counts[target]
