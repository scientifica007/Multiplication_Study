"""What an associative, commutative sum can retain about ordered products."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import comb, prod

from contextual_equality import DivisibilityStudy, packing_study
from history_grammar import State
from model import PRODUCTS, Binary, Quantity, Undefined


@dataclass(frozen=True)
class Factors:
    left: View
    right: View


def _read(n: int, modulus: int | None) -> int:
    return n if modulus is None else n % modulus


@dataclass(frozen=True)
class View:
    kind: str
    value: int
    depth: int
    modulus: int | None
    # An input label (kind, reading) or an ordered product, paired with its multiplicity.
    parts: frozenset[tuple[State | Factors, int]] = frozenset()

    def shallower(self) -> View:
        if self.depth == 0:
            return self
        parts = Counter()
        if self.depth > 1:
            for card, count in self.parts:
                if isinstance(card, Factors):
                    card = Factors(card.left.shallower(), card.right.shallower())
                parts[card] += count
        return View(self.kind, self.value, self.depth - 1, self.modulus, frozenset(parts.items()))

    def last_split_counts(self) -> tuple[int, int]:
        """Numbers of ordered/unordered splits into two nonempty sub-bags."""
        if self.depth == 0:
            raise ValueError("A reading alone does not specify the constituents")
        choices = prod(count + 1 for _, count in self.parts)
        return max(choices - 2, 0), (choices - 1) // 2


def describe(term: Quantity, depth: int, modulus: int | None = None) -> View:
    if type(depth) is not int or depth < 0:
        raise ValueError("Depth must be a nonnegative integer")
    if modulus is not None and (type(modulus) is not int or modulus < 1):
        raise ValueError("Modulus must be a positive integer")

    def visit(root: Quantity, remaining: int) -> View:
        value = _read(root.amount, modulus)
        if remaining == 0:
            return View(root.kind, value, 0, modulus)
        parts = Counter()
        pending = [root]
        while pending:
            t = pending.pop()
            if isinstance(t, Binary):
                if t.operator == "+":
                    pending.extend((t.left, t.right))
                    continue
                card = Factors(visit(t.left, remaining - 1), visit(t.right, remaining - 1))
            else:
                # Initial or lifted inputs are labelled at the boundary of this experiment.
                card = (t.kind, _read(t.amount, modulus))
            parts[card] += 1
        return View(root.kind, value, remaining, modulus, frozenset(parts.items()))

    return visit(term, depth)


def _same_experiment(left: View, right: View) -> None:
    if (left.depth, left.modulus) != (right.depth, right.modulus):
        raise ValueError("The operands use different observation settings")


def add_views(left: View, right: View) -> View:
    _same_experiment(left, right)
    if left.kind != right.kind:
        raise Undefined("Addition requires a common kind")
    counts = Counter(dict(left.parts))
    counts.update(dict(right.parts))
    value = _read(left.value + right.value, left.modulus)
    return View(left.kind, value, left.depth, left.modulus, frozenset(counts.items()))


def recover_summand(total: View, known: View) -> View:
    """Recover the other nonempty contribution when one sub-bag is supplied."""
    _same_experiment(total, known)
    if total.depth == 0 or total.kind != known.kind:
        raise Undefined("Expected constituent records of the same kind")
    whole, part = Counter(dict(total.parts)), Counter(dict(known.parts))
    if not part or not part < whole:
        raise Undefined("Expected a proper nonempty sub-bag")
    value = _read(total.value - known.value, total.modulus)
    return View(total.kind, value, total.depth, total.modulus, frozenset((whole - part).items()))


def multiply_views(left: View, right: View) -> View:
    _same_experiment(left, right)
    pair = left.kind, right.kind
    if pair not in PRODUCTS:
        raise Undefined("No product for these ordered kinds")
    parts = frozenset()
    if left.depth > 0:
        parts = frozenset({(Factors(left.shallower(), right.shallower()), 1)})
    value = _read(left.value * right.value, left.modulus)
    return View(PRODUCTS[pair], value, left.depth, left.modulus, parts)


def view_counts(frontier: Mapping[str, int], atoms: Mapping[str, int],
                rules: Mapping[tuple[str, str], str], depth: int, width: int) -> dict[str, int]:
    """Reachable view counts with at most width nonempty constituents per exposed sum."""
    if type(depth) is not int or depth < 0 or type(width) is not int or width < 1:
        raise ValueError("Expected a nonnegative depth and a positive width")
    if not frontier or frontier.keys() != atoms.keys():
        raise ValueError("Both catalogues must specify the same kinds")
    if any(type(n) is not int or n < 0 for n in (*frontier.values(), *atoms.values())):
        raise ValueError("Catalogue sizes must be nonnegative integers")
    for (left, right), target in rules.items():
        if left == right or not {left, right, target} <= frontier.keys():
            raise ValueError("Invalid ordered product rule")
    sizes = dict(frontier)
    for _ in range(depth):
        cards = dict(atoms)
        for (left, right), target in rules.items():
            cards[target] += sizes[left] * sizes[right]
        sizes = {kind: comb(n + width, width) - 1 for kind, n in cards.items()}
    return sizes


class SumCodes:
    """Rank and unrank unordered lots of one product rule given size and total residue."""

    def __init__(self, study: DivisibilityStudy, left: str, right: str, size: int):
        if type(size) is not int or size < 0:
            raise ValueError("Lot count must be a nonnegative integer")
        self.size = size
        target, _ = study.rules[left, right]
        self.modulus = study.periods[target]
        self._book = study.factor_codes(left, right)
        cards = sorted((self._book.decode(r, tag), (r, tag))
                       for r, count in self._book.counts().items() for tag in range(count))
        self._labels = [label for label, _ in cards]
        self._weights = [code[0] for _, code in cards]
        self._index = {code: i for i, (_, code) in enumerate(cards)}
        m, d = self.modulus, len(cards)
        # table[k][i][r] counts size-k bags of residue r using card types i and above.
        empty = (1,) + (0,) * (m - 1)
        self._table = [[empty] * (d + 1)]
        for _ in range(size):
            prev = self._table[-1]
            current = [(0,) * m] * (d + 1)
            for i in reversed(range(d)):
                w = self._weights[i]
                current[i] = tuple(current[i + 1][r] + prev[i][(r - w) % m] for r in range(m))
            self._table.append(current)

    @property
    def counts(self) -> tuple[int, ...]:
        return self._table[self.size][0]

    def encode(self, lots: Iterable[tuple[int, int]]) -> tuple[int, int]:
        indices = sorted(self._index[self._book.encode(x, y)] for x, y in lots)
        if len(indices) != self.size:
            raise ValueError("Incorrect number of lots")
        residue = sum(self._weights[i] for i in indices) % self.modulus
        remaining, first, tag = residue, 0, 0
        for pos, i in enumerate(indices):
            suffix = self._table[self.size - pos - 1]
            for j in range(first, i):
                tag += suffix[j][(remaining - self._weights[j]) % self.modulus]
            remaining = (remaining - self._weights[i]) % self.modulus
            first = i
        return residue, tag

    def decode(self, residue: int, tag: int) -> tuple[tuple[int, int], ...]:
        if type(residue) is not int or not 0 <= residue < self.modulus:
            raise ValueError("Invalid residue")
        if type(tag) is not int or not 0 <= tag < self.counts[residue]:
            raise ValueError("No bag with this tag at this residue")
        recovered = []
        first = 0
        for k in reversed(range(self.size)):
            for i in range(first, len(self._labels)):
                remaining = (residue - self._weights[i]) % self.modulus
                block = self._table[k][i][remaining]
                if tag < block:
                    recovered.append(self._labels[i])
                    residue, first = remaining, i
                    break
                tag -= block
            else:
                raise AssertionError("No completion for an in-range tag")
        return tuple(recovered)


if __name__ == "__main__":
    receipts = SumCodes(packing_study(), "box", "pairs_per_box", 2)
    print("باقي المسامير | عدد الأوصاف الممكنة لدفعتين")
    for residue, count in enumerate(receipts.counts):
        if count:
            print(f"{residue} | {count}")
    p, q = (1, 2), (2, 1)
    for lots in ((p, p), (p, q), (q, q)):
        code = receipts.encode(lots)
        print("الباقي والرمز:", code, "| فئتا العاملين في كل دفعة:", receipts.decode(*code))
