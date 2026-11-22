"""Independent model for multiple partial repair operations on typed histories.

Extra structure: external chronological log, finite residue, and typed repair
instructions. Elementary products remain separately typed and fully unpackable.
"""
from collections import deque
from dataclasses import dataclass
from math import perm


@dataclass(frozen=True)
class Repair:
    name: str
    values: tuple[int, ...]
    domain: tuple[bool, ...]


@dataclass(frozen=True)
class State:
    window: tuple[tuple[int, int], ...]
    residue: int
    closed: bool


def validate(N: int, h: int, m: int, repairs: tuple[Repair, ...]):
    if any(type(x) is not int for x in (N, h, m)) or not (1 <= h < N) or m < 1:
        raise ValueError('Require N >= h+1, h >= 1, m >= 1')
    if not isinstance(repairs, tuple) or not repairs:
        raise ValueError('At least one repair is required')
    names = set()
    for repair in repairs:
        if (not isinstance(repair, Repair) or not repair.name or
                repair.name in names or len(repair.values) != m or
                len(repair.domain) != m or
                any(type(x) is not int or not 0 <= x < m for x in repair.values) or
                any(type(x) is not bool for x in repair.domain)):
            raise ValueError('Invalid named repair, range or domain')
        names.add(repair.name)


def total_repair(name: str, values: tuple[int, ...]) -> Repair:
    return Repair(name, tuple(values), (True,)*len(values))


def alphabet(N: int, repairs: tuple[Repair, ...]):
    return tuple((a, n) for a in range(N) for n in (1, -1)) + tuple(
        f'repair:{repair.name}' for repair in repairs)


def transition(s: State, event, N: int, h: int, m: int, repairs: tuple[Repair, ...]):
    if isinstance(event, str) and event.startswith('repair:'):
        name = event.removeprefix('repair:')
        found = next((r for r in repairs if r.name == name), None)
        if found is None:
            raise ValueError('Unknown repair name')
        if len(s.window) != h or any(n < 0 for _, n in s.window) or not found.domain[s.residue]:
            return None
        return State(s.window, found.values[s.residue], False)
    if not (isinstance(event, tuple) and len(event) == 2):
        raise ValueError('Expected signed typed product event or repair')
    a, n = event
    if type(a) is not int or not 0 <= a < N or type(n) is not int or n not in (-1,1):
        raise ValueError('Expected A_a * B_(+/-1)')
    nxt = (s.window + ((a, n),))[-h:]
    if len({a for a, _ in nxt}) != len(nxt):
        return None
    return State(nxt, (s.residue + n) % m, s.closed or n < 0)


def observable(s: State):
    return s.window, (not s.closed and s.residue == 0)


def reachable(N: int, h: int, m: int, repairs: tuple[Repair, ...]):
    validate(N, h, m, repairs)
    start = State((),0,False)
    q=deque([start]); seen={start}; result=[start]
    while q:
        s=q.popleft()
        for e in alphabet(N, repairs):
            t=transition(s,e,N,h,m,repairs)
            if t is not None and t not in seen:
                seen.add(t);result.append(t);q.append(t)
    return tuple(result)


def signatures(repairs: tuple[Repair, ...], residue: int):
    return tuple(repair.values[residue] if repair.domain[residue] else None
                 for repair in repairs)


def common_periods(m: int, repairs: tuple[Repair, ...]):
    return tuple(d for d in range(m) if all(
        signatures(repairs, x) == signatures(repairs, (x+d)%m)
        for x in range(m)))


def predicted(N: int, h: int, m: int, repairs: tuple[Repair, ...]):
    validate(N,h,m,repairs)
    short=sum(perm(N,j)*2**j for j in range(h))
    p=perm(N,h)
    full=short + m*p*(2**h+1)
    k=m//len(common_periods(m,repairs))
    minimum=short + p*(2**h*k+m)
    return full, minimum


def contextual_key(s: State, h: int, m: int, repairs: tuple[Repair, ...]):
    if len(s.window)<h:
        return s.window, 'warm'
    if s.closed:
        coset=min((s.residue+d)%m for d in common_periods(m,repairs))
        return s.window,'closed',coset
    return s.window,'open',s.residue


def minimization(N: int, h: int, m: int, repairs: tuple[Repair, ...]):
    states=reachable(N,h,m,repairs)
    events=alphabet(N,repairs)
    def classify(keys):
        seen={}; assignments={}
        for s,key in zip(states,keys):
            if key not in seen:
                seen[key]=len(seen)
            assignments[s]=seen[key]
        return assignments
    classes=classify(observable(s) for s in states)
    for _ in range(len(states)+1):
        next_classes=classify((observable(s),tuple(
            None if (nxt:=transition(s,e,N,h,m,repairs)) is None else classes[nxt]
            for e in events)) for s in states)
        if next_classes==classes:
            return states,classes
        classes=next_classes
    raise AssertionError('Refinement did not converge')


def repair_signature_periods(m: int, repairs: tuple[Repair, ...]):
    """Same as common_periods, written as intersection of separate stabilizers."""
    groups=[]
    for repair in repairs:
        image=lambda x: repair.values[x] if repair.domain[x] else None
        groups.append(set(d for d in range(m) if all(
            image((x+d)%m)==image(x) for x in range(m))))
    return tuple(sorted(set.intersection(*groups)))


def distinguishing_word(left: State, right: State, N: int, h: int, m: int,
                        repairs: tuple[Repair, ...]):
    """Shortest separating *partial* action word, or None if equivalent.

    Returns a tuple of typed actions. An action is a witness when precisely
    one state admits it; otherwise we compare the subsequent guard readings.
    """
    q=deque([(left,right,())]);seen={(left,right)}
    while q:
        s,t,word=q.popleft()
        if observable(s)!=observable(t):
            return word
        for event in alphabet(N,repairs):
            ns=transition(s,event,N,h,m,repairs)
            nt=transition(t,event,N,h,m,repairs)
            if (ns is None)!=(nt is None):
                return word+(event,)
            if ns is not None and (ns,nt) not in seen:
                seen.add((ns,nt)); q.append((ns,nt,word+(event,)))
    return None


if __name__=='__main__':
    cases=((3,2,6,(total_repair('two',tuple(r%2 for r in range(6))),
                    total_repair('three',tuple(r%3 for r in range(6))))),
           (3,2,6,(Repair('even_reset',(0,)*6,tuple(x%2==0 for x in range(6))),)))
    for N,h,m,repairs in cases:
        states,blocks=minimization(N,h,m,repairs)
        print('repairs',tuple(x.name for x in repairs),'H',common_periods(m,repairs),
              'full',len(states),'minimal',len(set(blocks.values())),
              'theory',predicted(N,h,m,repairs))
