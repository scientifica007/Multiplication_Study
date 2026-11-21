"""Count all ordered multiplication histories for a nonnegative typed reading."""

from collections import defaultdict
from collections.abc import Iterable, Mapping

from history_codes import divisors
from history_grammar import Pair, State, analyze, distinct_atoms
from zero_histories import classify_zero


def count_histories(target: State, atoms: Iterable[State],
                    rules: Mapping[tuple[str, str], str]) -> int | float:
    """Return zero, a finite exact count, or math.inf, for a finite set of atoms."""
    kind, amount = target
    if type(amount) is not int or amount < 0:
        raise ValueError("The target amount must be a nonnegative integer")
    if amount == 0:
        return classify_zero(kind, atoms, rules).count

    candidate_amounts = divisors(amount)
    candidates = set(candidate_amounts)
    weights = {s: 1 for s in distinct_atoms(atoms) if s[1] in candidates}
    productions: dict[State, list[Pair]] = defaultdict(list)
    for (left, right), result in rules.items():
        if left == right:
            raise ValueError("A product requires different operand kinds")
        for n in candidate_amounts:
            for a in divisors(n):
                productions[result, n].append(((left, a), (right, n // a)))
    # Positive states already carry their exact amount and each leaf has weight one.
    return analyze(target, weights, productions, lambda state, index: state).count
