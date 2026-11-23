"""Finite many-sorted partial-algebra verification with concrete witnesses.

A public quotient may forget full provenance; the original typed product
receipts remain intact.  This module is a finite-algebra checker, not a new
axiom or a universal decision procedure for infinite algebras.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import product
from typing import Callable


@dataclass(frozen=True)
class Value:
    sort: str
    name: str
    amount: int
    # Each product retains its ordered *complete* inputs, recursively.
    inputs: tuple[Value, ...] = ()


@dataclass(frozen=True)
class Operation:
    name: str
    inputs: tuple[str, ...]
    output: str
    table: dict[tuple[Value, ...], Value]


@dataclass(frozen=True)
class Hole:
    """A well-typed unary polynomial step, with all other arguments fixed."""
    operation: str
    position: int
    arguments: tuple[Value | None, ...]

    def describe(self) -> str:
        return self.operation + '(' + ', '.join(
            '□' if arg is None else arg.name for arg in self.arguments) + ')'


@dataclass(frozen=True)
class Witness:
    kind: str  # observation, definedness, or output-class
    left: Value
    right: Value
    steps: tuple[Hole, ...]
    left_end: Value | None
    right_end: Value | None


class FiniteSortedAlgebra:
    def __init__(self, sorts: dict[str, tuple[Value, ...]],
                 operations: tuple[Operation, ...],
                 observation: Callable[[Value], object]):
        self.sorts = {s: tuple(elems) for s, elems in sorts.items()}
        self.operations = tuple(operations)
        self.observation = observation
        self.elements = tuple(e for elems in self.sorts.values() for e in elems)
        self._by_name = {op.name: op for op in operations}
        self._validate()
        self.contexts = {s: self._contexts_for(s) for s in self.sorts}

    def _validate(self):
        if len(set(self.elements)) != len(self.elements):
            raise ValueError('Elements must be globally unique')
        for s, elems in self.sorts.items():
            if any(e.sort != s for e in elems):
                raise ValueError('A value has been placed in the wrong sort')
        if len(self._by_name) != len(self.operations):
            raise ValueError('Operation names must be unique')
        for op in self.operations:
            if op.output not in self.sorts or any(s not in self.sorts for s in op.inputs):
                raise ValueError('Undeclared sort in operation signature')
            for arguments, output in op.table.items():
                if len(arguments) != len(op.inputs):
                    raise ValueError('Wrong operation arity')
                if any(x not in self.sorts[s] for s, x in zip(op.inputs, arguments)):
                    raise ValueError('Operation input not in the declared sort')
                if output not in self.sorts[op.output]:
                    raise ValueError('Operation output not in the declared sort')

    def _contexts_for(self, sort: str) -> tuple[Hole, ...]:
        contexts = []
        for op in self.operations:
            for position, input_sort in enumerate(op.inputs):
                if input_sort != sort:
                    continue
                choices = [(None,) if i == position else self.sorts[other]
                           for i, other in enumerate(op.inputs)]
                for args in product(*choices):
                    contexts.append(Hole(op.name, position, args))
        return tuple(contexts)

    def apply(self, operation: str, args: tuple[Value, ...]) -> Value | None:
        op = self._by_name[operation]
        if len(args) != len(op.inputs) or any(
            x not in self.sorts[s] for s, x in zip(op.inputs, args)
        ):
            raise ValueError('Ill-typed application')
        return op.table.get(args)

    def apply_hole(self, hole: Hole, value: Value) -> Value | None:
        op = self._by_name[hole.operation]
        if value.sort != op.inputs[hole.position]:
            raise ValueError('Ill-typed context')
        args = tuple(value if i == hole.position else other
                     for i, other in enumerate(hole.arguments))
        return self.apply(hole.operation, args)


def initial_partition(algebra: FiniteSortedAlgebra) -> dict[Value, int]:
    names: dict[tuple, int] = {}
    result = {}
    for x in algebra.elements:
        key = (x.sort, algebra.observation(x))
        if key not in names:
            names[key] = len(names)
        result[x] = names[key]
    return result


def refine_partition(algebra: FiniteSortedAlgebra,
                     initial: dict[Value, int] | None = None):
    """Greatest strong congruence contained in observable equality.

    Output is (blocks, refinement_rounds).  Old partition IDs are explicitly
    retained in signatures, ensuring monotone splitting and finite termination.
    """
    blocks = initial_partition(algebra) if initial is None else dict(initial)
    if set(blocks) != set(algebra.elements):
        raise ValueError('Partition must cover every element')
    rounds = 0
    while True:
        labels = {}
        nxt = {}
        for x in algebra.elements:
            signatures = tuple(
                (hole.operation, hole.position, hole.arguments,
                 None if (y := algebra.apply_hole(hole, x)) is None else blocks[y])
                for hole in algebra.contexts[x.sort])
            key = (x.sort, blocks[x], signatures)
            if key not in labels:
                labels[key] = len(labels)
            nxt[x] = labels[key]
        if all(blocks[x] == blocks[y] for x in algebra.elements for y in algebra.elements
               if nxt[x] == nxt[y]) and all(nxt[x] == nxt[y] for x in algebra.elements
                                        for y in algebra.elements if blocks[x] == blocks[y]):
            return nxt, rounds
        blocks = nxt
        rounds += 1
        if rounds > len(algebra.elements):
            raise AssertionError('Strict finite refinement did not converge')


def quotient_counts(algebra: FiniteSortedAlgebra,
                    blocks: dict[Value, int]) -> dict[str, int]:
    return {s: len({blocks[e] for e in elems}) for s, elems in algebra.sorts.items()}


def verify_candidate(algebra: FiniteSortedAlgebra,
                     q: Callable[[Value], object]) -> Witness | None:
    """Exact one-hole criterion for a proposed quotient; returns a local fault.

    Two equal quotient inputs must have matching observation, matching
    definedness, and equivalent outputs under any basic one-hole context.
    These tests suffice for all multi-input operations by changing one input
    representative at a time.
    """
    for s, elems in algebra.sorts.items():
        for i, x in enumerate(elems):
            for y in elems[i+1:]:
                if q(x) != q(y):
                    continue
                if algebra.observation(x) != algebra.observation(y):
                    return Witness('observation', x, y, (), x, y)
                for hole in algebra.contexts[s]:
                    ux, uy = algebra.apply_hole(hole, x), algebra.apply_hole(hole, y)
                    if (ux is None) != (uy is None):
                        return Witness('definedness', x, y, (hole,), ux, uy)
                    if ux is not None and q(ux) != q(uy):
                        return Witness('output-class', x, y, (hole,), ux, uy)
    return None


def shortest_witness(algebra: FiniteSortedAlgebra,
                     x: Value, y: Value) -> Witness | None:
    """BFS for a *shortest* distinguishing well-typed one-hole term context.

    A mismatched definedness is discovered while generating the next layer;
    do not return it before checking all observations on the current layer.
    """
    if x.sort != y.sort:
        raise ValueError('Context comparisons require matching sorts')
    queue = deque([(x, y, ())])
    seen = {(x, y)}
    best_domain_witness = None
    while queue:
        a, b, path = queue.popleft()
        if algebra.observation(a) != algebra.observation(b):
            return Witness('observation', x, y, path, a, b)
        if best_domain_witness is not None and len(path) >= len(best_domain_witness.steps):
            return best_domain_witness
        for hole in algebra.contexts[a.sort]:
            ax, by = algebra.apply_hole(hole, a), algebra.apply_hole(hole, b)
            if (ax is None) != (by is None):
                if best_domain_witness is None:
                    best_domain_witness = Witness('definedness', x, y,
                                                  path + (hole,), ax, by)
            elif ax is not None and (ax, by) not in seen:
                seen.add((ax, by))
                queue.append((ax, by, path + (hole,)))
    return best_domain_witness


def build_product_model(allow_unpack: bool = False) -> FiniteSortedAlgebra:
    """A×B→C, C×D⇀E, E×F⇀G, with an optional observable unpacking API.

    This reproduces the typed example from round 10.  Full product receipts
    preserve recursive inputs even when the *public* quotient does not.
    """
    A_nums = (-3, -2, -1, 1, 2, 3)
    B_nums = (-6, -3, -2, 2, 3, 6)
    A = tuple(Value('A', f'A_{a}', a) for a in A_nums)
    B = tuple(Value('B', f'B_{b}', b) for b in B_nums)
    D = (Value('D', 'seal', 2), Value('D', 'inspect', 3))
    F = (Value('F', 'confirm', 5),)
    cs = {}
    C = tuple(Value('C', f'C_({a.amount},{b.amount})',
                    a.amount * b.amount, (a, b)) for a, b in product(A, B))
    for c in C:
        cs[c.inputs] = c
    es = {}
    E = []
    for c, d in product(C, D):
        a, b = c.inputs
        if (d.name == 'seal' and b.amount % 2 == 0) or (
            d.name == 'inspect' and a.amount % 2 == 0
        ):
            e = Value('E', f'E_({c.name},{d.name})', c.amount * d.amount, (c, d))
            es[(c, d)] = e
            E.append(e)
    gs = {}
    G = []
    for e, f in product(E, F):
        c, d = e.inputs
        if d.name == 'seal' and c.inputs[0].amount == 1:
            g = Value('G', f'G_({e.name},{f.name})', e.amount * f.amount, (e, f))
            gs[(e, f)] = g
            G.append(g)
    sorts = {'A': A, 'B': B, 'C': C, 'D': D, 'E': tuple(E),
             'F': F, 'G': tuple(G)}
    ops = [Operation('multiply_AB', ('A', 'B'), 'C', cs),
           Operation('multiply_CD', ('C', 'D'), 'E', es),
           Operation('multiply_EF', ('E', 'F'), 'G', gs)]
    if allow_unpack:
        for typ, left_sort, right_sort in (
            ('C', 'A', 'B'), ('E', 'C', 'D'), ('G', 'E', 'F')
        ):
            ops.extend((
                Operation(f'unpack_{typ}_left', (typ,), left_sort,
                          {(v,): v.inputs[0] for v in sorts[typ]}),
                Operation(f'unpack_{typ}_right', (typ,), right_sort,
                          {(v,): v.inputs[1] for v in sorts[typ]}),
            ))
    return FiniteSortedAlgebra(sorts, tuple(ops), lambda x: x.amount)


def c_receipt(model: FiniteSortedAlgebra, a: int, b: int) -> Value:
    return next(c for c in model.sorts['C'] if c.inputs[0].amount == a
                and c.inputs[1].amount == b)


if __name__ == '__main__':
    for mode in (False, True):
        m = build_product_model(mode)
        partition, rounds = refine_partition(m)
        print('unpack=', mode, 'sort_sizes=', {s: len(v) for s, v in m.sorts.items()},
              'quotient=', quotient_counts(m, partition), 'rounds=', rounds)
        c1, c2 = c_receipt(m, 1, 6), c_receipt(m, 3, 2)
        w = shortest_witness(m, c1, c2)
        print('  witness:', w.kind if w else 'equivalent',
              [h.describe() for h in w.steps] if w else ())
