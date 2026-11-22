"""Check addition records against raw terms and direct multiset enumeration."""

import unittest
from collections import Counter, defaultdict
from functools import reduce
from itertools import combinations_with_replacement, product
from math import comb

from contextual_equality import packing_study
from model import Atom, Lift, Undefined, add, multiply, unpack
from packing_distribution import add as merge_shipments, pack
from sum_memory import (Factors, SumCodes, add_views, describe, multiply_views,
                        recover_summand, view_counts)


def lot(boxes, pairs):
    return multiply(Atom("box", boxes), Atom("screws_per_box", 2 * pairs))


def sum_trees(word):
    if len(word) == 1:
        yield word[0]
    for cut in range(1, len(word)):
        for left in sum_trees(word[:cut]):
            for right in sum_trees(word[cut:]):
                yield add(left, right)


class SumMemoryChecks(unittest.TestCase):
    def test_all_parenthesizations_and_last_splits(self):
        p, q = lot(1, 2), lot(2, 1)
        self.assertEqual((p.amount, q.amount), (4, 4))
        self.assertNotEqual(unpack(p), unpack(q))
        trees = Counter()
        ordered, unordered = defaultdict(set), defaultdict(set)
        for n in range(1, 6):
            for word in product((p, q), repeat=n):
                expected = describe(reduce(add, word), 1)
                for root in sum_trees(word):
                    summary = describe(root, 1)
                    self.assertEqual(summary, expected)
                    trees[summary] += 1
                    if n > 1:
                        children = describe(root.left, 1), describe(root.right, 1)
                        ordered[summary].add(children)
                        unordered[summary].add(frozenset(children))
                        self.assertEqual(recover_summand(summary, children[0]), children[1])
        for summary in trees:
            self.assertEqual(summary.last_split_counts(),
                             (len(ordered[summary]), len(unordered[summary])))
        four = describe(add(add(p, p), add(q, q)), 1)
        self.assertEqual((sum(trees.values()), trees[four], four.last_split_counts()),
                         (550, 30, (7, 4)))
        self.assertEqual(describe(add(add(p, p), add(p, p)), 1).last_split_counts(), (3, 2))

    def test_pairing_same_measures_and_distribution(self):
        first = ((1, 1), (2, 3), (3, 2))
        second = ((1, 2), (2, 1), (3, 3))
        for i in (0, 1):
            self.assertEqual(sorted(s[i] for s in first), sorted(s[i] for s in second))
        a, b = (reduce(add, (lot(*s) for s in shipment)) for shipment in (first, second))
        self.assertEqual((a.amount, b.amount), (26, 26))
        self.assertEqual(describe(a, 0), describe(b, 0))
        self.assertNotEqual(describe(a, 1), describe(b, 1))
        rate = Atom("screws_per_box", 4)
        one = pack(Atom("box", 1), rate)
        self.assertEqual(merge_shipments(one, one), pack(Atom("box", 2), rate))
        self.assertNotEqual(describe(add(lot(1, 2), lot(1, 2)), 1), describe(lot(2, 2), 1))

    def test_cutoff_forward_updates_and_coalescing(self):
        a, times = Atom("apple", 2), Atom("times", 3)
        b = multiply(Atom("apple", 1), Atom("times", 2))
        p, q = (multiply(x, times) for x in (a, b))
        mixed = add(p, q)
        for modulus in (None, 1, 5):
            for depth in range(4):
                vp, vq = (describe(x, depth, modulus) for x in (p, q))
                vm = describe(mixed, depth, modulus)
                self.assertEqual(add_views(vp, vq), vm)
                self.assertEqual(multiply_views(vm, describe(times, depth, modulus)),
                                 describe(multiply(mixed, times), depth, modulus))
                self.assertEqual(vm.shallower(), describe(mixed, max(0, depth - 1), modulus))
        fine = describe(mixed, 2)
        self.assertEqual(len(fine.parts), 2)
        self.assertEqual([n for _, n in fine.shallower().parts], [2])
        self.assertTrue(all(isinstance(card, Factors) for card, _ in fine.parts))
        for x, y in ((Atom("box", 2), Atom("screws_per_box", 2)),
                     (Atom("screws_per_box", 2), Atom("box", 2))):
            result = multiply_views(describe(x, 1), describe(y, 1))
            self.assertEqual(result, describe(multiply(x, y), 1))
        self.assertNotEqual(describe(multiply(x, y), 1), describe(multiply(y, x), 1))
        lifted = add(Lift(Atom("apple", 2), "fruit"), Lift(Atom("pear", 2), "fruit"))
        self.assertEqual(dict(describe(lifted, 1).parts), {("fruit", 2): 2})

    def test_both_growth_bounds(self):
        for kinds, rules, inputs in [
            (("apple", "times"), {("apple", "times"): "apple"}, (1, 1)),
            (("bundle", "boxes_per_bundle", "box", "screws_per_box", "screw"),
             {("bundle", "boxes_per_bundle"): "box", ("box", "screws_per_box"): "screw"},
             (1, 2, 2, 3, 6)),
        ]:
            atoms = {k: Atom(k, value) for k, value in zip(kinds, inputs)}
            previous = {k: [atom] for k, atom in atoms.items()}
            for h in (1, 2):
                cards = {k: [atom] for k, atom in atoms.items()}
                for (left, right), target in rules.items():
                    cards[target].extend(multiply(x, y) for x in previous[left] for y in previous[right])
                following = {}
                for k, options in cards.items():
                    terms = options + [add(x, y) for x, y in combinations_with_replacement(options, 2)]
                    following[k] = list({describe(t, h, 1): t for t in terms}.values())
                sizes = view_counts(dict.fromkeys(kinds, 1), dict.fromkeys(kinds, 1), rules, h, 2)
                self.assertEqual(sizes, {k: len(v) for k, v in following.items()})
                previous = following
            self.assertEqual(len(previous["apple" if "apple" in kinds else "screw"]), 77)
        p, q = lot(1, 2), lot(2, 1)
        for n in range(1, 13):
            words = [[p] * j + [q] * (n - j) for j in range(n + 1)]
            results = {describe(reduce(add, word), 1) for word in words}
            self.assertEqual(len(results), n + 1)
            self.assertEqual({v.value for v in results}, {4 * n})

    def test_sum_between_products_with_a_change_of_kind(self):
        boxes = multiply(Atom("bundle", 2), Atom("boxes_per_bundle", 3))
        staged = multiply(add(boxes, Atom("box", 1)), Atom("screws_per_box", 2))
        direct = multiply(Atom("box", 7), Atom("screws_per_box", 2))
        self.assertEqual((staged.kind, staged.amount), ("screw", 14))
        self.assertEqual(describe(staged, 1), describe(direct, 1))
        self.assertNotEqual(describe(staged, 2), describe(direct, 2))
        outer, = dict(describe(staged, 2).parts)
        self.assertEqual(outer.left, add_views(describe(boxes, 1), describe(Atom("box", 1), 1)))
        self.assertEqual(outer.right, describe(Atom("screws_per_box", 2), 1))

    def test_conditional_codes_against_every_small_manifest(self):
        study = packing_study()
        labels = list(product(range(6), repeat=2))
        checked = 0
        for n in range(5):
            codes = SumCodes(study, "box", "pairs_per_box", n)
            ranks = Counter()
            for lots in combinations_with_replacement(labels, n):
                r = sum(2 * x * y for x, y in lots) % 12
                code = r, ranks[r]
                self.assertEqual(codes.encode(reversed(lots)), code)
                self.assertEqual(codes.decode(*code), lots)
                ranks[r] += 1
                checked += 1
            self.assertEqual(codes.counts, tuple(ranks[i] for i in range(12)))
            self.assertEqual(sum(codes.counts), comb(35 + n, n))
        self.assertEqual(checked, 91390)

    def test_two_lots_residue_formula_and_exact_large_tags(self):
        study = packing_study()
        w = study.factor_codes("box", "pairs_per_box").counts()
        codes = SumCodes(study, "box", "pairs_per_box", 2)
        for s, count in enumerate(codes.counts):
            ordered = sum(v * w.get((s - r) % 12, 0) for r, v in w.items())
            diagonal = sum(v for r, v in w.items() if 2 * r % 12 == s)
            self.assertEqual(2 * count, ordered + diagonal)
        self.assertEqual(codes.counts[::2], (175, 72, 124, 99, 124, 72))
        self.assertEqual(codes.encode([(7, 8), (8, 7)]), codes.encode([(1, 2), (2, 1)]))
        large = SumCodes(study, "box", "pairs_per_box", 48)
        tag = large.counts[0] - 1
        self.assertGreater(tag, 2 ** 64)
        self.assertEqual(large.encode(large.decode(0, tag)), (0, tag))

    def test_valid_zero_lots_and_invalid_settings(self):
        p, z = lot(1, 2), lot(0, 2)
        total, vp, vz = (describe(t, 1) for t in (add(p, z), p, z))
        self.assertEqual(total.value, vp.value)
        self.assertNotEqual(total, vp)
        self.assertEqual(recover_summand(total, vp), vz)
        for other in (total, describe(lot(5, 5), 1)):
            with self.assertRaises(Undefined):
                recover_summand(total, other)
        with self.assertRaises(Undefined):
            add_views(vp, describe(Atom("apple", 4), 1))
        with self.assertRaises(Undefined):
            multiply_views(vp, vp)
        with self.assertRaises(ValueError):
            add_views(vp, describe(p, 1, 3))
        with self.assertRaises(ValueError):
            describe(p, 0).last_split_counts()
        for h, m in [(-1, None), (True, 12), (1, 0)]:
            with self.assertRaises(ValueError):
                describe(p, h, m)
        with self.assertRaises(ValueError):
            view_counts({"a": 1}, {"a": 1}, {("a", "a"): "a"}, 1, 2)
        book = SumCodes(packing_study(), "box", "pairs_per_box", 2)
        for code in ((0, -1), (0, 175), (1, 0), (12, 0), (False, 0)):
            with self.assertRaises(ValueError):
                book.decode(*code)
        with self.assertRaises(ValueError):
            book.encode([(1, 2)])


if __name__ == "__main__":
    unittest.main()
