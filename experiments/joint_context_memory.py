"""Joint contextual memory for typed signed products and distinct-label windows.

Input sorts A and B are distinct. Each elementary product A_a * B_n (n=+-1)
retains its ordered input pair in a separate receipt. The chronological log
and extra guard operation are ADDITIONAL assumptions, not founding axioms.
"""
from collections import deque
from dataclasses import dataclass
from itertools import product
from math import factorial, perm

from typed_suffix_automaton import refine_partial


Event = tuple[int, int]


@dataclass(frozen=True)
class State:
    window: tuple[Event, ...]
    residue: int
    ever_negative: bool


def parameters(N: int, h: int, m: int) -> None:
    if any(type(x) is not int for x in (N, h, m)) or not (1 <= h < N) or m < 1:
        raise ValueError('Require integer N >= h+1 >= 2 and m >= 1')


def empty() -> State:
    return State((), 0, False)


def alphabet(N: int) -> tuple[Event, ...]:
    if type(N) is not int or N < 2:
        raise ValueError('At least two labels required')
    return tuple(product(range(N), (1, -1)))


def advance(state: State, event: Event, N: int, h: int, m: int) -> State | None:
    """Return None for an inadmissible repeated label in the resulting window."""
    parameters(N, h, m)
    a, n = event
    if type(a) is not int or type(n) is not int or not 0 <= a < N or n not in (-1, 1):
        raise ValueError('Event must encode A_a * B_+/-1')
    window = (state.window + (event,))[-h:]
    if len({a for a, _ in window}) != len(window):
        return None
    return State(window, (state.residue + n) % m,
                 state.ever_negative or n < 0)


def run(events: tuple[Event, ...], N: int, h: int, m: int) -> State:
    state = empty()
    for event in events:
        result = advance(state, event, N, h, m)
        if result is None:
            raise ValueError('History has duplicate A labels inside its live window')
        state = result
    return state


def guard(state: State) -> bool:
    """Extra typed S x T inspection is admissible iff this returns True."""
    return not state.ever_negative and state.residue == 0


def observed(state: State, full: bool = False) -> tuple:
    return (state.window, state.residue, state.ever_negative) if full else (state.window, guard(state))


def reachable(N: int, h: int, m: int) -> tuple[State, ...]:
    parameters(N, h, m)
    events = alphabet(N)
    q = deque([empty()]); seen = {empty()}; result = [empty()]
    while q:
        state = q.popleft()
        for event in events:
            next_state = advance(state, event, N, h, m)
            if next_state is not None and next_state not in seen:
                seen.add(next_state)
                result.append(next_state)
                q.append(next_state)
    return tuple(result)


def partition(N: int, h: int, m: int, full: bool = False) -> dict[State, int]:
    states = reachable(N, h, m)
    return refine_partial(states, alphabet(N),
                          lambda s, event: advance(s, event, N, h, m),
                          lambda s: observed(s, full))


def predicted_counts(N: int, h: int, m: int) -> tuple[int, int]:
    """(All-state count, contextual-minimal count), including short histories."""
    parameters(N, h, m)
    short = sum(perm(N, j) * 2**j for j in range(h))
    full = short + m * perm(N, h) * (2**h + 1)
    contextual = short + perm(N, h) * (2**h + m)
    return full, contextual


def balanced_code(window: tuple[Event, ...]) -> int:
    """The unordered distinct-label signed window encoded in ONE large integer."""
    if len({a for a, _ in window}) != len(window):
        raise ValueError('Requires distinct A labels in window')
    if any(type(a) is not int or a < 0 or type(n) is not int or n not in (-1, 1)
           for a, n in window):
        raise ValueError('A labels nonnegative, right factors unit signed')
    return sum(n * 3**a for a, n in window)


def decode_balanced(number: int, N: int) -> tuple[Event, ...]:
    """The inverse, sorted by A label, for balanced ternary digits -1,0,+1."""
    if type(number) is not int or type(N) is not int or N < 0:
        raise ValueError('Invalid code or alphabet size')
    result = []
    for a in range(N):
        digit = number % 3
        n = -1 if digit == 2 else digit
        if n:
            result.append((a, n))
        number = (number - n) // 3
    if number:
        raise ValueError('Code needs labels outside selected universe')
    return tuple(result)


def order_rank(window: tuple[Event, ...]) -> int:
    """Chronological permutation index relative to label-sorted events."""
    remaining = list(sorted(window))
    rank = 0
    for j, event in enumerate(window):
        index = remaining.index(event)
        rank += index * factorial(len(window) - 1 - j)
        del remaining[index]
    return rank


def order_unrank(sorted_events: tuple[Event, ...], rank: int) -> tuple[Event, ...]:
    if tuple(sorted_events) != tuple(sorted(sorted_events)):
        raise ValueError('Signed events must be sorted')
    if type(rank) is not int or not 0 <= rank < factorial(len(sorted_events)):
        raise ValueError('Permutation index out of range')
    remaining = list(sorted_events); result = []
    for length in range(len(remaining), 0, -1):
        index, rank = divmod(rank, factorial(length-1))
        result.append(remaining.pop(index))
    return tuple(result)


def window_from_code(code: int, rank: int, N: int) -> tuple[Event, ...]:
    return order_unrank(decode_balanced(code, N), rank)


def minimal_key(state: State, h: int) -> tuple:
    """Exact contextual equivalence class by window and observably useful memory."""
    code = balanced_code(state.window)
    order = order_rank(state.window)
    if len(state.window) < h:
        return len(state.window), code, order, 'warming'
    if state.ever_negative:
        return h, code, order, 'closed'
    return h, code, order, 'open', state.residue


if __name__ == '__main__':
    for N, h, m in ((2,1,3), (3,2,3), (4,3,2)):
        states = reachable(N,h,m)
        full, contextual = predicted_counts(N,h,m)
        classes = partition(N,h,m)
        print(f'N={N} h={h} m={m}: full {len(states)}/{full}, '
              f'contextual {len(set(classes.values()))}/{contextual}')
