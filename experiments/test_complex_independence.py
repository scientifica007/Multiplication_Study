"""Exact finite tests of two infinite algebra constructions, not finite proofs of field nonexistence."""
import unittest
from fractions import Fraction
from itertools import product
from complex_independence import (
    GaussQ, ScalarField, NativeTypedModel, ZERO,ONE,MINUS_ONE,I,
    CQuantity, Receipt, signed_receipts,
)


class ModelIndependenceTests(unittest.TestCase):
    def setUp(self):
        self.models={name:NativeTypedModel(ScalarField(name)) for name in ('Q','Qi')}

    def test_01_fields_are_distinct_and_root_requires_extension(self):
        self.assertIsNone(self.models['Q'].field.root_of_minus_one())
        self.assertFalse(self.models['Q'].field.member(I))
        self.assertEqual(self.models['Qi'].field.root_of_minus_one(),I)
        self.assertEqual(I*I,MINUS_ONE)
        self.assertTrue(self.models['Qi'].field.member(I))

    def test_02_exact_gaussian_rational_field_operations(self):
        numbers=(ZERO,ONE,MINUS_ONE,I,-I,GaussQ(Fraction(2,3),Fraction(-3,5)))
        for x,y,z in product(numbers,repeat=3):
            self.assertEqual((x+y)+z,x+(y+z))
            self.assertEqual((x*y)*z,x*(y*z))
            self.assertEqual(x*(y+z),x*y+x*z)
        for x in numbers:
            self.assertEqual(x+(-x),ZERO)
            if x!=ZERO:self.assertEqual(x*x.inverse(),ONE)
        with self.assertRaises(ZeroDivisionError):ZERO.inverse()

    def test_03_native_product_only_differently_typed_a_then_b(self):
        for m in self.models.values():
            a=m.factor('A',ONE);b=m.factor('B',ONE)
            self.assertIsNotNone(m.star(a,b))
            self.assertIsNone(m.star(b,a))
            self.assertIsNone(m.star(a,a))
            self.assertIsNone(m.star(b,b))
            self.assertIsNone(m.star(m.star(a,b),m.star(a,b)))

    def test_04_same_sort_addition_but_no_cross_type_addition(self):
        for m in self.models.values():
            a=m.factor('A',ONE);a2=m.factor('A',GaussQ(2))
            b=m.factor('B',ONE)
            self.assertEqual(m.add(a,a2),m.factor('A',GaussQ(3)))
            self.assertIsNone(m.add(a,b))
            self.assertIsNone(m.add(b,a))
            self.assertIsNone(m.add(a,m.star(a,b)))
            self.assertIsNone(m.star(a,a2))

    def test_05_all_four_signed_pairs_are_preserved(self):
        for m in self.models.values():
            records=signed_receipts(m)
            self.assertEqual(len(set(records)),4)
            self.assertEqual([m.read(x) for x in records],
                             [ONE,MINUS_ONE,MINUS_ONE,ONE])
            self.assertNotEqual(records[0],records[3])
            self.assertNotEqual(records[1],records[2])
            for x in records:self.assertEqual(m.star(*m.unpack(x)),x)

    def test_06_c_sum_retains_multiset_receipts_and_zero_measurement(self):
        for m in self.models.values():
            records=signed_receipts(m)
            full=m.add(records[0],records[1])
            self.assertIsInstance(full,CQuantity)
            self.assertEqual(m.read(full),ZERO)
            self.assertNotEqual(full,m.empty_c())
            self.assertIsNone(m.unpack(full))
            self.assertEqual(len(full.terms),2)
            self.assertEqual(m.add(m.empty_c(),records[0]),records[0])
            self.assertEqual(m.add(records[0],records[1]),m.add(records[1],records[0]))

    def test_07_complex_field_i_can_be_used_in_distinct_native_types(self):
        m=self.models['Qi']
        ai=m.factor('A',I);bi=m.factor('B',I)
        receipt=m.star(ai,bi)
        self.assertEqual(m.unpack(receipt),(ai,bi))
        self.assertEqual(m.read(receipt),MINUS_ONE)
        self.assertIsNone(m.star(ai,ai))
        self.assertIsNone(m.star(bi,bi))
        self.assertNotEqual(receipt,m.star(m.factor('A',MINUS_ONE),m.factor('B',ONE)))

    def test_08_rational_field_rejects_i_as_a_factor(self):
        m=self.models['Q']
        with self.assertRaises(ValueError):m.factor('A',I)
        with self.assertRaises(ValueError):m.factor('B',I)
        with self.assertRaises(ValueError):m.scalar_multiply(I,I)
        self.assertIsNone(m.field.root_of_minus_one())

    def test_09_numeric_distributivity_not_full_receipt_distributivity(self):
        for m in self.models.values():
            a=m.factor('A',ONE);aa=m.factor('A',GaussQ(2));b=m.factor('B',GaussQ(3))
            single=m.star(m.add(a,aa),b)
            distributed=m.add(m.star(a,b),m.star(aa,b))
            self.assertEqual(m.read(single),m.read(distributed))
            self.assertNotEqual(single,distributed)
            self.assertIsNotNone(m.unpack(single))
            self.assertIsNone(m.unpack(distributed))
            for x,y,z in product((-2,-1,1,2),repeat=3):
                a=m.factor('A',GaussQ(x));a2=m.factor('A',GaussQ(y));b=m.factor('B',GaussQ(z))
                self.assertEqual(m.read(m.star(m.add(a,a2),b)),
                                 m.read(m.add(m.star(a,b),m.star(a2,b))))

    def test_10_exact_fractional_readings_in_both_models(self):
        for m in self.models.values():
            a=m.factor('A',GaussQ(Fraction(2,3)))
            b=m.factor('B',GaussQ(Fraction(-3,4)))
            record=m.star(a,b)
            self.assertEqual(m.read(record),GaussQ(Fraction(-1,2)))
            self.assertEqual(m.unpack(record),(a,b))

    def test_11_complex_product_is_not_the_classical_square_in_native_sort(self):
        m=self.models['Qi']
        a=m.factor('A',I);b=m.factor('B',I)
        self.assertEqual(m.scalar_multiply(I,I),MINUS_ONE)
        self.assertEqual(m.read(m.star(a,b)),MINUS_ONE)
        self.assertIsNone(m.star(a,a))
        self.assertNotEqual(a,b)

    def test_12_rat_field_rational_samples_have_no_negative_squares(self):
        for p,q in product(range(-6,7),range(1,7)):
            r=GaussQ(Fraction(p,q))
            self.assertNotEqual(r*r,MINUS_ONE)
        # General impossibility is proven algebraically, not by this finite sample.

    def test_13_injectivity_exact_for_sampled_scalar_pairs(self):
        for m in self.models.values():
            elements=[GaussQ(n) for n in range(-3,4)]
            if m.field.name=='Qi':elements += [I,-I,GaussQ(Fraction(1,2),Fraction(3,4))]
            records=set()
            for x,y in product(elements,repeat=2):
                left=m.factor('A',x);right=m.factor('B',y)
                full=m.star(left,right)
                self.assertNotIn(full,records)
                self.assertEqual(m.unpack(full),(left,right))
                records.add(full)
            self.assertEqual(len(records),len(elements)**2)

    def test_14_native_minus_one_is_not_identified_with_a_signed_receipt(self):
        for m in self.models.values():
            negative=m.star(m.factor('A',MINUS_ONE),m.factor('B',ONE))
            positive=m.star(m.factor('A',ONE),m.factor('B',MINUS_ONE))
            self.assertEqual(m.read(negative),m.read(positive))
            self.assertNotEqual(negative,positive)
            self.assertNotEqual(negative,m.factor('A',MINUS_ONE))
            self.assertNotEqual(negative,m.factor('B',MINUS_ONE))


if __name__=='__main__':
    unittest.main()
