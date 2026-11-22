"""Reopenable contextual guards with a partial repair operation.

Elementary products have ordered A_a x B_(+/-1) input receipts, external to
this automaton. Chronological append/repair and the guard are EXTRA structure;
they are not a replacement for the project's injective elementary product.
"""
from collections import deque
from dataclasses import dataclass
from math import perm


@dataclass(frozen=True)
class State:
    window: tuple
    residue: int
    negative_since_repair: bool


def empty() -> State:
    return State((), 0, False)


def validate(N, h, m, rho):
    if (any(type(z) is not int for z in (N, h, m))
            or not (1 <= h < N) or m < 1):
        raise ValueError('N >= h+1, h >= 1, m >= 1 required')
    if (not isinstance(rho, tuple) or len(rho) != m
            or any(type(z) is not int or not 0 <= z < m for z in rho)):
        raise ValueError('rho must be a function Z_m -> Z_m given as a tuple')


def alphabet(N):
    return tuple((a, n) for a in range(N) for n in (1, -1)) + ('repair',)


def transition(state, event, N, h, m, rho):
    """None means the typed instruction is not admissible."""
    if event == 'repair':
        # Repair is available ONLY when the window is full and wholly positive.
        # This keeps the reachable-state shape of the preceding round.
        if len(state.window) != h or any(n < 0 for a, n in state.window):
            return None
        return State(state.window, rho[state.residue], False)
    if not isinstance(event, tuple) or len(event) != 2:
        raise ValueError('Expected typed event (label, +/-1) or repair')
    a, n = event
    if (type(a) is not int or type(n) is not int
            or a not in range(N) or n not in (-1, 1)):
        raise ValueError('Expected A_a x B_(+/-1)')
    nxt = (state.window + ((a, n),))[-h:]
    if len({a for a, n in nxt}) != len(nxt):
        return None
    return State(nxt, (state.residue + n) % m,
                 state.negative_since_repair or n < 0)


def reachable(N, h, m, rho):
    validate(N, h, m, rho)
    start = empty()
    seen, result, queue = {start}, [start], deque([start])
    while queue:
        state = queue.popleft()
        for event in alphabet(N):
            nxt = transition(state, event, N, h, m, rho)
            if nxt is not None and nxt not in seen:
                seen.add(nxt)
                result.append(nxt)
                queue.append(nxt)
    return tuple(result)


def observable(state):
    """Read ordered last-h receipts and guard success only."""
    return (state.window,
            not state.negative_since_repair and state.residue == 0)


def minimization(N, h, m, rho):
    """Exact partition refinement, distinguishing forbidden transitions."""
    states = reachable(N, h, m, rho)
    events = alphabet(N)

    def classify(keys):
        lookup, result = {}, {}
        for state, key in zip(states, keys):
            if key not in lookup:
                lookup[key] = len(lookup)
            result[state] = lookup[key]
        return result

    classes = classify(observable(s) for s in states)
    while True:
        nxt = classify(
            (observable(s),
             tuple(None if (target := transition(s, e, N, h, m, rho)) is None
                   else classes[target] for e in events))
            for s in states)
        if nxt == classes:
            return states, classes
        classes = nxt


def periods(rho):
    """Translation stabilizer H_rho in the additive group Z_m."""
    m = len(rho)
    if m < 1:
        raise ValueError('Nonempty rho required')
    return tuple(d for d in range(m)
                 if all(rho[(x + d) % m] == rho[x] for x in range(m)))


def predicted(N, h, m, rho):
    """Return exact counts (reachable full states, minimal observable states)."""
    validate(N, h, m, rho)
    short = sum(perm(N, j) * 2**j for j in range(h))
    p = perm(N, h)
    full = short + m*p*(2**h + 1)
    k = m//len(periods(rho))
    minimum = short + p*(2**h*k + m)
    return full, minimum


def contextual_key(state, h, rho):
    """Closed residues are remembered only modulo period subgroup H_rho."""
    if len(state.window) < h:
        return (state.window, 'warming')
    if state.negative_since_repair:
        sub = periods(rho)
        coset = min((state.residue + d) % len(rho) for d in sub)
        return (state.window, 'closed', coset)
    return (state.window, 'open', state.residue)


def standard_repairs(m):
    return {
        'preserve': tuple(range(m)),
        'erase': (0,)*m,
        **{f'mod_{d}': tuple(x % d for x in range(m))
           for d in range(1, m+1) if m % d == 0},
    }


if __name__ == '__main__':
    for N, h, m in ((2,1,3), (3,2,3), (3,2,6), (4,3,2)):
        for name, rho in standard_repairs(m).items():
            states, quotient = minimization(N, h, m, rho)
            f, g = predicted(N, h, m, rho)
            assert (len(states), len(set(quotient.values()))) == (f, g)
            print(N, h, m, name, (f, g), 'H=', periods(rho))
