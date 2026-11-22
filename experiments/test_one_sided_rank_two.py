"""Independent bounded checks; general claims require separate proofs."""
import unittest
from itertools import product
from signed_provenance import Atom
from one_sided_rank_two import Output, multiply, unpack, output_measure, left_defect, proportional_vectors, multiply_with_zero, unpack_with_zero, compress_free_receipts, kernel_relation, canonical_free_representative


class RankTwoWitnessTests(unittest.TestCase):
    def test_typed_domain_and_zero_exclusion(self):
        with self.assertRaises(ValueError):
            multiply(Atom('A', 0), Atom('B', 0))
        with self.assertRaises(ValueError):
            multiply(Atom('B', 1), Atom('A', 1))
        with self.assertRaises(ValueError):
            multiply(Atom('A', 2), Atom('A', 3))

    def test_complete_inverse_and_measure(self):
        self.assertEqual(unpack(Output(1, -5)), (Atom('A', -5), Atom('B', 1)))
        for a, n in product(range(-30, 31), range(-30, 31)):
            if n == 0:
                continue
            receipt = multiply(Atom('A', a), Atom('B', n))
            self.assertEqual(unpack(receipt), (Atom('A', a), Atom('B', n)))
            self.assertEqual(output_measure(receipt), a * n)
        with self.assertRaises(ValueError):
            unpack(Output(0, 0))
        with self.assertRaises(ValueError):
            unpack(Output(2, 3))

    def test_signs_are_distinct(self):
        r = [multiply(Atom('A', a), Atom('B', n))
             for a, n in product((-1, 1), repeat=2)]
        self.assertEqual(len(set(r)), 4)
        self.assertEqual(sorted(output_measure(x) for x in r), [-1, -1, 1, 1])
        self.assertNotEqual(multiply(Atom('A', 1), Atom('B', 1)),
                            multiply(Atom('A', -1), Atom('B', -1)))

    def test_partial_right_distribution_and_left_defect(self):
        for a, m, n in product(range(-8, 9), repeat=3):
            if m and n and m + n:
                left = multiply(Atom('A', a), Atom('B', m + n))
                right = (multiply(Atom('A', a), Atom('B', m))
                         + multiply(Atom('A', a), Atom('B', n)))
                self.assertEqual(left, right)
        for a, b, n in product(range(-5, 6), repeat=3):
            if n:
                self.assertEqual(left_defect(a, b, n), Output(-n, 0))

    def test_cancellations_and_sum_history_collisions(self):
        for a, n in product(range(-5, 6), repeat=2):
            if n:
                self.assertEqual(multiply(Atom('A', a), Atom('B', n))
                                 + multiply(Atom('A', a), Atom('B', -n)),
                                 Output(0, 0))
        r = lambda a: multiply(Atom('A', a), Atom('B', 1))
        self.assertEqual(r(1) + r(3), r(0) + r(4))
        self.assertEqual(r(1) + r(3), multiply(Atom('A', 2), Atom('B', 2)))

    def test_full_zero_extension_with_distributivity_exception(self):
        seen = set()
        for a, n in product(range(-15, 16), repeat=2):
            receipt = multiply_with_zero(Atom('A', a), Atom('B', n))
            self.assertNotIn(receipt, seen)
            seen.add(receipt)
            self.assertEqual(unpack_with_zero(receipt),
                             (Atom('A', a), Atom('B', n)))
            self.assertEqual(output_measure(receipt), a*n)
        for a, m, n in product(range(-4, 5), repeat=3):
            if m and n and m+n:
                self.assertEqual(multiply_with_zero(Atom('A', a), Atom('B', m+n)),
                                 multiply_with_zero(Atom('A', a), Atom('B', m)) +
                                 multiply_with_zero(Atom('A', a), Atom('B', n)))
        for a in range(-4,5):
            self.assertNotEqual(multiply_with_zero(Atom('A', a), Atom('B', 0)),
                                Output(0,0))
            self.assertNotEqual(multiply_with_zero(Atom('A', a), Atom('B', 1)) +
                                multiply_with_zero(Atom('A', a), Atom('B', -1)),
                                multiply_with_zero(Atom('A', a), Atom('B', 0)))
        with self.assertRaises(ValueError):
            unpack_with_zero(Output(0,0))
        with self.assertRaises(ValueError):
            unpack_with_zero(Output(3,2))

    def test_universal_compression_kernel_basis(self):
        for a in range(-30,31):
            if a in (0,1):
                continue
            relation = kernel_relation(a)
            self.assertEqual(compress_free_receipts(relation), Output(0,0))
        sample = {a: ((a*a + 3*a + 1) % 7) - 3 for a in range(-5,6)}
        r = canonical_free_representative(sample)
        self.assertEqual(compress_free_receipts(sample),
                         compress_free_receipts(r))
        self.assertEqual(compress_free_receipts({0:1,2:1}),
                         compress_free_receipts({1:2}))
        self.assertEqual(compress_free_receipts({0:1}), Output(1,0))
        self.assertEqual(compress_free_receipts({1:1}), Output(1,1))

    def test_rational_slope_separation(self):
        for a, b in product(range(-8, 9), repeat=2):
            self.assertEqual(proportional_vectors((1, a), (1, b)), a == b)
        # A single output coordinate of the form n*a would confound 1*6 and 2*3.
        self.assertEqual(1 * 6, 2 * 3)
        self.assertNotEqual(Output(1, 6), Output(2, 6))


if __name__ == '__main__':
    unittest.main()
