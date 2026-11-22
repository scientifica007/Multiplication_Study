"""Forward context checks for the backward period calculation."""

import unittest
from collections import Counter
from itertools import product
from math import gcd, lcm

from contextual_equality import DivisibilityStudy, Step, packing_study
from model import Atom, add, multiply, unpack


def finite_context_partition(moduli, rules):
    """Minimize the full finite operation table without the period recurrence."""
    modulus = lcm(*moduli.values())
    states = [(kind, n) for kind in moduli for n in range(modulus)]
    index = {s: i for i, s in enumerate(states)}
    dead = len(states)
    columns = [Step(op, fixed, on_left) for op in ("+", "*")
               for fixed in states for on_left in (True, False)]
    table = []
    for state in states:
        row = []
        for step in columns:
            left, right = (state, step.partner) if step.hole_on_left else (step.partner, state)
            pair = left[0], right[0]
            target = None
            if step.operation == "+" and left[0] == right[0]:
                target = left[0], (left[1] + right[1]) % modulus
            elif step.operation == "*" and pair in rules:
                kind, c = rules[pair]
                target = kind, (c * left[1] * right[1]) % modulus
            row.append(index.get(target, dead))
        table.append(row)
    table.append([dead] * len(columns))
    observed = [(k, n % moduli[k] == 0) for k, n in states] + [None]
    labels = observed
    layers = [labels]
    while True:
        ids = {}
        refined = []
        for i, successors in enumerate(table):
            key = (labels[i], tuple(labels[j] for j in successors))
            refined.append(ids.setdefault(key, len(ids)))
        if len(ids) == len(set(labels)):
            break
        labels = refined
        layers.append(labels)
    col = {step: j for j, step in enumerate(columns)}

    def replay(state, steps):
        i = index[state]
        for step in steps:
            k, n = step.partner
            reduced = Step(step.operation, (k, n % modulus), step.hole_on_left)
            i = table[i][col[reduced]]
        return observed[i]

    def shortest(left, right):
        a, b = index[left], index[right]
        return next((depth for depth, layer in enumerate(layers) if layer[a] != layer[b]), None)

    return dict(zip(states, refined)), replay, shortest


class SubstitutionChecks(unittest.TestCase):
    def check_against_partition(self, moduli, rules):
        study = DivisibilityStudy(moduli, rules)
        labels, replay, _ = finite_context_partition(moduli, rules)
        counts = range(lcm(*moduli.values()))
        comparisons = 0
        for kind, x, y in product(moduli, counts, counts):
            equal = labels[kind, x] == labels[kind, y]
            self.assertEqual(equal, (x - y) % study.periods[kind] == 0)
            steps = study.witness(kind, x, y)
            self.assertEqual(steps is None, equal)
            if steps is not None:
                self.assertLessEqual(len(steps), len(moduli))
                self.assertNotEqual(replay((kind, x), steps), replay((kind, y), steps))
            comparisons += 1
        return comparisons

    def test_all_contexts_in_small_ordered_tables(self):
        options = [None, *product(("A", "B"), (0, 1, 2))]
        tables = pairs = 0
        for ma, mb in product(range(1, 5), repeat=2):
            moduli = {"A": ma, "B": mb}
            for forward, reverse in product(options, repeat=2):
                rules = {k: v for k, v in [(("A", "B"), forward), (("B", "A"), reverse)]
                         if v is not None}
                pairs += self.check_against_partition(moduli, rules)
                tables += 1
        self.assertEqual((tables, pairs), (784, 47040))

    def test_complete_partitions_across_four_kinds(self):
        moduli = {"A": 1, "R": 1, "B": 2, "S": 12}
        tables = pairs = 0
        for a, b, c in product(range(4), repeat=3):
            rules = {("A", "R"): ("B", a), ("R", "B"): ("S", b), ("S", "R"): ("A", c)}
            pairs += self.check_against_partition(moduli, rules)
            tables += 1
        self.assertEqual((tables, pairs), (64, 36864))

    def test_packing_and_hole_on_each_side(self):
        study = packing_study()
        self.assertEqual(study.periods, {"box": 6, "pairs_per_box": 6, "screw": 12})
        for kind, partner, left in (("box", "pairs_per_box", True), ("pairs_per_box", "box", False)):
            steps = study.witness(kind, 1, 5)
            self.assertEqual(steps, (Step("*", (partner, 1), left), Step("+", ("screw", 2))))
            self.assertEqual([study.apply((kind, n), steps) for n in (1, 5)],
                             [("screw", 4), ("screw", 12)])
            self.assertIsNone(study.witness(kind, 1, 7))
        # No single addition or single multiplication distinguishes one box from five.
        _, replay, _ = finite_context_partition(study.moduli, study.rules)
        for op, fixed, side in product(("+", "*"), product(study.moduli, range(12)), (True, False)):
            self.assertEqual(replay(("box", 1), [Step(op, fixed, side)]),
                             replay(("box", 5), [Step(op, fixed, side)]))
        self.assertIsNone(study.apply(("box", 1), [Step("*", ("pairs_per_box", 1), False)]))
        self.assertIsNone(study.apply(("box", 1), [Step("+", ("pairs_per_box", 1))]))
        self.assertIsNone(study.apply(("box", 1), [Step("*", ("box", 1))]))
        self.assertEqual(study.witness("screw", 12, 11), ())
        self.assertEqual(study.observation(None), None)
        self.assertEqual(study.observation(("screw", 0)), ("screw", True))
        self.assertEqual(study.observation(("screw", 1)), ("screw", False))

    def test_class_pairs_and_actual_product_records(self):
        study = packing_study()
        codes = study.factor_codes("box", "pairs_per_box")
        fibres = codes.counts()
        self.assertEqual(fibres, {0: 15, 2: 2, 4: 6, 6: 5, 8: 6, 10: 2})
        self.assertEqual(sum(fibres.values()), 36)
        self.assertEqual((max(fibres.values()) - 1).bit_length(), 4)
        self.assertEqual((codes.encode(1, 2), codes.encode(2, 1)), ((4, 0), (4, 1)))
        for n, k in product(range(18), repeat=2):
            code = codes.encode(n, k)
            self.assertEqual(code[0], 2 * n * k % 12)
            self.assertEqual(codes.decode(*code), (n % 6, k % 6))
        for bad in ((0, -1), (0, 15), (1, 0), (False, 0)):
            with self.assertRaises(ValueError):
                codes.decode(*bad)
        # Convert one pair per box into an actual rate of two screws per box.
        p = multiply(Atom("box", 1), Atom("screws_per_box", 4))
        q = multiply(Atom("box", 2), Atom("screws_per_box", 2))
        self.assertEqual((p.amount, q.amount), (4, 4))
        self.assertNotEqual(unpack(p), unpack(q))
        self.assertIsNotNone(study.witness("box", 1, 2))
        self.assertIsNotNone(study.witness("pairs_per_box", 2, 1))
        for boxes in (1, 5):
            full = add(multiply(Atom("box", boxes), Atom("screws_per_box", 2)), Atom("screw", 2))
            self.assertEqual(full.amount, study.apply(("box", boxes), study.witness("box", 1, 5))[1])

    def test_repeated_product_decoding(self):
        start = Atom("apple", 1)
        totals = Counter()
        records = set()
        for choices in product((2, 3), repeat=6):
            record = start
            for r in choices:
                record = multiply(record, Atom("times", r))
            totals[record.amount] += 1
            records.add(record)
            for r in reversed(choices):
                record, factor = unpack(record)
                self.assertEqual(factor, Atom("times", r))
            self.assertEqual(record, start)
        self.assertEqual((len(records), len(totals), totals[216]), (64, 7, 20))

    def test_cycles_depth_and_combined_output_tests(self):
        study = DivisibilityStudy({"A": 1, "B": 1, "C": 1, "D": 60}, {
            ("A", "B"): ("C", 2), ("C", "B"): ("D", 3), ("D", "B"): ("A", 5)})
        self.assertEqual(study.periods, {"A": 10, "B": 20, "C": 20, "D": 60})
        steps = study.witness("A", 1, 9)
        self.assertEqual(steps, (Step("*", ("B", 1)), Step("*", ("B", 1)), Step("+", ("D", 6))))
        self.assertEqual(study.apply(("A", 9), steps), ("D", 60))
        merged = DivisibilityStudy({"A": 1, "B": 1, "C": 12, "D": 15}, {
            ("A", "B"): ("C", 2), ("B", "A"): ("D", 3)})
        self.assertEqual(merged.periods, {"A": 30, "B": 30, "C": 12, "D": 15})
        for y, side in [(6, False), (5, True)]:
            self.assertEqual(merged.witness("A", 0, y)[0].hole_on_left, side)

    def test_number_of_kinds_is_a_sharp_uniform_bound(self):
        for n in range(1, 9):
            kinds = [str(i) for i in range(n)]
            first, last = kinds[0], kinds[-1]
            moduli = dict.fromkeys(kinds, 1)
            moduli[last] = 3
            rules = {(source, last): (target, 1) for source, target in zip(kinds, kinds[1:])}
            study = DivisibilityStudy(moduli, rules)
            _, replay, shortest = finite_context_partition(moduli, rules)
            steps = study.witness(first, 1, 2)
            self.assertEqual(shortest((first, 1), (first, 2)), n)
            self.assertEqual(len(steps), n)
            self.assertEqual(steps[-1], Step("+", (last, 1)))
            self.assertNotEqual(replay((first, 1), steps), replay((first, 2), steps))

    def test_return_to_the_fruit_example_and_boundaries(self):
        fruit = DivisibilityStudy({"apple": 3}, {})
        self.assertEqual(fruit.witness("apple", 1, 2), (Step("+", ("apple", 1)),))
        self.assertIsNone(fruit.witness("apple", 2, 5))
        huge = (2 ** 127) * 45
        for c in (0, 1, 6, huge):
            study = DivisibilityStudy({"box": 1, "rate": 1, "screw": huge},
                                      {("box", "rate"): ("screw", c)})
            period = huge // gcd(huge, c)
            self.assertEqual(study.periods["box"], period)
            self.assertIsNone(study.witness("box", 10 ** 80, 10 ** 80 + period))
        for bad in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                DivisibilityStudy({"a": bad}, {})
        for args in [({"a": 1}, {("a", "a"): ("a", 1)}),
                     ({"a": 3, "b": 1}, {("a", "b"): ("c", 1)}),
                     ({"a": 3, "b": 1}, {("a", "b"): ("a", -1)})]:
            with self.assertRaises(ValueError):
                DivisibilityStudy(*args)
        with self.assertRaises(ValueError):
            fruit.witness("apple", -1, 0)


if __name__ == "__main__":
    unittest.main()
