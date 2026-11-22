"""Independent forward packing, separator enumeration, and exact receipt round trips."""

import unittest
from collections import defaultdict
from itertools import combinations_with_replacement, product
from math import comb, inf, isqrt

from batch_receipts import BatchReceipts
from model import Atom
from packing_distribution import BOX, RATE, Shipment, add, pack


def partitions_by_cuts(n):
    """Place cuts between n consecutive boxes, then forget the order of the lots."""
    results = set()
    for mask in range(1 << (n - 1)):
        ends = [0] + [j for j in range(1, n) if mask & (1 << (j - 1))] + [n]
        results.add(tuple(sorted(b - a for a, b in zip(ends, ends[1:]))))
    return results


class BatchReceiptChecks(unittest.TestCase):
    def test_four_boxes_and_partition_bijection(self):
        book = BatchReceipts(Shipment(((3, 4),)))
        expected = [(4,), (1, 3), (2, 2), (1, 1, 2), (1, 1, 1, 1)]
        for tag, sizes in enumerate(expected):
            lots = tuple((n, 3) for n in sizes)
            self.assertEqual(book.decode(tag), lots)
            self.assertEqual(book.encode(reversed(lots)), tag)
        self.assertEqual((book.count(), book.fixed_bits(), book.count(2), book.fixed_bits(2)),
                         (5, 3, 2, 1))
        for n in range(1, 13):
            book = BatchReceipts(Shipment(((3, n),)))
            cuts = partitions_by_cuts(n)
            self.assertEqual(book.count(), len(cuts))
            self.assertEqual({tuple(j for j, _ in book.decode(t)) for t in range(book.count())}, cuts)
            for k in range(n + 2):
                self.assertEqual(book.count(k), sum(len(row) == k for row in cuts))

    def test_small_shipments_against_forward_enumeration(self):
        rates = (0, 2, 5)
        cap, limit = 4, 5
        # All possible lots for these rows, including rate zero and size zero.
        lots = [(n, r) for r in rates for n in range(cap + 1)]
        packed = {lot: pack(Atom(BOX, lot[0]), Atom(RATE, lot[1])) for lot in lots}
        grouped = defaultdict(list)
        for k in range(limit + 1):
            for receipt in combinations_with_replacement(lots, k):
                table = Shipment()
                for lot in receipt:
                    table = add(table, packed[lot])
                if all(n <= cap for _, n in table.rows):
                    grouped[table, k].append(receipt)
        checked = {False: 0, True: 0}
        for totals in product((None, *range(cap + 1)), repeat=len(rates)):
            table = Shipment(tuple((r, n) for r, n in zip(rates, totals) if n is not None))
            for zeros in (False, True):
                book = BatchReceipts(table, allow_zero=zeros)
                prefix = 0
                for k in range(limit + 1):
                    candidates = grouped[table, k]
                    if not zeros:
                        candidates = [s for s in candidates if all(n > 0 for n, _ in s)]
                    self.assertEqual(book.count(k), len(candidates))
                    tags = set()
                    for receipt in candidates:
                        tag = book.encode(reversed(receipt), k)
                        self.assertEqual(book.decode(tag, k), receipt)
                        self.assertEqual(book.encode(receipt), prefix + tag)
                        self.assertEqual(book.decode(prefix + tag), receipt)
                        tags.add(tag)
                    self.assertEqual(tags, set(range(len(candidates))))
                    checked[zeros] += len(candidates)
                    prefix += len(candidates)
        self.assertEqual(checked, {False: 890, True: 4860})

    def test_multiple_rates_and_known_total(self):
        shipment = Shipment(((3, 4), (5, 3)))
        positive = BatchReceipts(shipment)
        zeros = BatchReceipts(shipment, allow_zero=True)
        self.assertEqual(shipment.screw_count, 27)
        self.assertEqual((positive.count(), positive.fixed_bits()), (15, 4))
        self.assertEqual([positive.count(k) for k in range(8)], [0, 0, 1, 3, 4, 4, 2, 1])
        self.assertEqual((positive.fixed_bits(4), zeros.count(4), zeros.fixed_bits(4)), (2, 13, 4))
        for k in (7, 8, 25, 10**30):
            self.assertEqual(zeros.count(k), 15 * k - 51)
        mixed = BatchReceipts(Shipment(((0, 0), (3, 1), (5, 1))), allow_zero=True)
        for k in (3, 4, 7, 100, 10**30):
            self.assertEqual(mixed.count(k), comb(k - 1, 2))

    def test_zero_size_zero_rate_and_empty_shipment(self):
        for zeros in (False, True):
            empty = BatchReceipts(Shipment(), allow_zero=zeros)
            self.assertEqual((empty.count(), empty.count(0), empty.count(1)), (1, 1, 0))
            self.assertEqual((empty.fixed_bits(), empty.decode(0), empty.encode(())), (0, (), 0))
        announced = Shipment(((7, 0),))
        self.assertEqual(announced.without_empty_rates(), Shipment())
        no_zeros = BatchReceipts(announced)
        self.assertEqual((no_zeros.count(), no_zeros.count(0), no_zeros.count(2)), (0, 0, 0))
        with self.assertRaises(ValueError):
            no_zeros.fixed_bits()
        with self.assertRaises(ValueError):
            no_zeros.decode(0)
        zero_row = BatchReceipts(announced, allow_zero=True)
        self.assertEqual((zero_row.count(), zero_row.fixed_bits(), zero_row.count(0)), (inf, None, 0))
        for k in (1, 2, 7):
            lots = ((0, 7),) * k
            self.assertEqual((zero_row.count(k), zero_row.fixed_bits(k)), (1, 0))
            self.assertEqual((zero_row.decode(k - 1), zero_row.decode(0, k)), (lots, lots))
        for r in (0, 3):
            single = BatchReceipts(Shipment(((r, 4),)), allow_zero=True)
            self.assertEqual([single.count(k) for k in range(6)], [0, 1, 3, 4, 5, 5])
        one_each = BatchReceipts(Shipment(((3, 1), (5, 1))), allow_zero=True)
        for k in (2, 3, 4, 50):
            self.assertEqual(one_each.count(k), k - 1)
            self.assertEqual(one_each.encode(one_each.decode(k - 2, k), k), k - 2)

    def test_large_exact_tags_and_impossible_inputs(self):
        large = BatchReceipts(Shipment(((3, 500),)))
        self.assertGreater(large.count(), 2**64)
        for tag in (0, large.count() // 2, large.count() - 1):
            self.assertEqual(large.encode(large.decode(tag)), tag)
        book = BatchReceipts(Shipment(((3, 4), (5, 3))))
        for k in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                book.count(k)
        for lots, k in [([(4, 3)], None), ([(3, 3), (3, 5)], None),
                        ([(4, 3), (3, 5)], 3), ([(4, 3), (3, 5), (0, 3)], None),
                        ([(4, 3), (3, 8)], None), ([(True, 3), (3, 5)], None)]:
            with self.assertRaises(ValueError):
                book.encode(lots, k)
        for tag, k in [(-1, None), (True, None), (15, None), (4, 4), (0, 20)]:
            with self.assertRaises(ValueError):
                book.decode(tag, k)
        with self.assertRaises(ValueError):
            BatchReceipts(Shipment(), allow_zero=1)

    def test_what_an_additive_square_reading_recovers(self):
        for a, b in combinations_with_replacement(range(15), 2):
            h, squares = a + b, a * a + b * b
            gap = isqrt(2 * squares - h * h)
            self.assertEqual(((h - gap) // 2, (h + gap) // 2), (a, b))
        x, y = (1, 4, 4), (2, 2, 5)
        self.assertEqual(tuple(sum(a**j for a in x) for j in (0, 1, 2)), (3, 9, 33))
        self.assertEqual(tuple(sum(b**j for b in y) for j in (0, 1, 2)), (3, 9, 33))
        book = BatchReceipts(Shipment(((3, 9),)))
        self.assertNotEqual(book.encode([(n, 3) for n in x], 3),
                            book.encode([(n, 3) for n in y], 3))


if __name__ == "__main__":
    unittest.main()
