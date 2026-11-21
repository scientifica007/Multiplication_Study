"""Classify complete histories of a typed zero with kind-dependent multiplication."""

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from math import inf

from history_grammar import Classification, History, Pair, ProductTree, State, analyze, distinct_atoms

ZERO = 0
POSITIVE = 1  # A class in the grammar, independent of the actual positive amount.


def classify_zero(
    kind: str,
    atoms: Iterable[State],
    rules: Mapping[tuple[str, str], str],
    *,
    infinite_positive: Mapping[str, Callable[[int], int]] | None = None,
) -> Classification:
    """Count histories with root (kind, 0), retaining witnesses with exact leaf amounts.

    The finite atoms are (kind, amount) pairs. Each additional infinite source
    maps indices 0, 1, ... to distinct positive amounts of its kind.
    """
    sources = dict(infinite_positive or {})
    choices: dict[State, list[int]] = defaultdict(list)
    for name, amount in sorted(distinct_atoms(atoms)):
        sign = ZERO if amount == 0 else POSITIVE
        choices[name, sign].append(amount)
    weights: dict[State, int | float] = {s: len(items) for s, items in choices.items()}
    for name in sources:
        weights[name, POSITIVE] = inf

    def leaf_at(state: State, index: int) -> State:
        name, sign = state
        if sign == POSITIVE and name in sources:
            value = sources[name](index)
            if type(value) is not int or value <= 0:
                raise ValueError("An infinite positive source must return positive integers")
            return name, value
        return name, choices[state][index]

    productions: dict[State, list[Pair]] = defaultdict(list)
    for (left, right), result in rules.items():
        if left == right:
            raise ValueError("A product requires different operand kinds")
        for a in (ZERO, POSITIVE):
            for b in (ZERO, POSITIVE):
                productions[result, a * b].append(((left, a), (right, b)))
    return analyze((kind, ZERO), weights, productions, leaf_at)


if __name__ == "__main__":
    packing = {("box", "rate"): "screw"}
    doubling = {**packing, ("box", "times"): "box"}
    cases = [
        ("لا يوجد معدل صفري", {("box", 2), ("rate", 3)}, packing, {}),
        ("دفعة واحدة ومعدل صفري", {("box", 2), ("rate", 0)}, packing, {}),
        ("خمسة أزواج تعطي صفرًا", {("box", n) for n in (0, 2, 5)} |
         {("rate", n) for n in (0, 3, 7)}, packing, {}),
        ("تضاعف الدفعة قبل تطبيق معدل التعبئة الصفري", {("box", 1), ("times", 2), ("rate", 0)}, doubling, {}),
        ("كل عدد موجب من العلب مدخل أولي", {("rate", 0)}, packing, {"box": lambda i: i + 1}),
    ]
    labels = {"productive_cycle": "خطوات ضرب يمكن تكرارها ثم إكمال التاريخ",
              "infinite_inputs": "مدخلات أولية مختلفة بلا حد"}
    quantities = {"box": "عدد العلب", "rate": "مسامير لكل علبة", "times": "معامل التكرار"}

    def display(tree: History) -> str:
        if isinstance(tree, ProductTree):
            return f"({display(tree.left)} × {display(tree.right)})"
        kind, amount = tree
        return f"[{quantities[kind]} = {amount}]"

    for title, leaves, table, sources in cases:
        answer = classify_zero("screw", leaves, table, infinite_positive=sources)
        count = "∞" if answer.count == inf else str(answer.count)
        print(f"{title} — عدد التواريخ {count}")
        for witness in answer.families:
            print("  " + labels[witness.reason])
            for index in (0, 1):
                print("  " + display(witness.history(index)))
