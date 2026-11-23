"""Ground operational equality claims against an independent context enumerator."""
import unittest
from itertools import product
from equality_levels import (
    Atom, FirstReceipt, CQuantity, PROBES, first_product, atomic, quantity,
    add_c, sources, source_class, merge_classes, summary, add_summaries,
    second_product, public_test, direct_signature, probe_after_add,
    unpack_product, all_atoms, finite_histories, quotient_is_safe_on_sample,
)


class EqualityLevelsTests(unittest.TestCase):
    def test_01_initial_products_are_full_unambiguous_records(self):
        atoms = all_atoms()
        self.assertEqual(len(atoms), 16)
        self.assertEqual(len(set(atoms)), 16)
        for x in atoms:
            self.assertEqual(unpack_product(x.terms[0]),
                             (x.terms[0].left, x.terms[0].right))
        with self.assertRaises(TypeError):
            first_product(Atom('B', 2), Atom('A', 1))

    def test_02_three_equalities_are_properly_nested(self):
        x, y, z = atomic(-1, -2), atomic(1, 2), atomic(1, 2)
        self.assertEqual(x.amount, y.amount)
        self.assertNotEqual(x, y)
        self.assertNotEqual(summary(x), summary(y))
        c = add_c(atomic(1, 2), atomic(1, -2))
        d = add_c(c, c)
        self.assertNotEqual(c, d)
        self.assertEqual(summary(c), summary(d))

    def test_03_direct_equivalence_fails_in_additive_context(self):
        x, y, z = atomic(-1, -2), atomic(1, 2), atomic(1, 2)
        self.assertEqual(direct_signature(x), direct_signature(y))
        self.assertEqual(add_c(x, z).amount, add_c(y, z).amount)
        self.assertNotEqual(probe_after_add(x, z), probe_after_add(y, z))
        self.assertEqual(public_test(add_c(x, z), PROBES[0])[0], False)
        self.assertEqual(public_test(add_c(y, z), PROBES[0])[0], True)

    def test_04_same_left_source_but_different_right_source(self):
        x, y, z = atomic(1, -2), atomic(1, 2), atomic(-1, 2)
        self.assertEqual(sources(x, 'A'), sources(y, 'A'))
        self.assertNotEqual(sources(x, 'B'), sources(y, 'B'))
        # To avoid a measurement difference, use opposite-value sums.
        p = add_c(atomic(1, -2), atomic(1, 2))
        q = add_c(atomic(-1, -2), atomic(-1, 2))
        self.assertEqual(p.amount, q.amount)
        self.assertEqual(source_class(sources(p, 'B')), ('mixed',))
        self.assertEqual(source_class(sources(q, 'B')), ('mixed',))
        self.assertNotEqual(summary(p), summary(q))
        self.assertNotEqual(probe_after_add(p, atomic(1, 2)),
                            probe_after_add(q, atomic(1, 2)))

    def test_05_summary_is_a_commutative_monoid_homomorphism(self):
        elems = (quantity(), atomic(1, 2), atomic(-1, -2),
                 atomic(2, 3), atomic(1, -2))
        for x, y, z in product(elems, repeat=3):
            self.assertEqual(add_c(x, y), add_c(y, x))
            self.assertEqual(add_c(add_c(x, y), z), add_c(x, add_c(y, z)))
            self.assertEqual(summary(add_c(x, y)), add_summaries(summary(x), summary(y)))
            self.assertEqual(summary(add_c(add_c(x, y), z)),
                             add_summaries(add_summaries(summary(x),summary(y)),summary(z)))

    def test_06_16_atomic_records_vs_8_numerical_values(self):
        atoms = all_atoms()
        self.assertEqual(len({x.amount for x in atoms}), 8)
        self.assertEqual(len({direct_signature(x) for x in atoms}), 8)
        self.assertEqual(len({summary(x) for x in atoms}), 16)

    def test_07_minimality_over_84_histories_with_one_atom_contexts(self):
        selected = tuple(v.terms[0] for v in (
            atomic(-1, -2), atomic(-1, 2), atomic(1, -2),
            atomic(1, 2), atomic(2, -3), atomic(2, 3)))
        histories = finite_histories(selected, 3)
        self.assertEqual(len(histories), 84)
        probes = (quantity(),) + all_atoms()
        observed = {
            x: tuple(probe_after_add(x, z) for z in probes)
            for x in histories
        }
        for x, y in product(histories, repeat=2):
            self.assertEqual(summary(x) == summary(y), observed[x] == observed[y],
                             (x, y))

    def test_08_tagged_zero_and_empty_sum_differ_operationally(self):
        z = add_c(atomic(1, 2), atomic(1, -2))
        empty = quantity()
        self.assertEqual(z.amount, empty.amount)
        self.assertNotEqual(summary(z), summary(empty))
        self.assertTrue(public_test(z, PROBES[0])[0])
        self.assertFalse(public_test(empty, PROBES[0])[0])

    def test_09_full_unpack_after_a_legal_probe_defeats_observational_quotient(self):
        x = add_c(atomic(1, 2), atomic(1, -2))
        y = add_c(x, x)
        self.assertEqual(summary(x),summary(y))
        self.assertNotEqual(x,y)
        p1=second_product(x,PROBES[0])
        p2=second_product(y,PROBES[0])
        self.assertEqual(p1.amount,p2.amount)
        self.assertNotEqual(p1,p2)
        self.assertEqual(unpack_product(p1),(x,PROBES[0]))
        self.assertEqual(unpack_product(p2),(y,PROBES[0]))

    def test_10_kernel_factorization_rejects_measurement_and_direct_guard(self):
        values=all_atoms()+(
            add_c(atomic(-1,-2),atomic(1,2)),
            add_c(atomic(1,2),atomic(1,2)),
        )
        ops = tuple((p.name,
                     lambda x, p=p: public_test(x,p)[0],
                     lambda x, p=p: public_test(x,p)[1]) for p in PROBES)
        self.assertFalse(quotient_is_safe_on_sample(values,lambda x:x.amount,ops))
        self.assertTrue(quotient_is_safe_on_sample(values,summary,ops))

    def test_11_new_count_guard_invalidates_old_minimal_summary(self):
        x=add_c(atomic(1,2),atomic(1,-2))
        y=add_c(x,x)
        self.assertEqual(summary(x),summary(y))
        self.assertTrue(len(x.terms)<=2)
        self.assertFalse(len(y.terms)<=2)
        # The old summary was minimal only for the old declared observation language.

    def test_12_exhaustive_direct_vs_context_distinguishers(self):
        selected = tuple(v.terms[0] for v in (
            atomic(-1,-2), atomic(-1,2), atomic(1,-2),
            atomic(1,2), atomic(2,-3), atomic(2,3)))
        histories=finite_histories(selected,3)
        self.assertLess(len({direct_signature(x) for x in histories}),
                        len({summary(x) for x in histories}))
        self.assertLess(len({summary(x) for x in histories}),len(histories))


if __name__ == '__main__':
    unittest.main()
