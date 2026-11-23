"""Nonzero-only partial distributivity: finite certificates and countermodels.

No zero is a permitted multiplicative argument. Elementary product receipts
retain their ordered typed inputs, unless the output is explicitly a reading.
"""
from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class Atom:
    sort: str
    value: int


@dataclass(frozen=True)
class Receipt:
    left: Atom
    right: Atom
    sort: str = 'E'


def receipt(a: int, b: int) -> Receipt:
    if type(a) is not int or type(b) is not int or a == 0 or b == 0:
        raise ValueError('Both factors must be nonzero integers')
    return Receipt(Atom('A', a), Atom('B', b))


def unpack(x: Receipt):
    if not isinstance(x, Receipt):
        raise TypeError('Only complete multiplication receipts can be unpacked')
    return x.left, x.right


def reading(x: Receipt) -> int:
    return x.left.value * x.right.value


def permitted_sum(x: int, y: int) -> bool:
    return x != 0 and y != 0 and x + y != 0


def diamond_pair(a: int, b: int):
    """Both 2a,b and a,2b are nonzero, distinct input pairs."""
    if not a or not b:
        raise ValueError('Nonzero witness required')
    return receipt(2 * a, b), receipt(a, 2 * b)


@dataclass(frozen=True)
class Tagged:
    """Commutative monoid Z x {0,1} with a local group at tag=1."""
    amount: int
    tag: bool


def tagged_add(x: Tagged, y: Tagged) -> Tagged:
    return Tagged(x.amount + y.amount, x.tag or y.tag)


def tagged_product(a: int, b: int) -> Tagged:
    if not a or not b:
        raise ValueError('Products with a zero factor are not defined')
    return Tagged(a * b, True)


def one_sided_product(a: int, b: int) -> tuple[tuple[int, int], ...]:
    """Free abelian group with generator e_b. Injective for a,b != 0."""
    if not a or not b:
        raise ValueError('Nonzero factors required')
    return ((b, a),)


def group_add(x: tuple[tuple[int, int], ...], y: tuple[tuple[int, int], ...]):
    result = dict(x)
    for label, amount in y:
        result[label] = result.get(label, 0) + amount
    return tuple(sorted((label, amount) for label, amount in result.items() if amount != 0))


def unit_vector(index: int, length: int = 7, coefficient: int = 1) -> tuple[int, ...]:
    return tuple(coefficient if j == index else 0 for j in range(length))


def vec_add(x: tuple[int, ...], y: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(a + b for a, b in zip(x, y))


def restricted_partial_product(a: int, b: int) -> tuple[int, ...]:
    """Nine injective outputs on {1,2,3}², satisfying two selected laws.

    Required left distributivity: mu(2,1)=mu(1,1)+mu(1,1).
    Required right distributivity: mu(3,2)=mu(3,1)+mu(3,1).
    Other distribution instances are intentionally NOT imposed.
    """
    if a not in (1, 2, 3) or b not in (1, 2, 3):
        raise ValueError('Outside the finite partial domain')
    first = {(1,1): unit_vector(0), (2,1): unit_vector(0, coefficient=2),
             (3,1): unit_vector(1), (3,2): unit_vector(1, coefficient=2)}
    if (a,b) in first:
        return first[(a,b)]
    extras = sorted(set(product((1,2,3), repeat=2)) - set(first))
    return unit_vector(2 + extras.index((a,b)))


def full_receipt_reading_additivity(a: int, b: int, c: int, *, left: bool):
    """The *measurement* distributes even though receipt identities do not."""
    if not permitted_sum(a, b) or not c:
        raise ValueError('Only nonzero legal sums')
    if left:
        whole = receipt(a+b, c)
        pieces = (receipt(a,c), receipt(b,c))
    else:
        whole = receipt(c,a+b)
        pieces = (receipt(c,a), receipt(c,b))
    return (reading(whole) == sum(map(reading, pieces)), whole, pieces)
