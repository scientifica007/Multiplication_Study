"""Finite typed A*B -> C, C*D -> E and E*F -> G multiplication.

All product receipts retain their ordered inputs. Guard predicates and
numerical readings are additional model assumptions, not founding axioms.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product

@dataclass(frozen=True)
class Atom:
    sort: str
    label: int | str
    amount: int

@dataclass(frozen=True)
class Receipt:
    sort: str
    left: Atom | 'Receipt'
    right: Atom
    amount: int
    operation: str

A_LABELS = (-3, -2, -1, 1, 2, 3)
B_VALUES = (-6, -3, -2, 2, 3, 6)
D_FACTORS = (('seal', 2), ('inspect', 3))
F_FACTORS = (('confirm', 5),)

def operand_a(a: int) -> Atom:
    if type(a) is not int or a not in A_LABELS:
        raise ValueError('Unknown A label')
    return Atom('A', a, a)

def operand_b(b: int) -> Atom:
    if type(b) is not int or b not in B_VALUES:
        raise ValueError('Unknown B factor')
    return Atom('B', b, b)

def operand_d(name: str) -> Atom:
    return Atom('D', name, dict(D_FACTORS)[name])

def operand_f(name: str = 'confirm') -> Atom:
    return Atom('F', name, dict(F_FACTORS)[name])

def multiply(left: Atom | Receipt, right: Atom) -> Receipt | None:
    """Undefined typed pairs return None, never a fake numeric zero."""
    if not isinstance(right, Atom) or not isinstance(left, (Atom, Receipt)):
        return None
    if isinstance(left, Atom) and left.sort == 'A' and right.sort == 'B':
        if left == operand_a(left.label) and right == operand_b(right.label):
            return Receipt('C', left, right, left.amount * right.amount, 'first')
        return None
    if isinstance(left, Receipt) and left.sort == 'C' and right.sort == 'D':
        if right.label not in dict(D_FACTORS) or right != operand_d(right.label):
            return None
        a, b = left.left.label, left.right.label
        allowed = (right.label == 'seal' and b % 2 == 0) or (
            right.label == 'inspect' and a % 2 == 0)
        return Receipt('E', left, right, left.amount * right.amount, right.label) if allowed else None
    if isinstance(left, Receipt) and left.sort == 'E' and right.sort == 'F':
        if right.label != 'confirm' or right != operand_f('confirm'):
            return None
        first = left.left
        allowed = left.operation == 'seal' and first.left.label == 1
        return Receipt('G', left, right, left.amount * right.amount, 'confirm') if allowed else None
    return None

def unpack(node: Receipt) -> tuple[Atom | Receipt, Atom]:
    if not isinstance(node, Receipt):
        raise ValueError('Only complete product receipts can be unpacked')
    return node.left, node.right

def products() -> tuple[Receipt, ...]:
    return tuple(multiply(operand_a(a), operand_b(b)) for a, b in product(A_LABELS, B_VALUES))

def positive_products() -> tuple[Receipt, ...]:
    return tuple(c for c in products() if c.left.label > 0 and c.right.label > 0)

def right_context_operands(node: Receipt) -> tuple[Atom, ...]:
    if node.sort == 'C':
        return tuple(operand_d(name) for name, _ in D_FACTORS)
    if node.sort == 'E':
        return tuple(operand_f(name) for name, _ in F_FACTORS)
    return ()

def observation(node: Receipt) -> tuple[str, int]:
    return node.sort, node.amount

def context_signature(node: Receipt, depth: int) -> tuple:
    """Recursive bounded-depth behavioral signature; None = forbidden operation."""
    if type(depth) is not int or depth < 0:
        raise ValueError('Depth must be a nonnegative integer')
    base = observation(node)
    if depth == 0:
        return (base,)
    children = tuple((op.label, None if (child := multiply(node, op)) is None
                      else context_signature(child, depth-1))
                     for op in right_context_operands(node))
    return base, children

def classes(depth: int, receipts: tuple[Receipt, ...] | None = None) -> tuple[tuple[Receipt, ...], ...]:
    groups: dict[tuple, list[Receipt]] = {}
    for c in products() if receipts is None else receipts:
        groups.setdefault(context_signature(c, depth), []).append(c)
    return tuple(tuple(g) for g in groups.values())

def all_context_words(max_depth: int) -> tuple[tuple[Atom, ...], ...]:
    if type(max_depth) is not int or max_depth < 0:
        raise ValueError('Negative context depth')
    result = [()]
    if max_depth >= 1:
        result += [(operand_d(s),) for s, _ in D_FACTORS]
    if max_depth >= 2:
        result += [(operand_d(d), operand_f(f)) for d, _ in D_FACTORS
                   for f, _ in F_FACTORS]
    return tuple(result)

def trace(node: Receipt, word: tuple[Atom, ...]) -> tuple[str, int] | None:
    """Independent interpreter for explicit right-context words."""
    for right in word:
        node = multiply(node, right)
        if node is None:
            return None
    return observation(node)

def flat_context_signature(node: Receipt, max_depth: int) -> tuple:
    return tuple(trace(node, word) for word in all_context_words(max_depth))

def measure_factors_through(depth: int) -> bool:
    """If same measured C values can always substitute through depth."""
    first = products()
    return all(x.amount != y.amount or
               context_signature(x,depth) == context_signature(y,depth)
               for x in first for y in first)

if __name__ == '__main__':
    for depth in range(4):
        print(depth, len(classes(depth)), len(classes(depth,positive_products())),
              measure_factors_through(depth))
