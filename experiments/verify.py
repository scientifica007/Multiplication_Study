"""Run with python3 experiments/verify.py from the repository root."""

import unittest
from collections import defaultdict
from itertools import product
from math import inf

from history_codes import decode, divisors, encode, history_count
from model import KINDS, PRODUCTS, Atom, Lift, Undefined, add, multiply, reading, unpack
from typed_histories import count_histories


class TypedModelChecks(unittest.TestCase):
    def test_disjoint_domains_and_decoding(self):
        atoms = [Atom(kind, n) for kind in sorted(KINDS) for n in range(4)]
        additions = products = 0
        for a, b in product(atoms, repeat=2):
            same_kind = a.kind == b.kind
            allowed_product = (a.kind, b.kind) in PRODUCTS
            self.assertFalse(same_kind and allowed_product)
            if same_kind:
                self.assertEqual(reading(add(a, b)), (a.kind, a.amount + b.amount))
                additions += 1
            else:
                with self.assertRaises(Undefined):
                    add(a, b)
            if allowed_product:
                result = multiply(a, b)
                self.assertEqual(unpack(result), (a, b))
                self.assertEqual(reading(result), (PRODUCTS[a.kind, b.kind], a.amount * b.amount))
                products += 1
            else:
                with self.assertRaises(Undefined):
                    multiply(a, b)
        self.assertEqual((len(atoms)**2, additions, products), (1936, 176, 96))

    def test_explicit_lift_and_direction(self):
        a, b = Atom("apple", 2), Atom("pear", 2)
        for op in (add, multiply):
            with self.assertRaises(Undefined):
                op(a, b)
        combined = add(Lift(a, "fruit"), Lift(b, "fruit"))
        self.assertEqual(reading(combined), ("fruit", 4))
        self.assertEqual(combined.left.source, a)
        with self.assertRaises(Undefined):
            Lift(Atom("screws_per_box", 2), "thing")
        with self.assertRaises(Undefined):
            multiply(Atom("times", 2), a)
        box, rate = Atom("box", 2), Atom("screws_per_box", 2)
        forward, reverse = multiply(box, rate), multiply(rate, box)
        self.assertEqual(reading(forward), reading(reverse))
        self.assertNotEqual(forward, reverse)
        self.assertEqual(unpack(reverse), (rate, box))

    def test_count_laws_and_parentheses(self):
        for m, n, k in product(range(5), repeat=3):
            a, b = Atom("box", m), Atom("box", k)
            r, s = Atom("screws_per_box", n), Atom("screws_per_box", k)
            self.assertEqual(reading(multiply(add(a, b), r)), reading(add(multiply(a, r), multiply(b, r))))
            self.assertEqual(reading(multiply(a, add(r, s))), reading(add(multiply(a, r), multiply(a, s))))
        a, b, c = Atom("bundle", 2), Atom("boxes_per_bundle", 3), Atom("screws_per_box", 4)
        left, right = multiply(multiply(a, b), c), multiply(a, multiply(b, c))
        self.assertEqual(reading(left), ("screw", 24))
        self.assertEqual(reading(left), reading(right))
        self.assertNotEqual(left, right)
        self.assertEqual(unpack(left), (multiply(a, b), c))
        self.assertEqual(unpack(right), (a, multiply(b, c)))

    def test_identity_and_zero_fibres(self):
        one, two, zero = (Atom("times", n) for n in (1, 2, 0))
        x = Atom("apple", 3)
        y = multiply(x, two)
        after_one = multiply(y, one)
        self.assertEqual(reading(y), reading(after_one))
        self.assertNotEqual(unpack(y), unpack(after_one))
        self.assertEqual((unpack(y), unpack(after_one)), ((x, two), (y, one)))
        units = {y}
        term = y
        for _ in range(20):
            term = multiply(term, one)
            self.assertEqual(reading(term), ("apple", 6))
            units.add(term)
        self.assertEqual(len(units), 21)
        zeros = {multiply(Atom("apple", n), zero) for n in range(65)}
        self.assertEqual(len(zeros), 65)
        self.assertEqual({reading(z) for z in zeros}, {("apple", 0)})
        self.assertEqual({unpack(z)[0].amount for z in zeros}, set(range(65)))
        with self.assertRaises(Undefined):
            unpack(x)


class MemoryChecks(unittest.TestCase):
    def test_single_product(self):
        for n in range(1, 129):
            pairs = [(a, n // a) for a in range(1, n + 1) if n % a == 0]
            self.assertEqual(tuple(a for a, _ in pairs), divisors(n))
            for a, b in pairs:
                result = multiply(Atom("box", a), Atom("screws_per_box", b))
                self.assertEqual(reading(result), ("screw", n))
        self.assertEqual(divisors(12), (1, 2, 3, 4, 6, 12))

    def test_full_code_against_forward_generation(self):
        # Generate by appending factors to a prefix, independently of divisor ranking.
        limit = 128
        sequences = defaultdict(set)

        def extend(amount, steps):
            sequences[amount].add(steps)
            for factor in range(2, limit // amount + 1):
                extend(amount * factor, steps + (factor,))

        extend(1, ())
        for n in range(1, limit + 1):
            actual = sequences[n]
            self.assertEqual(history_count(n), len(actual))
            ranks = set()
            for steps in actual:
                amount, rank = encode(steps)
                self.assertEqual(amount, n)
                self.assertEqual(decode(n, rank), steps)
                ranks.add(rank)
            self.assertEqual(ranks, set(range(len(actual))))
        self.assertEqual(history_count(12), 8)
        self.assertEqual(history_count(24), 20)
        for k in range(1, 13):
            self.assertEqual(history_count(2**k), 2**(k-1))

    def test_boundaries(self):
        self.assertEqual(encode(()), (1, 0))
        self.assertEqual(decode(1, 0), ())
        for steps in ((0,), (1,), (-3,), (2, 1), (2.5,)):
            with self.assertRaises(ValueError):
                encode(steps)
        for n, rank in ((0, 0), (-1, 0), (1, 1), (12, -1), (12, 8)):
            with self.assertRaises(ValueError):
                decode(n, rank)


class TypedHistoryChecks(unittest.TestCase):
    def test_three_packing_histories(self):
        leaves = {("bundle", 2), ("boxes_per_bundle", 3), ("screws_per_box", 4)}
        # Enumerate complete expressions independently. No tree from these
        # inputs can have height > 2 under the packaging rules.
        terms = {Atom(kind, n) for kind, n in leaves}
        for _ in range(2):
            terms |= {multiply(a, b) for a, b in product(terms, repeat=2)
                      if (a.kind, b.kind) in PRODUCTS}
        for kind in KINDS:
            for n in range(1, 25):
                direct = sum(reading(t) == (kind, n) for t in terms)
                self.assertEqual(count_histories((kind, n), leaves, PRODUCTS), direct)
        self.assertEqual(count_histories(("screw", 24), leaves, PRODUCTS), 3)
        one_way = dict(PRODUCTS)
        del one_way["screws_per_box", "box"]
        self.assertEqual(count_histories(("screw", 24), leaves, one_way), 2)

    def test_cycles_need_reachability_and_productive_siblings(self):
        seeds = {("apple", 3), ("times", 2)}
        self.assertEqual(count_histories(("apple", 6), seeds, PRODUCTS), 1)
        self.assertEqual(count_histories(("apple", 6), seeds | {("times", 1)}, PRODUCTS), inf)
        self.assertEqual(count_histories(("apple", 6), {("times", 1)}, PRODUCTS), 0)
        packing = {("bundle", 2), ("boxes_per_bundle", 3), ("screws_per_box", 4)}
        self.assertEqual(count_histories(("screw", 24), packing | seeds | {("times", 1)}, PRODUCTS), 3)
        cycle = {("A", "U"): "B", ("B", "V"): "A"}
        self.assertEqual(count_histories(("A", 5), {("A", 5), ("U", 1)}, cycle), 1)
        self.assertEqual(count_histories(("A", 5), {("A", 5), ("U", 1), ("V", 1)}, cycle), inf)
        self.assertEqual(count_histories(("A", 0), set(), cycle), 0)

    def test_chain_is_a_special_case(self):
        for n in range(1, 129):
            leaves = {("apple", 1)} | {("times", d) for d in divisors(n) if d >= 2}
            self.assertEqual(count_histories(("apple", n), leaves, PRODUCTS), history_count(n))


def load_tests(loader, tests, pattern):
    tests.addTests(loader.loadTestsFromName("test_zero_histories"))
    tests.addTests(loader.loadTestsFromName("test_square_extension"))
    return tests


if __name__ == "__main__":
    unittest.main(verbosity=2)
