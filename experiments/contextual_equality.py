"""Substitution under typed sums and scaled products, observed by divisibility."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import gcd, lcm
from types import MappingProxyType

from history_grammar import State


@dataclass(frozen=True)
class Step:
    """The partner is fixed. The hole receives the preceding step's result."""

    operation: str
    partner: State
    hole_on_left: bool = True


class FactorCodes:
    """Reversible tags for the ordered classes of one direct product."""

    def __init__(self, left_period: int, right_period: int, output_period: int, scale: int):
        self._periods = left_period, right_period
        self._tags = {}
        self._pairs = {}
        for x in range(left_period):
            for y in range(right_period):
                residue = scale * x * y % output_period
                pairs = self._pairs.setdefault(residue, [])
                self._tags[x, y] = (residue, len(pairs))
                pairs.append((x, y))

    def counts(self) -> dict[int, int]:
        return {r: len(pairs) for r, pairs in self._pairs.items()}

    def encode(self, x: int, y: int) -> tuple[int, int]:
        if any(type(n) is not int or n < 0 for n in (x, y)):
            raise ValueError("Expected nonnegative integer factors")
        return self._tags[x % self._periods[0], y % self._periods[1]]

    def decode(self, residue: int, tag: int) -> tuple[int, int]:
        if type(residue) is not int or residue not in self._pairs:
            raise ValueError("Unattainable residue")
        pairs = self._pairs[residue]
        if type(tag) is not int or not 0 <= tag < len(pairs):
            raise ValueError("Tag outside the residue's fibre")
        return pairs[tag]


class DivisibilityStudy:
    def __init__(self, moduli: Mapping[str, int],
                 rules: Mapping[tuple[str, str], tuple[str, int]]):
        if not moduli or any(type(m) is not int or m < 1 for m in moduli.values()):
            raise ValueError("Each kind needs a positive integer test modulus")
        self.moduli = MappingProxyType(dict(moduli))
        products = {}
        for (left, right), (result, scale) in rules.items():
            if left == right or any(k not in moduli for k in (left, right, result)):
                raise ValueError("A product requires two different known kinds and a known result")
            if type(scale) is not int or scale < 0:
                raise ValueError("Product scales must be nonnegative integers")
            products[left, right] = (result, scale)
        self.rules = MappingProxyType(products)

        # Layer h records what can reach a final test through at most h products.
        self._layers = [dict(moduli)]
        for _ in range(len(moduli) - 1):
            previous = self._layers[-1]
            current = previous.copy()
            for (left, right), (target, scale) in products.items():
                needed = previous[target] // gcd(previous[target], scale)
                for source in (left, right):
                    current[source] = lcm(current[source], needed)
            if current == previous:
                break
            self._layers.append(current)
        self.periods = MappingProxyType(self._layers[-1])

    def _check(self, kind: str, amount: int) -> None:
        if kind not in self.moduli or type(amount) is not int or amount < 0:
            raise ValueError("Expected a known kind and a nonnegative integer count")

    def observation(self, state: State | None) -> tuple[str, bool] | None:
        if state is None:
            return None
        kind, amount = state
        self._check(kind, amount)
        return kind, amount % self.moduli[kind] == 0

    def apply(self, state: State, context: Iterable[Step]) -> State | None:
        kind, amount = state
        self._check(kind, amount)
        for step in context:
            partner, count = step.partner
            self._check(partner, count)
            if step.operation == "+":
                if partner != kind:
                    return None
                amount += count
            elif step.operation == "*":
                pair = (kind, partner) if step.hole_on_left else (partner, kind)
                if pair not in self.rules:
                    return None
                kind, scale = self.rules[pair]
                amount *= scale * count
            else:
                raise ValueError("Unknown operation")
        return kind, amount

    def witness(self, kind: str, x: int, y: int) -> tuple[Step, ...] | None:
        """Return an executable context or None if all contexts agree."""
        self._check(kind, x)
        self._check(kind, y)
        if (x - y) % self.periods[kind] == 0:
            return None
        steps = []
        for shorter in reversed(self._layers[:-1]):
            if (x - y) % shorter[kind]:
                continue  # A shorter product path already distinguishes this pair.
            for (left, right), (target, scale) in self.rules.items():
                if kind in (left, right) and scale * (x - y) % shorter[target]:
                    hole_on_left = kind == left
                    partner = right if hole_on_left else left
                    steps.append(Step("*", (partner, 1), hole_on_left))
                    kind, x, y = target, scale * x, scale * y
                    break
            else:
                raise AssertionError("Missing edge for a strict period refinement")
        modulus = self.moduli[kind]
        if (x % modulus == 0) == (y % modulus == 0):
            shift = min((-x) % modulus, (-y) % modulus)
            steps.append(Step("+", (kind, shift)))
        return tuple(steps)

    def factor_codes(self, left: str, right: str) -> FactorCodes:
        """Enumerate class pairs only when a codebook for this rule is requested."""
        target, scale = self.rules[left, right]
        return FactorCodes(self.periods[left], self.periods[right], self.periods[target], scale)


def packing_study() -> DivisibilityStudy:
    return DivisibilityStudy(
        {"box": 1, "pairs_per_box": 1, "screw": 12},
        {("box", "pairs_per_box"): ("screw", 2)},
    )


if __name__ == "__main__":
    study = packing_study()
    print("عدد الفئات (علب، أزواج لكل علبة، مسامير):",
          tuple(study.periods[k] for k in ("box", "pairs_per_box", "screw")))
    context = study.witness("box", 1, 5)
    assert context is not None
    print("زوج في كل علبة، ثم نضيف مسمارين. عدد العلب | عدد المسامير | حكم الفحص")
    for count in (1, 5):
        result = study.apply(("box", count), context)
        verdict = "تكتمل الدزينة" if study.observation(result)[1] else "تبقى مسامير خارج الدزينة"
        print(f"{count} | {result[1]} | {verdict}")
    print("تكافؤ علبة وسبع علب في كل السياقات:", "نعم" if study.witness("box", 1, 7) is None else "لا")
    codes = study.factor_codes("box", "pairs_per_box")
    print("أزواج فئات العاملين لكل باقٍ:", sorted(codes.counts().items()))
    for factors in ((1, 2), (2, 1)):
        code = codes.encode(*factors)
        print("الباقي ورقم الزوج:", code, "| الفئتان بعد الفكّ:", codes.decode(*code))
