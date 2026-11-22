"""Independent finite tests of real nested typed products and context quotients."""
import unittest
from itertools import product
from math import ceil, log2
from two_stage_typed_products import (
    Atom, A_LABELS, B_VALUES, operand_a, operand_b, operand_d, operand_f,
    multiply, unpack, products, positive_products, context_signature,
    flat_context_signature, all_context_words, classes, observation,
    measure_factors_through,
)

class TwoStageTypedProductTests(unittest.TestCase):
    def test_full_primary_provenance_and_all_sign_patterns(self):
        all_c=products()
        self.assertEqual(len(all_c),36)
        self.assertEqual(len(set(all_c)),36)
        for a,b in product(A_LABELS,B_VALUES):
            c=multiply(operand_a(a),operand_b(b))
            self.assertEqual((c.sort,c.amount),('C',a*b))
            self.assertEqual(unpack(c),(operand_a(a),operand_b(b)))
        x=multiply(operand_a(1),operand_b(6))
        y=multiply(operand_a(-1),operand_b(-6))
        self.assertEqual(x.amount,y.amount)
        self.assertNotEqual(x,y)
        self.assertNotEqual(unpack(x),unpack(y))

    def test_primary_same_measure_but_different_next_legality(self):
        x=multiply(operand_a(1),operand_b(6))
        y=multiply(operand_a(2),operand_b(3))
        z=multiply(operand_a(3),operand_b(2))
        self.assertEqual({x.amount,y.amount,z.amount},{6})
        self.assertIsNotNone(multiply(x,operand_d('seal')))
        self.assertIsNone(multiply(y,operand_d('seal')))
        self.assertIsNotNone(multiply(z,operand_d('seal')))
        self.assertIsNone(multiply(x,operand_d('inspect')))
        self.assertIsNotNone(multiply(y,operand_d('inspect')))
        self.assertIsNone(multiply(z,operand_d('inspect')))

    def test_nested_unpacking_and_two_stage_numerical_reading(self):
        for c in products():
            for mode in ('seal','inspect'):
                e=multiply(c,operand_d(mode))
                allowed=(c.right.label%2==0) if mode=='seal' else (c.left.label%2==0)
                self.assertEqual(e is not None,allowed)
                if e is None:continue
                self.assertEqual(unpack(e),(c,operand_d(mode)))
                self.assertEqual(e.amount,c.amount*operand_d(mode).amount)
                self.assertEqual(unpack(unpack(e)[0]),(c.left,c.right))
                g=multiply(e,operand_f())
                permit=mode=='seal' and c.left.label==1
                self.assertEqual(g is not None,permit)
                if permit:
                    self.assertEqual(g.amount,e.amount*5)
                    self.assertEqual(unpack(g),(e,operand_f()))
                    self.assertEqual(unpack(unpack(g)[0]),(c,operand_d(mode)))

    def test_types_direction_and_no_fake_zero(self):
        a=operand_a(1); b=operand_b(6);d=operand_d('seal');f=operand_f()
        c=multiply(a,b)
        for x,y in ((b,a),(a,a),(b,b),(c,b),(c,a),(c,f),(d,c),(a,d)):
            self.assertIsNone(multiply(x,y))
        self.assertIsNone(multiply(c,Atom('D','seal',999)))
        with self.assertRaises(ValueError):unpack(a)
        with self.assertRaises(ValueError):context_signature(c,-1)

    def test_exact_partition_counts_positive_and_signed(self):
        self.assertEqual([len(classes(k,positive_products())) for k in range(4)],[7,8,9,9])
        self.assertEqual([len(classes(k)) for k in range(4)],[14,16,20,20])
        self.assertTrue(measure_factors_through(0))
        self.assertFalse(measure_factors_through(1))
        self.assertFalse(measure_factors_through(2))
        self.assertEqual((ceil(log2(7)),ceil(log2(9))),(3,4))

    def test_one_step_indistinguishable_but_two_step_distinct(self):
        x=multiply(operand_a(1),operand_b(6))
        z=multiply(operand_a(3),operand_b(2))
        self.assertEqual(context_signature(x,0),context_signature(z,0))
        self.assertEqual(context_signature(x,1),context_signature(z,1))
        self.assertNotEqual(context_signature(x,2),context_signature(z,2))
        ex=multiply(x,operand_d('seal'))
        ez=multiply(z,operand_d('seal'))
        self.assertEqual(observation(ex),observation(ez))
        self.assertIsNotNone(multiply(ex,operand_f()))
        self.assertIsNone(multiply(ez,operand_f()))

    def test_flat_context_traces_agree_with_recursive_equivalence(self):
        receipts=products()
        for depth in (0,1,2,3):
            for x in receipts:
                for y in receipts:
                    self.assertEqual(context_signature(x,depth)==context_signature(y,depth),
                                     flat_context_signature(x,depth)==flat_context_signature(y,depth),
                                     (depth,x.left.label,x.right.label,y.left.label,y.right.label))
        self.assertEqual([len(all_context_words(k)) for k in (0,1,2,3)],[1,3,5,5])

    def test_partition_refines_monotonically(self):
        receipts=products()
        for x in receipts:
            for y in receipts:
                if context_signature(x,2)==context_signature(y,2):
                    self.assertEqual(context_signature(x,1),context_signature(y,1))
                if context_signature(x,1)==context_signature(y,1):
                    self.assertEqual(context_signature(x,0),context_signature(y,0))

    def test_unobservable_full_history_not_equated_with_record_equality(self):
        receipts=products()
        self.assertLess(len(classes(2)),len(receipts))
        pairs=[(x,y) for i,x in enumerate(receipts) for y in receipts[i+1:]
               if context_signature(x,2)==context_signature(y,2)]
        self.assertTrue(pairs)
        self.assertTrue(all(x!=y and unpack(x)!=unpack(y) for x,y in pairs))

if __name__=='__main__':
    unittest.main()
