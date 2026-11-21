"""Independent finite-tree counts, constructive infinity witnesses and boundaries."""

import unittest
from collections import defaultdict
from itertools import combinations, product
from math import inf

from history_grammar import ProductTree
from typed_histories import count_histories
from zero_histories import POSITIVE, ZERO, classify_zero


PACKING = {("box", "rate"): "screw"}
DOUBLING = {**PACKING, ("box", "times"): "box"}


def subsets(items):
    return [s for k in range(len(items) + 1) for s in combinations(items, k)]


def enumerate_trees(atoms, rules, height):
    """Build ordered trees forwards and evaluate each product using exact integers."""
    readings = {atom: atom for atom in atoms}
    for _ in range(height):
        operands = defaultdict(list)
        for tree, (kind, amount) in readings.items():
            operands[kind].append((tree, amount))
        for (a, b), result in rules.items():
            for (left, x), (right, y) in product(operands[a], operands[b]):
                readings[ProductTree(left, right)] = (result, x * y)
    return readings


def evaluate(tree, rules, is_leaf):
    """Read back a witness without trusting any state used by the classifier."""
    if isinstance(tree, ProductTree):
        a, x = evaluate(tree.left, rules, is_leaf)
        b, y = evaluate(tree.right, rules, is_leaf)
        return rules[a, b], x * y
    if not is_leaf(tree):
        raise AssertionError(f"Unlicensed leaf: {tree!r}")
    return tree


class ZeroHistoryChecks(unittest.TestCase):
    def test_one_step_all_256_input_pairs(self):
        choices = subsets(range(4))
        for a, b in product(choices, repeat=2):
            atoms = {("box", n) for n in a} | {("rate", n) for n in b}
            trees = {ProductTree(("box", x), ("rate", y)) for x, y in product(a, b) if x * y == 0}
            result = classify_zero("screw", atoms, PACKING)
            a0, b0 = a.count(0), b.count(0)
            self.assertEqual(len(trees), a0*b0 + a0*(len(b)-b0) + (len(a)-a0)*b0)
            self.assertEqual(result.count, len(trees))
            self.assertEqual(result.families, ())
            self.assertIn(result.example, trees or {None})

    def test_full_trees_against_independent_forward_enumeration(self):
        # Both branches can be products; the largest tree height is exactly two.
        table = {("A", "B"): "L", ("B", "A"): "L", ("C", "D"): "R",
                 ("L", "R"): "G", ("R", "L"): "G", ("A", "R"): "G"}
        pool = [(k, n) for k, a in zip("ABCD", (2, 3, 5, 7)) for n in (0, a)]
        for leaves in subsets(pool):
            readings = enumerate_trees(leaves, table, 2)
            zero_trees = defaultdict(set)
            for tree, (kind, amount) in readings.items():
                if amount == 0:
                    zero_trees[kind].add(tree)
            for kind in "ABCDLRG":
                result = classify_zero(kind, leaves, table)
                self.assertEqual(result.count, len(zero_trees[kind]), (kind, leaves))
                self.assertIn(result.example, zero_trees[kind] or {None})
                self.assertFalse(result.families)

    def test_atoms_both_orders_and_mixed_positive_target(self):
        atoms = [("box", 0), ("rate", 0), ("screw", 0), ("rate", 0),
                 ("box", 2), ("rate", 3), ("box", 2)]
        rules = {**PACKING, ("rate", "box"): "screw"}
        # A zero input is a tree by itself; each ordered rule adds three trees.
        self.assertEqual(count_histories(("screw", 0), iter(atoms), rules), 7)
        self.assertEqual(count_histories(("screw", 6), atoms, rules), 2)
        self.assertEqual(count_histories(("box", 0), [], rules), 0)
        self.assertEqual(classify_zero("box", [("box", 0)] * 2, {}).example, ("box", 0))
        self.assertEqual(count_histories(("screw", 0), {("box", 10**150), ("rate", 0)}, PACKING), 1)

    def test_positive_cycle_before_a_single_zero_product(self):
        atoms = {("box", 1), ("times", 2), ("rate", 0)}
        result = classify_zero("screw", atoms, DOUBLING)
        self.assertEqual(result.count, inf)
        family, = result.families
        self.assertEqual((family.reason, family.anchor), ("productive_cycle", ("box", POSITIVE)))
        self.assertEqual((family.route[0].parent, family.loop[0].child), (("screw", ZERO), family.anchor))
        witnesses = [family.history(i) for i in range(16)]
        self.assertEqual(len(set(witnesses)), 16)
        for k, tree in enumerate(witnesses):
            self.assertEqual(evaluate(tree, DOUBLING, atoms.__contains__), ("screw", 0))
            self.assertEqual(evaluate(tree.left, DOUBLING, atoms.__contains__), ("box", 2**k))
            self.assertEqual(tree.right, ("rate", 0))

    def test_loop_through_three_kinds_and_both_operand_positions(self):
        rules = {("gate", "B"): "A", ("C", "u"): "B", ("v", "A"): "C",
                 ("stop", "A"): "target"}
        atoms = {("A", 2), ("gate", 3), ("u", 5), ("v", 7), ("stop", 0)}
        result = classify_zero("target", atoms, rules)
        self.assertEqual(result.count, inf)
        witness, = result.families
        self.assertEqual({f.parent[0] for f in witness.loop}, {"A", "B", "C"})
        self.assertEqual({f.slot for f in witness.loop}, {0, 1})
        amounts = []
        for i in range(5):
            tree = witness.history(i)
            self.assertEqual(evaluate(tree, rules, atoms.__contains__), ("target", 0))
            amounts.append(evaluate(tree.right, rules, atoms.__contains__)[1])
        self.assertTrue(all(b == a * 105 for a, b in zip(amounts, amounts[1:])))

    def test_zero_cycle_needs_a_seed_and_productive_sibling(self):
        table = {("zero", "unit"): "zero"}
        atoms = {("zero", 0), ("unit", 0)}
        family, = classify_zero("zero", atoms, table).families
        self.assertEqual((family.anchor, family.route), (("zero", ZERO), ()))
        examples = [family.history(i) for i in range(4)]
        self.assertEqual(len(set(examples)), 4)
        for tree in examples:
            self.assertEqual(evaluate(tree, table, atoms.__contains__), ("zero", 0))
        self.assertEqual(count_histories(("zero", 0), {("unit", 0)}, table), 0)
        self.assertEqual(count_histories(("zero", 0), {("zero", 0)}, table), 1)

    def test_infinite_inputs_with_no_cycle(self):
        atoms = {("rate", 0), ("box", 2)}  # The explicit box also occurs in the source.
        even = lambda i: 2 * (i + 1)
        result = classify_zero("screw", atoms, PACKING, infinite_positive={"box": even})
        self.assertEqual(result.count, inf)
        family, = result.families
        self.assertEqual((family.reason, family.anchor, family.loop), ("infinite_inputs", ("box", POSITIVE), ()))
        for k in (0, 1, 15, 10**6):
            tree = family.history(k)
            self.assertEqual(tree, ProductTree(("box", even(k)), ("rate", 0)))
            self.assertEqual(evaluate(tree, PACKING, lambda leaf: leaf in atoms or leaf == ("box", even(k))),
                             ("screw", 0))

    def test_two_causes_can_coexist_and_irrelevant_causes_are_ignored(self):
        atoms = {("rate", 0), ("times", 2)}
        result = classify_zero("screw", atoms, DOUBLING, infinite_positive={"box": lambda i: i+1})
        self.assertEqual(result.count, inf)
        self.assertEqual({f.reason for f in result.families}, {"productive_cycle", "infinite_inputs"})
        for family in result.families:
            trees = {family.history(i) for i in range(4)}
            self.assertEqual(len(trees), 4)
            for tree in trees:
                self.assertEqual(evaluate(tree, DOUBLING, lambda leaf: leaf in atoms or
                                          (leaf[0] == "box" and leaf[1] > 0)), ("screw", 0))

        def unused(_):
            raise AssertionError("Unreachable sources must not be sampled")

        unreachable = {**PACKING, ("box", "missing"): "box", ("U", "V"): "U",
                       ("U", "missing"): "screw"}
        extras = {"U": unused}
        report = classify_zero("screw", {("box", 2), ("rate", 0), ("V", 2)}, unreachable,
                               infinite_positive=extras)
        self.assertEqual((report.count, report.families), (1, ()))
        blocked = classify_zero("screw", {("rate", 3)}, PACKING, infinite_positive={"box": unused})
        self.assertEqual((blocked.count, blocked.example, blocked.families), (0, None, ()))

    def test_boundaries_and_declared_types(self):
        for n in (-1, False, 0.0):
            with self.assertRaises(ValueError):
                classify_zero("box", [("box", 0), ("box", n)], {})
            with self.assertRaises(ValueError):
                count_histories(("box", n), [], {})
        with self.assertRaises(ValueError):
            classify_zero("box", [], {("box", "box"): "box"})
        with self.assertRaises(ValueError):
            classify_zero("screw", {("rate", 0)}, PACKING, infinite_positive={"box": lambda i: 0})
        result = classify_zero("screw", {("rate", 0)}, PACKING, infinite_positive={"box": lambda i: i+1})
        for i in (-1, 0.5, True):
            with self.assertRaises(ValueError):
                result.families[0].history(i)


if __name__ == "__main__":
    unittest.main(verbosity=2)
