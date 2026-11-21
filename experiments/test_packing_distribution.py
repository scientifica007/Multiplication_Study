"""Exact distribution, inverse factors and independent enumeration of packing records."""

import unittest
from itertools import product

from model import Atom, Undefined, add as tree_add, multiply as tree_pack, reading
from packing_distribution import BOX, RATE, Shipment, add, pack


def boxes(n):
    return Atom(BOX, n)


def rate(r):
    return Atom(RATE, r)


class PackingDistributionChecks(unittest.TestCase):
    def test_typed_domains_and_numeric_inputs(self):
        a, b = boxes(2), rate(3)
        p = pack(a, b)
        self.assertEqual(p.unpack(), (a, b))
        for left, right in product((a, b, p), repeat=2):
            if (left, right) != (a, b):
                with self.assertRaises(Undefined):
                    pack(left, right)
            if type(left) is not type(right) or (isinstance(left, Atom) and left.kind != right.kind):
                with self.assertRaises(Undefined):
                    add(left, right)
        with self.assertRaises(Undefined):
            pack(tree_add(a, a), b)  # A history from the syntax-tree model is a different input.
        with self.assertRaises(Undefined):
            add(Atom("apple", 1), Atom("apple", 2))
        for value in (-1, 0.5, True):
            for row in ((value, 0), (0, value)):
                with self.assertRaises(ValueError):
                    Shipment((row,))
        huge = 10**90
        self.assertEqual(pack(boxes(huge), rate(huge)).screw_count, huge**2)

    def test_distributing_over_box_counts_and_rates(self):
        count_equal = rate_equal = 0
        for n, k, r in product(range(8), repeat=3):
            first = pack(add(boxes(n), boxes(k)), rate(r))
            split = add(pack(boxes(n), rate(r)), pack(boxes(k), rate(r)))
            self.assertEqual(first, split)
            self.assertEqual(first.unpack(), (boxes(n + k), rate(r)))
            self.assertEqual(split.screw_count, (n + k) * r)
            count_equal += first == split

            second = pack(boxes(n), add(rate(k), rate(r)))
            split_rate = add(pack(boxes(n), rate(k)), pack(boxes(n), rate(r)))
            self.assertEqual(second.screw_count, split_rate.screw_count)
            self.assertEqual((second.box_count, split_rate.box_count), (n, 2*n))
            self.assertEqual(second == split_rate, n == k == r == 0)
            rate_equal += second == split_rate
        self.assertEqual((count_equal, rate_equal), (512, 1))

    def test_unit_batch_generates_disjoint_positive_sequences(self):
        seen = set()
        for r in range(8):
            unit = pack(boxes(1), rate(r))
            record = unit
            for n in range(1, 17):
                self.assertEqual(record, pack(boxes(n), rate(r)))
                self.assertEqual(record.unpack(), (boxes(n), rate(r)))
                self.assertNotIn(record, seen)
                self.assertEqual(record.without_empty_rates(), record)
                seen.add(record)
                record = add(record, unit)
        self.assertEqual(len(seen), 128)
        six_at_two, four_at_three = pack(boxes(6), rate(2)), pack(boxes(4), rate(3))
        self.assertEqual(six_at_two.screw_count, four_at_three.screw_count)
        self.assertNotEqual(six_at_two, four_at_three)

    def test_merges_against_individual_boxes_and_declared_rates(self):
        rates = (0, 2, 5)
        # Each rate is absent, declared empty, or used by one or two physical boxes.
        cases = []
        for counts in product((None, 0, 1, 2), repeat=3):
            record = Shipment()
            declared, physical_boxes = set(), []
            for r, n in zip(rates, counts):
                if n is not None:
                    record = add(record, pack(boxes(n), rate(r)))
                    declared.add(r)
                    physical_boxes.extend([r] * n)
            cases.append((record, declared, physical_boxes))
        self.assertEqual(len({record for record, _, _ in cases}), 64)
        for (left, labels_a, boxes_a), (right, labels_b, boxes_b) in product(cases, repeat=2):
            measured = boxes_a + boxes_b
            expected = tuple((r, measured.count(r)) for r in sorted(labels_a | labels_b))
            merged = add(left, right)
            self.assertEqual(merged.rows, expected)
            self.assertEqual(merged, add(right, left))
            self.assertEqual((merged.box_count, merged.screw_count), (len(measured), sum(measured)))
            self.assertEqual(merged.without_empty_rates(),
                             add(left.without_empty_rates(), right.without_empty_rates()))
            if len(expected) == 1:
                r, n = expected[0]
                self.assertEqual(merged.unpack(), (boxes(n), rate(r)))
            else:
                with self.assertRaises(Undefined):
                    merged.unpack()

    def test_zero_boxes_and_zero_rate(self):
        empty = Shipment()
        flags = [pack(boxes(0), rate(r)) for r in range(8)]
        self.assertEqual(len(set(flags)), 8)
        self.assertEqual({flag.without_empty_rates() for flag in flags}, {empty})
        for r, flag in enumerate(flags):
            shipment = pack(boxes(2), rate(r))
            self.assertEqual(flag.unpack(), (boxes(0), rate(r)))
            self.assertNotEqual(flag, empty)
            self.assertEqual(add(flag, flag), flag)
            self.assertEqual(add(shipment, flag), add(shipment, empty))
            self.assertEqual(add(shipment, flag), shipment)
        with self.assertRaises(Undefined):
            empty.unpack()
        mixed = add(flags[3], flags[6])
        self.assertEqual((mixed.rows, mixed.box_count, mixed.screw_count), (((3, 0), (6, 0)), 0, 0))
        with self.assertRaises(Undefined):
            mixed.unpack()
        positive_zero_rate = pack(boxes(4), rate(0))
        self.assertEqual(positive_zero_rate.without_empty_rates().unpack(), (boxes(4), rate(0)))
        self.assertEqual(positive_zero_rate.screw_count, 0)

    def test_addition_history_and_two_readings(self):
        a, b = boxes(2), rate(3)
        p = pack(a, b)
        same_rate, doubled_rate = add(p, p), pack(a, add(b, b))
        self.assertEqual(same_rate.unpack(), (boxes(4), rate(3)))
        self.assertEqual(doubled_rate.unpack(), (boxes(2), rate(6)))
        self.assertEqual(same_rate.screw_count, doubled_rate.screw_count)
        self.assertNotEqual(same_rate, doubled_rate)
        self.assertEqual(add(pack(boxes(1), b), pack(boxes(3), b)), same_rate)
        mixed = add(pack(boxes(1), rate(2)), pack(boxes(1), rate(4)))
        self.assertEqual((mixed.box_count, mixed.screw_count), (p.box_count, p.screw_count))
        self.assertNotEqual(mixed, p)
        with self.assertRaises(Undefined):
            mixed.unpack()
        flag = pack(boxes(0), rate(6))
        self.assertEqual(add(add(p, mixed), flag), add(p, add(mixed, flag)))
        before, after = tree_pack(tree_add(a, a), b), tree_add(tree_pack(a, b), tree_pack(a, b))
        self.assertEqual(reading(before), reading(after))
        self.assertNotEqual(before, after)

    def test_two_sided_distribution_with_idempotent_additions(self):
        # All 16 binary operations on each of two two-element tagged sorts.
        # The output stores the ordered pair, with addition applied coordinatewise.
        values = (0, 1)
        triples = tuple(product(values, repeat=3))
        tables = tuple(product(values, repeat=4))
        both = 0
        for table_a, table_b in product(tables, repeat=2):
            def input_a(a, c):
                return table_a[2*a + c]

            def input_b(b, d):
                return table_b[2*b + d]

            def merge(left, right):
                return input_a(left[0], right[0]), input_b(left[1], right[1])

            over_a = all((input_a(a, c), b) == merge((a, b), (c, b)) for a, c, b in triples)
            over_b = all((a, input_b(b, d)) == merge((a, b), (a, d)) for a, b, d in triples)
            self.assertEqual(over_a, all(input_b(b, b) == b for b in values))
            self.assertEqual(over_b, all(input_a(a, a) == a for a in values))
            both += over_a and over_b
        self.assertEqual(both, 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
