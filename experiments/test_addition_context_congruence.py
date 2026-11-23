"""Exhaustive finite model checks and a structural distributivity counterexample."""
import unittest
from itertools import product
from addition_context_congruence import (
    A_LABELS, B_LABELS, CValue, Atom, atom_a, atom_b, atom_d, first_product,
    unpack_product, quantity, atomic, add_c, support, batch_product, add_e,
    direct_signature, support_kind, merge_kinds, sufficient_summary,
    add_summaries, finite_histories, universe,
)

class ContextAdditionTests(unittest.TestCase):
    def test_complete_primary_product_receipts(self):
        nodes = universe()
        self.assertEqual(len(nodes), 36)
        self.assertEqual(len(set(nodes)), 36)
        for a, b in product(A_LABELS,B_LABELS):
            p = first_product(atom_a(a), atom_b(b))
            self.assertEqual(unpack_product(p), (atom_a(a),atom_b(b)))
            self.assertEqual(atomic(a,b).amount, a*b)
        self.assertNotEqual(atomic(3,2), atomic(-3,-2))
        self.assertEqual(atomic(3,2).amount, atomic(-3,-2).amount)

    def test_substitution_fails_after_addition(self):
        x,y,z = atomic(3,2), atomic(-3,-2), atomic(3,2)
        self.assertEqual(direct_signature(x),direct_signature(y))
        self.assertEqual(add_c(x,z).amount,add_c(y,z).amount)
        self.assertIsNotNone(batch_product(add_c(x,z),atom_d()))
        self.assertIsNone(batch_product(add_c(y,z),atom_d()))
        self.assertNotEqual(direct_signature(add_c(x,z)),direct_signature(add_c(y,z)))

    def test_monoid_laws_and_summary_homomorphism(self):
        sample=(quantity(), atomic(3,2),atomic(-3,-2),atomic(1,6),atomic(2,-3))
        empty=quantity()
        for x,y,z in product(sample,repeat=3):
            self.assertEqual(add_c(x,empty),x)
            self.assertEqual(add_c(x,y),add_c(y,x))
            self.assertEqual(add_c(add_c(x,y),z),add_c(x,add_c(y,z)))
            self.assertEqual(sufficient_summary(add_c(x,y)),
                             add_summaries(sufficient_summary(x),sufficient_summary(y)))

    def test_exact_unbounded_context_characterization_finite_checks(self):
        gens=tuple(atomic(a,b).terms[0] for a,b in product((-3,3,2),(2,-2)))
        histories=finite_histories(gens,3)
        self.assertEqual(len(histories),84)  # 1+6+21+56
        tests=(quantity(),)+tuple(quantity(g) for g in gens)
        for x,y in product(histories,repeat=2):
            expected=sufficient_summary(x)==sufficient_summary(y)
            actual=all(direct_signature(add_c(x,z))==direct_signature(add_c(y,z))
                       for z in tests)
            self.assertEqual(actual,expected,(x,y))

    def test_atomic_36_separate_under_additive_contexts(self):
        nodes=universe()
        self.assertEqual(len({direct_signature(c) for c in nodes}),14)
        self.assertEqual(len({sufficient_summary(c) for c in nodes}),36)
        positive=tuple(c for c in nodes if c.terms[0].left.label>0 and c.terms[0].right.label>0)
        self.assertEqual(len(positive),9)
        self.assertEqual(len({direct_signature(c) for c in positive}),7)
        self.assertEqual(len({sufficient_summary(c) for c in positive}),9)

    def test_missing_distributivity_with_mixed_support(self):
        x,y=atomic(3,2),atomic(-3,-2)
        self.assertIsNone(batch_product(add_c(x,y),atom_d()))
        u,v=batch_product(x,atom_d()),batch_product(y,atom_d())
        self.assertIsNotNone(u)
        self.assertIsNotNone(v)
        self.assertEqual(add_e(u,v).amount,2*(x.amount+y.amount))

    def test_numeric_distributivity_but_structural_inequality(self):
        x,y=atomic(3,2),atomic(3,-2)
        lhs=batch_product(add_c(x,y),atom_d())
        rhs=add_e(batch_product(x,atom_d()),batch_product(y,atom_d()))
        self.assertEqual(lhs.amount,rhs.amount)
        self.assertEqual(lhs.amount,0)
        self.assertNotEqual(lhs,rhs)
        self.assertEqual(unpack_product(lhs),(add_c(x,y),atom_d()))
        self.assertEqual(len(rhs.terms),2)

    def test_empty_and_cancelled_zero_differ(self):
        empty=quantity()
        zero=add_c(atomic(3,2),atomic(3,-2))
        self.assertEqual(empty.amount,zero.amount)
        self.assertEqual(support_kind(empty),('empty',))
        self.assertEqual(support_kind(zero),('single',3))
        self.assertIsNone(batch_product(empty,atom_d()))
        self.assertIsNotNone(batch_product(zero,atom_d()))
        self.assertNotEqual(sufficient_summary(empty),sufficient_summary(zero))

    def test_mixed_histories_same_measure_and_different_provenance(self):
        x=add_c(atomic(3,2),atomic(-3,-2))
        y=add_c(atomic(3,-2),atomic(-3,2))
        self.assertEqual(support_kind(x),support_kind(y))
        self.assertEqual(x.amount,12)
        self.assertEqual(y.amount,-12)
        self.assertNotEqual(sufficient_summary(x),sufficient_summary(y))
        z=add_c(atomic(2,3),atomic(-2,-3))
        self.assertEqual(x.amount,z.amount)
        self.assertEqual(sufficient_summary(x),sufficient_summary(z))
        self.assertNotEqual(x,z)

    def test_invalid_type_operations_and_provenance(self):
        a,b=atom_a(3),atom_b(2)
        self.assertIsNone(first_product(b,a))
        with self.assertRaises(TypeError): add_c(atomic(3,2),a)
        with self.assertRaises(ValueError): unpack_product(quantity())
        self.assertIsNone(batch_product(quantity(),atom_d()))
        self.assertIsNone(batch_product(atomic(3,2),a))

if __name__=='__main__':
    unittest.main()
