"""Finite contextual-equivalence laboratory for typed sign-event receipts.

A '+' event denotes one admissible typed product A_1 * B_+1,
'-' denotes A_1 * B_-1. Events are appended chronologically to an
EXTERNAL log; this append is not asserted to be addition in the result sort.
The guard represents availability of a distinct typed C x T operation.
"""
from collections import deque
from dataclasses import dataclass
from itertools import product

ALPHABET = ('+', '-')


@dataclass(frozen=True)
class State:
    residue: int
    negative_ever: bool
    suffix: str


def validate(m: int, h: int) -> None:
    if type(m) is not int or type(h) is not int or m < 1 or h < 1:
        raise ValueError('m and h must be positive integers')


def initial() -> State:
    return State(0, False, '')


def step(state: State, event: str, m: int, h: int) -> State:
    validate(m, h)
    if event not in ALPHABET or len(event) != 1:
        raise ValueError('Only signed unit events + and - are supported')
    return State((state.residue + (1 if event == '+' else -1)) % m,
                 state.negative_ever or event == '-',
                 (state.suffix + event)[-h:])


def observe_word(word: str, m: int, h: int) -> State:
    state = initial()
    for sign in word:
        state = step(state, sign, m, h)
    return state


def can_test(state: State) -> bool:
    """Availability of a separate C x T probe; the probe leaves state intact."""
    return not state.negative_ever and state.residue == 0


def output(state: State, expose_residue: bool = False) -> tuple:
    if expose_residue:
        return (state.suffix, state.residue, state.negative_ever)
    return (state.suffix, can_test(state))


def reachable(m: int, h: int) -> tuple[State, ...]:
    validate(m, h)
    start = initial()
    queue = deque([start]); seen = {start}; result = [start]
    while queue:
        state = queue.popleft()
        for event in ALPHABET:
            next_state = step(state, event, m, h)
            if next_state not in seen:
                seen.add(next_state); result.append(next_state); queue.append(next_state)
    return tuple(result)


def minimal_partition(m: int, h: int, expose_residue: bool = False) -> dict[State, int]:
    """Compute exact Moore-equivalence via partition refinement; all states reachable."""
    states = reachable(m, h)

    def classify(keys) -> dict[State, int]:
        labels = {}
        result = {}
        for state, key in zip(states, keys):
            if key not in labels:
                labels[key] = len(labels)
            result[state] = labels[key]
        return result

    classes = classify(output(st, expose_residue) for st in states)
    for _ in range(len(states) + 1):
        next_classes = classify(
            (output(st, expose_residue),
             tuple(classes[step(st, event, m, h)] for event in ALPHABET))
            for st in states
        )
        if next_classes == classes:
            return classes
        classes = next_classes
    raise AssertionError('Partition refinement did not converge')


def refine_partial(states, alphabet, transition, observation):
    """Minimize a finite deterministic *partial* Moore transition system.

    A failed transition returns None, distinguishable from an ordinary state.
    Assumes hashable distinct states, finite alphabet and transition-closure.
    """
    states = tuple(states)
    alphabet = tuple(alphabet)
    if len(set(states)) != len(states):
        raise ValueError('States must be distinct and hashable')
    seen = set(states)
    for st in states:
        for event in alphabet:
            nxt = transition(st, event)
            if nxt is not None and nxt not in seen:
                raise ValueError('The supplied state set must be transition-closed')

    def classify(keys):
        ids, result = {}, {}
        for st, key in zip(states, keys):
            if key not in ids:
                ids[key] = len(ids)
            result[st] = ids[key]
        return result

    blocks = classify(observation(st) for st in states)
    for _ in range(len(states)+1):
        updated = classify((observation(st), tuple(
            None if transition(st, event) is None else blocks[transition(st, event)]
            for event in alphabet)) for st in states)
        if updated == blocks:
            return blocks
        blocks = updated
    raise AssertionError('Expected finite partition refinement to terminate')


def predicted_full(m: int, h: int) -> int:
    validate(m, h)
    return (2**h - 1) + m*(2**h + 1)


def predicted_guard_only(m: int, h: int) -> int:
    validate(m, h)
    return (2**(h+1)) + m - 1


def shortest_distinguishing_continuation(
    left: State, right: State, m: int, h: int, expose_residue: bool = False
) -> str | None:
    """Find shortest witness suffix, or None if states are contextually equivalent."""
    validate(m, h)
    queue = deque([(left, right, '')])
    seen = {(left, right)}
    while queue:
        x, y, word = queue.popleft()
        if output(x, expose_residue) != output(y, expose_residue):
            return word
        for event in ALPHABET:
            nx, ny = step(x, event, m, h), step(y, event, m, h)
            if (nx, ny) not in seen:
                seen.add((nx, ny)); queue.append((nx, ny, word+event))
    return None


if __name__ == '__main__':
    for h in (1, 2, 3):
        m = 3
        states = reachable(m, h)
        guarded = minimal_partition(m, h)
        print(f'm={m}, h={h}: reachable={len(states)}, '
              f'full={predicted_full(m,h)}, '
              f'contextual={len(set(guarded.values()))}, '
              f'formula={predicted_guard_only(m,h)}')
