"""Contextual provenance: additive weights plus an irreversible negative-event flag.

An event is (left-label a, nonzero signed right-factor n). Histories are
commutative multisets of events. No claim that these guards follow from the
project's four founding axioms: the negative-event query is an extra test.
"""
from dataclasses import dataclass
from typing import Iterable


Event = tuple[int, int]
History = tuple[Event, ...]


def checked_history(events: Iterable[Event]) -> History:
    result = tuple(events)
    for a, n in result:
        if type(a) is not int or type(n) is not int or n == 0:
            raise ValueError('Event requires integer A label and nonzero integer B weight')
    return result


def weights(history: History) -> tuple[tuple[int, int], ...]:
    w: dict[int, int] = {}
    for a, n in checked_history(history):
        w[a] = w.get(a, 0) + n
        if not w[a]:
            del w[a]
    return tuple(sorted(w.items()))


def has_negative(history: History) -> bool:
    return any(n < 0 for _, n in checked_history(history))


@dataclass(frozen=True)
class State:
    weight: tuple[tuple[int, int], ...]
    negative_seen: bool


def summarize(history: History) -> State:
    return State(weights(history), has_negative(history))


def add_states(x: State, y: State) -> State:
    w = dict(x.weight)
    for a, n in y.weight:
        w[a] = w.get(a, 0) + n
        if not w[a]:
            del w[a]
    return State(tuple(sorted(w.items())), x.negative_seen or y.negative_seen)


def append_event(state: State, a: int, n: int) -> State:
    return add_states(state, summarize(((a, n),)))


def observation(history: History) -> State:
    """Observable group-weight and legality flag: enabled iff no negative event."""
    return summarize(history)


def contextual_equivalent(left: History, right: History) -> bool:
    """Exact iff criterion for all append contexts, including the empty one."""
    return observation(left) == observation(right)


def right_distributivity_on_state(a: int, m: int, n: int) -> bool:
    """Compare elementary event (a,m+n) with adding two event receipts.

    Defined only for m,n,m+n != 0. The guard fails precisely when
    some signed input is negative but m+n is positive.
    """
    if not m or not n or not (m+n):
        raise ValueError('Right-distribution test requires nonzero factors')
    return summarize(((a,m+n),)) == summarize(((a,m),(a,n)))


def fiber_state_count(w: tuple[tuple[int,int], ...]) -> int:
    """Possible q values for an arbitrary integer-weight fiber of W.

    Needs a nonempty set of available labels and both signs as events.
    """
    return 1 if any(n < 0 for _, n in w) else 2


def sparse_negative_decision(sparse_history: History, h: int) -> bool:
    """Guard is recoverable from weights in the distinct-label restricted domain."""
    hist = checked_history(sparse_history)
    if len(hist) > h or len({a for a, _ in hist}) != len(hist):
        raise ValueError('At most h distinct labels required')
    return any(n < 0 for _, n in weights(hist))


if __name__ == '__main__':
    first = ((3,1),)
    second = ((3,2),(3,-1))
    print('Equal group weight:', weights(first) == weights(second))
    print('Different contextual guard:', has_negative(first), has_negative(second))
    print('Summaries:', summarize(first), summarize(second))
    print('Mixed signs contradict full right distribution:',
          right_distributivity_on_state(3, 2, -1))
