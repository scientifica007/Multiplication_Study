"""Finite computational witnesses for the independent signed-provenance study."""
import unittest
from itertools import product
from math import ceil, log2

from signed_provenance import (
    Atom, aggregate_fiber_size, basis, formal_add, formal_measure,
    formal_neg, measure, multiply, one_sided_multiply,
    one_sided_unpack, signed_factor_pairs, typed_add, unpack,
)


class SignedProvenanceChecks(unittest.TestCase):
    def test_four_unit_sign_receipts(self):
        records = [multiply(Atom('A', a), Atom('B', b))
                   for a, b in product((-1, 1), repeat=2)]
        self.assertEqual(len(set(records)), 4)
        self.assertEqual(sorted(map(measure, records)), [-1, -1, 1, 1])
        self.assertEqual({unpack(r) for r in records},
                         {(Atom('A', a), Atom('B', b))
                          for a, b in product((-1, 1), repeat=2)})
        with self.assertRaises(ValueError):
            typed_add(Atom('A', 1), Atom('B', 1))
        with self.assertRaises(ValueError):
            multiply(Atom('B', 1), Atom('A', 1))
        with self.assertRaises(ValueError):
            multiply(Atom('A', 1), Atom('A', 1))

    def test_negative_of_receipt_is_not_negative_inputs(self):
        pp = multiply(Atom('A', 1), Atom('B', 1))
        mm = multiply(Atom('A', -1), Atom('B', -1))
        self.assertNotEqual(basis(mm), basis(pp))
        self.assertNotEqual(basis(mm), formal_neg(basis(pp)))
        self.assertEqual(formal_measure(basis(pp)), 1)
        self.assertEqual(formal_measure(basis(mm)), 1)
        self.assertEqual(formal_measure(formal_neg(basis(pp))), -1)
        self.assertEqual(formal_add(basis(pp), formal_neg(basis(pp))), {})

    def test_signed_factor_fibers_exhaustively(self):
        for p in list(range(-200, 0)) + list(range(1, 201)):
            actual = signed_factor_pairs(p)
            self.assertEqual(len(actual), 2 * sum(abs(p) % d == 0
                                                  for d in range(1, abs(p) + 1)))
            self.assertEqual(len(set(actual)), len(actual))
            self.assertTrue(all(a * b == p for a, b in actual))
        self.assertEqual(len(signed_factor_pairs(12)), 12)
        self.assertEqual(ceil(log2(len(signed_factor_pairs(12)))), 4)
        with self.assertRaises(ValueError):
            signed_factor_pairs(0)

    def test_aggregated_four_signs_fibers(self):
        for k in range(0, 19):
            counts = {}
            for a in range(k + 1):
                for b in range(k - a + 1):
                    for c in range(k - a - b + 1):
                        d = k - a - b - c
                        observed = a - b - c + d
                        counts[observed] = counts.get(observed, 0) + 1
            for observed in range(-k - 1, k + 2):
                self.assertEqual(counts.get(observed, 0),
                                 aggregate_fiber_size(k, observed), (k, observed))
        self.assertEqual(aggregate_fiber_size(2, 0), 4)
        self.assertEqual(aggregate_fiber_size(2, 2), 3)

    def test_one_sided_additivity_and_recovery(self):
        for a in range(-5, 6):
            for n in range(-5, 6):
                if not n:
                    continue
                output = one_sided_multiply(Atom('A', a), Atom('B', n))
                self.assertEqual(one_sided_unpack(output),
                                 (Atom('A', a), Atom('B', n)))
                self.assertEqual(sum(k*v for k,v in output.items()), a*n)
            for n1 in range(-5, 6):
                for n2 in range(-5, 6):
                    if not n1 or not n2 or n1 + n2 == 0:
                        continue
                    left = one_sided_multiply(Atom('A', a), Atom('B', n1+n2))
                    right = formal_add(
                        one_sided_multiply(Atom('A', a), Atom('B', n1)),
                        one_sided_multiply(Atom('A', a), Atom('B', n2)),
                    )
                    self.assertEqual(left, right)
        self.assertNotEqual(one_sided_multiply(Atom('A', 2), Atom('B', 1)),
                            {1: 2})
        with self.assertRaises(ValueError):
            one_sided_multiply(Atom('A', 1), Atom('B', 0))


if __name__ == '__main__':
    unittest.main()
