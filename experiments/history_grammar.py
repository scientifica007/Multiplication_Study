"""Count finite ordered derivation trees in a finite grammar with labelled leaves."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from graphlib import CycleError, TopologicalSorter
from itertools import pairwise
from math import inf

State = tuple[str, int]
Pair = tuple[State, State]
LeafAt = Callable[[State, int], State]


@dataclass(frozen=True)
class ProductTree:
    """A product keeps its ordered factors. Leaves are actual (kind, amount) pairs."""

    left: History
    right: History


History = State | ProductTree


@dataclass(frozen=True)
class Frame:
    """One edge of a derivation path, with the other factor already completed."""

    parent: State
    child: State
    slot: int  # Position of the open factor, 0 on the left and 1 on the right.
    sibling: History


def _fill(path: tuple[Frame, ...], tree: History) -> History:
    for frame in reversed(path):
        if frame.slot == 0:
            tree = ProductTree(tree, frame.sibling)
        else:
            tree = ProductTree(frame.sibling, tree)
    return tree


@dataclass(frozen=True)
class InfiniteFamily:
    anchor: State
    route: tuple[Frame, ...]  # Target to anchor.
    loop: tuple[Frame, ...]   # Anchor back to anchor, or empty for infinite inputs.
    _seed: History = field(repr=False)
    _leaf_at: LeafAt = field(repr=False, compare=False)

    @property
    def reason(self) -> str:
        return "productive_cycle" if self.loop else "infinite_inputs"

    def history(self, index: int) -> History:
        """Construct the indexed member; different indices give distinct full trees."""
        if type(index) is not int or index < 0:
            raise ValueError("A family index must be a nonnegative integer")
        if self.loop:
            tree = self._seed
            for _ in range(index):
                tree = _fill(self.loop, tree)
        else:
            tree = self._leaf_at(self.anchor, index)
        return _fill(self.route, tree)


@dataclass(frozen=True)
class Classification:
    count: int | float  # A nonnegative integer, or math.inf.
    example: History | None
    families: tuple[InfiniteFamily, ...] = ()


def distinct_atoms(atoms: Iterable[State]) -> set[State]:
    leaves = set()
    for kind, n in atoms:
        if type(n) is not int or n < 0:
            raise ValueError("Atomic amounts must be nonnegative integers")
        leaves.add((kind, n))
    return leaves


def analyze(target: State, weights: Mapping[State, int | float],
            productions: Mapping[State, list[Pair]], leaf_at: LeafAt) -> Classification:
    """Every positive leaf weight counts distinct labels. Productions are disjoint."""
    # Record one terminating production per productive state in construction order.
    proof: dict[State, Pair | None] = {s: None for s, n in weights.items() if n}
    while True:
        previous = len(proof)
        for parent, options in productions.items():
            if parent in proof:
                continue
            for left, right in options:
                if left in proof and right in proof:
                    proof[parent] = left, right
                    break
        if len(proof) == previous:
            break
    if target not in proof:
        return Classification(0, None)

    # Keep every usable ordered production, but only one edge per child for paths.
    available: dict[State, list[Pair]] = {}
    edges: dict[State, dict[State, tuple[Pair, int]]] = {}
    parent_of: dict[State, State | None] = {target: None}
    queue = deque([target])
    while queue:
        state = queue.popleft()
        available[state] = [
            (a, b) for a, b in productions.get(state, ()) if a in proof and b in proof
        ]
        edges[state] = {}
        for pair in available[state]:
            for slot, child in enumerate(pair):
                edges[state].setdefault(child, (pair, slot))
                if child not in parent_of:
                    parent_of[child] = state
                    queue.append(child)

    # Subtrees are immutable and shared; a sample does not enumerate all histories.
    bases: dict[State, History] = {}
    for state, pair in proof.items():
        if state in available:
            bases[state] = (leaf_at(state, 0) if pair is None
                            else ProductTree(bases[pair[0]], bases[pair[1]]))

    def frame(parent: State, child: State) -> Frame:
        pair, slot = edges[parent][child]
        return Frame(parent, child, slot, bases[pair[1 - slot]])

    def family(anchor: State, loop: tuple[Frame, ...] = ()) -> InfiniteFamily:
        path = []
        child = anchor
        while (parent := parent_of[child]) is not None:
            path.append(frame(parent, child))
            child = parent
        return InfiniteFamily(anchor, tuple(reversed(path)), loop, bases[anchor], leaf_at)

    families = []
    infinite_leaf = next((s for s in available if weights.get(s) == inf), None)
    if infinite_leaf is not None:
        families.append(family(infinite_leaf))
    try:
        order = tuple(TopologicalSorter(edges).static_order())
    except CycleError as error:
        # graphlib lists predecessors first; our witness follows parent to child.
        cycle = list(reversed(error.args[1]))
        loop = tuple(frame(parent, child) for parent, child in pairwise(cycle))
        families.append(family(cycle[0], loop))
    if families:
        return Classification(inf, bases[target], tuple(families))

    counts = {}
    for state in order:
        counts[state] = weights.get(state, 0) + sum(counts[a] * counts[b]
                                                   for a, b in available[state])
    return Classification(counts[target], bases[target])
