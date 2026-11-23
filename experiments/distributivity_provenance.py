"""Distributivity, unique product unpacking, and provenance-tagged zeros.

Extra hypotheses: left inputs are integers, each right input is a distinct
named typed factor with a numerical reading, and output is a commutative
monoid built from integer coordinate vectors plus persistent provenance tags.
This is not a general definition of the founding multiplication axioms.
"""
from __future__ import annotations
from dataclasses import dataclass

LABELS = ('positive', 'negative', 'double')
RIGHT_READING = {'positive': 1, 'negative': -1, 'double': 2}

@dataclass(frozen=True)
class Left:
    value: int
    sort: str = 'C'

@dataclass(frozen=True)
class Right:
    label: str
    sort: str = 'D'
    def __post_init__(self):
        if self.label not in LABELS:
            raise ValueError('Unrecognised D input')

@dataclass(frozen=True)
class Output:
    """An element (v,S) with finite-support v and supp(v) subset S."""
    vector: tuple[int, ...]
    tags: frozenset[str]
    sort: str = 'E'
    def __post_init__(self):
        if len(self.vector) != len(LABELS) or any(type(v) is not int for v in self.vector):
            raise ValueError('Wrong coordinate vector')
        if not self.tags <= frozenset(LABELS):
            raise ValueError('Unrecognised support tag')
        if any(v and label not in self.tags for v,label in zip(self.vector,LABELS)):
            raise ValueError('A nonzero coordinate requires its source tag')


def zero() -> Output:
    return Output((0,)*len(LABELS), frozenset())


def plus(u: Output, v: Output) -> Output:
    if not isinstance(u,Output) or not isinstance(v,Output):
        raise TypeError('Addition only on the E sort')
    return Output(tuple(a+b for a,b in zip(u.vector,v.vector)),u.tags | v.tags)


def multiply(c: Left, d: Right) -> Output:
    """Fully typed C x D -> E; no operation on same-sort pairs."""
    if not isinstance(c,Left) or not isinstance(d,Right) or type(c.value) is not int:
        raise TypeError('Typed inputs C integer and D named factor are required')
    return Output(tuple(c.value if label == d.label else 0 for label in LABELS),frozenset((d.label,)))


def unpack_product(e: Output) -> tuple[Left,Right]:
    """Partial U, defined on *the image of multiplication* only."""
    if not isinstance(e,Output) or len(e.tags) != 1:
        raise ValueError('The sum is not the image of a single typed product')
    label = next(iter(e.tags))
    index = LABELS.index(label)
    if any(v != 0 for j,v in enumerate(e.vector) if j != index):
        raise ValueError('Inconsistent product image')
    return Left(e.vector[index]),Right(label)


def reading(e: Output) -> int:
    return sum(n*RIGHT_READING[label] for n,label in zip(e.vector,LABELS))


def erase_provenance(e: Output) -> tuple[int,...]:
    """Forget semilattice tags; maps onto an abelian group of vectors."""
    return e.vector


def local_inverse(e: Output) -> Output:
    return Output(tuple(-a for a in e.vector),e.tags)


def raw_decomposition_left(a: int,b: int,d: Right):
    """Two different sum histories, one common algebraic result."""
    return plus(multiply(Left(a),d),multiply(Left(b),d))


if __name__ == '__main__':
    for d in LABELS:
        r=Right(d)
        for a,b in ((1,3),(-3,3),(0,1)):
            assert multiply(Left(a+b),r) == raw_decomposition_left(a,b,r)
    for label in LABELS:
        e=multiply(Left(0),Right(label))
        print(label, e, 'full unpack',unpack_product(e),'reading',reading(e))
