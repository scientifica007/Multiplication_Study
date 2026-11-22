"""A finite many-sorted partial-operation countermodel to coset-only equivalence.

This is a CONTROL projection of a typed provenance-preserving model. Complete
records retain ordered inputs; the control quotient need not retain them.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass

OPERATIONS = ('tick', 'freeze', 'release', 'check')
STAGES = ('Active', 'Held', 'Released')

@dataclass(frozen=True, order=True)
class Control:
    stage: str
    residue: int

@dataclass(frozen=True)
class Command:
    name: str
    sort: str = 'Instruction'

@dataclass(frozen=True)
class ProvenanceState:
    control: Control
    parent: ProvenanceState | None = None
    right: Command | None = None


def validate(modulus: int, allowed: frozenset[int]):
    if type(modulus) is not int or modulus < 1:
        raise ValueError('Positive integer modulus required')
    if not isinstance(allowed, frozenset) or any(type(r) is not int or r < 0 or r >= modulus for r in allowed):
        raise ValueError('Release domain must be a frozenset of residues')


def transition(state: Control, action: str, modulus: int,
               release_domain: frozenset[int], allow_held_tick: bool = False) -> Control | None:
    """A forbidden typed instruction has *no* result (None), not zero."""
    if state.stage not in STAGES or not 0 <= state.residue < modulus or action not in OPERATIONS:
        raise ValueError('Invalid typed control state or instruction')
    if action == 'tick':
        if state.stage in ('Active', 'Released') or (allow_held_tick and state.stage == 'Held'):
            return Control(state.stage, (state.residue + 1) % modulus)
    elif action == 'freeze' and state.stage == 'Active':
        return Control('Held', state.residue)
    elif action == 'release' and state.stage == 'Held' and state.residue in release_domain:
        return Control('Released', 0)
    elif action == 'check' and state.stage == 'Released' and state.residue == 0:
        return state
    return None


def initial() -> ProvenanceState:
    return ProvenanceState(Control('Active', 0))


def typed_step(current: ProvenanceState, command: Command,
               modulus: int, release_domain: frozenset[int],
               allow_held_tick: bool = False) -> ProvenanceState | None:
    if not isinstance(current, ProvenanceState) or not isinstance(command, Command) or command.sort != 'Instruction':
        raise TypeError('A typed control value and an instruction of a different sort are required')
    result = transition(current.control, command.name, modulus, release_domain, allow_held_tick)
    if result is None:
        return None
    return ProvenanceState(result, current, command)


def unpack(record: ProvenanceState) -> tuple[ProvenanceState, Command]:
    if record.parent is None or record.right is None:
        raise ValueError('Only the result of a typed instruction has a recorded input pair')
    return record.parent, record.right


def reachable(modulus: int, release_domain: frozenset[int],
              allow_held_tick: bool = False) -> tuple[Control, ...]:
    validate(modulus, release_domain)
    start = Control('Active', 0)
    queue = deque((start,))
    seen, records = {start}, [start]
    while queue:
        s = queue.popleft()
        for a in OPERATIONS:
            t = transition(s, a, modulus, release_domain, allow_held_tick)
            if t is not None and t not in seen:
                seen.add(t)
                records.append(t)
                queue.append(t)
    return tuple(records)


def period_subgroup(modulus: int, release_domain: frozenset[int]) -> tuple[int, ...]:
    validate(modulus, release_domain)
    return tuple(d for d in range(modulus) if all(
        ((x+d) % modulus in release_domain) == (x in release_domain)
        for x in range(modulus)))


def predicted_class_count(modulus: int, release_domain: frozenset[int],
                          allow_held_tick: bool = False) -> int:
    """Exact number of observable contextual-equivalence classes (all reachable)."""
    validate(modulus, release_domain)
    active = modulus // len(period_subgroup(modulus, release_domain))
    held = active if allow_held_tick else (1 if len(release_domain) in (0, modulus) else 2)
    released = modulus if release_domain else 0
    return active + held + released


def minimization(modulus: int, release_domain: frozenset[int],
                 allow_held_tick: bool = False) -> dict[Control, int]:
    states = reachable(modulus, release_domain, allow_held_tick)
    def classify(keys):
        identifiers, assignment = {}, {}
        for s, k in zip(states, keys):
            if k not in identifiers:
                identifiers[k] = len(identifiers)
            assignment[s] = identifiers[k]
        return assignment
    classes = classify(s.stage for s in states)
    for _ in range(len(states) + 1):
        refined = classify((s.stage, tuple(
            None if (t := transition(s, a, modulus, release_domain, allow_held_tick)) is None else classes[t]
            for a in OPERATIONS)) for s in states)
        if refined == classes:
            return classes
        classes = refined
    raise AssertionError('Finite partition refinement failed to terminate')


def shortest_witness(a: Control, b: Control, modulus: int,
                     release_domain: frozenset[int], allow_held_tick: bool = False) -> tuple[str, ...] | None:
    """Shortest separating action sequence; None for contextual equivalence."""
    queue = deque([(a, b, ())])
    seen = {(a, b)}
    while queue:
        x, y, prefix = queue.popleft()
        if x.stage != y.stage:
            return prefix
        for act in OPERATIONS:
            nx = transition(x, act, modulus, release_domain, allow_held_tick)
            ny = transition(y, act, modulus, release_domain, allow_held_tick)
            if (nx is None) != (ny is None):
                return prefix + (act,)
            if nx is not None and (nx, ny) not in seen:
                seen.add((nx, ny))
                queue.append((nx, ny, prefix + (act,)))
    return None


def stage_partition(modulus: int, release_domain: frozenset[int], stage: str,
                    allow_held_tick: bool = False) -> tuple[tuple[int, ...], ...]:
    blocks = minimization(modulus, release_domain, allow_held_tick)
    byclass = {}
    for s, cls in blocks.items():
        if s.stage == stage:
            byclass.setdefault(cls, []).append(s.residue)
    return tuple(sorted((tuple(sorted(v)) for v in byclass.values())))


if __name__ == '__main__':
    m=4; D=frozenset((0,1))
    print('reachable control states:', len(reachable(m,D)))
    print('minimal contextual classes:', len(set(minimization(m,D).values())))
    for sort in STAGES:
        print(sort, stage_partition(m,D,sort))
    print('period subgroup of the predicate:', period_subgroup(m,D))
    print('after allowing Held tick:', stage_partition(m,D,'Held',True))
