"""Exact tests for typed signed-exchange and three different quadratic rings."""
import unittest
from fractions import Fraction
from itertools import product
from signed_exchange_extension import (
    Factor, Receipt, CQuantity, make, star, unpack, add, native_reading,
    signed_exchange, iterate_exchange, Pair, multiply_pair,
    pair_exchange, coordinate_reading, real_embed_product_reading,
    J, ONE, ZERO,
)


class SignedExchangeTests(unittest.TestCase):
    def test_01_original_native_star_still_requires_distinct_types(self):
        a,b=Factor('A',1),Factor('B',1)
        self.assertEqual(unpack(star(a,b)),(a,b))
        for x,y in ((a,a),(b,b),(b,a)):
            self.assertIsNone(star(x,y))
            self.assertIsNone(add(x,y) if x.sort!=y.sort else star(x,y))
        self.assertEqual(add(a,Factor('A',2)),Factor('A',3))

    def test_02_four_signed_receipts_distinct_but_two_scalar_signs(self):
        s=[make(a,b) for a,b in product((-1,1),repeat=2)]
        self.assertEqual(len(set(s)),4)
        self.assertEqual(len({native_reading(x) for x in s}),2)
        self.assertNotEqual(make(-1,-1),make(1,1))
        self.assertEqual(native_reading(make(-1,-1)),1)

    def test_03_temporary_rotation_is_nontrivial_order_four(self):
        p=make(1,1)
        orbit=[iterate_exchange(p,n) for n in range(5)]
        self.assertEqual(orbit,[make(1,1),make(-1,1),make(-1,-1),
                                make(1,-1),make(1,1)])
        self.assertEqual(len(set(orbit[:4])),4)

    def test_04_rotation_squared_signs_both_factors_not_additive_negation(self):
        vals=(-2,-1,0,1,2)
        for a,b in product(vals,repeat=2):
            p=make(a,b)
            self.assertEqual(iterate_exchange(p,2),make(-a,-b))
            self.assertEqual(iterate_exchange(p,4),p)
            if (a,b)!=(0,0):self.assertNotEqual(iterate_exchange(p,2),p)
        self.assertEqual(iterate_exchange(make(0,0),1),make(0,0))

    def test_05_untwisted_exchange_is_an_involution(self):
        for a,b in product(range(-3,4),repeat=2):
            p=make(a,b)
            self.assertEqual(signed_exchange(p,1),make(b,a))
            self.assertEqual(iterate_exchange(p,2,1),p)
        self.assertNotEqual(signed_exchange(make(1,2)),signed_exchange(make(1,2),1))

    def test_06_degenerate_zero_exchange_is_not_an_involution(self):
        p=make(1,2)
        self.assertEqual(signed_exchange(p,0),make(0,1))
        self.assertEqual(iterate_exchange(p,2,0),make(0,0))
        self.assertNotEqual(iterate_exchange(p,2,0),CQuantity(()))
        self.assertNotEqual(iterate_exchange(p,2,0),p)

    def test_07_exchange_adds_as_a_map_of_receipt_multisets(self):
        p,q=make(1,2),make(-1,2)
        total=add(p,q)
        for kappa in (-1,0,1):
            self.assertEqual(signed_exchange(total,kappa),
                             add(signed_exchange(p,kappa),signed_exchange(q,kappa)))
            self.assertEqual(len(signed_exchange(total,kappa).terms),2)
        self.assertEqual(unpack(total),None)

    def test_08_standard_product_reading_sees_order_two_not_four(self):
        for a,b in product(range(-3,4),repeat=2):
            p=make(a,b)
            self.assertEqual(native_reading(signed_exchange(p,-1)),
                             -native_reading(p))
            self.assertEqual(native_reading(iterate_exchange(p,2,-1)),
                             native_reading(p))

    def test_09_pair_operator_squares_to_kappa_identity(self):
        for kappa in (-1,0,1):
            for a,b in product(range(-3,4),repeat=2):
                p=Pair(a,b)
                self.assertEqual(pair_exchange(pair_exchange(p,kappa),kappa),kappa*p)
                self.assertEqual(pair_exchange(p,kappa),multiply_pair(J,p,kappa))

    def test_10_three_external_quadratic_algebras_associative_distributive(self):
        xs=[ZERO,ONE,J,Pair(-2,1),Pair(Fraction(1,2),Fraction(3,4))]
        for kappa in (-1,0,1):
            for a,b,c in product(xs,repeat=3):
                self.assertEqual(multiply_pair(multiply_pair(a,b,kappa),c,kappa),
                                 multiply_pair(a,multiply_pair(b,c,kappa),kappa))
                self.assertEqual(multiply_pair(a,b,kappa),multiply_pair(b,a,kappa))
                self.assertEqual(multiply_pair(a,b+c,kappa),
                                 multiply_pair(a,b,kappa)+multiply_pair(a,c,kappa))
            for x in xs:self.assertEqual(multiply_pair(ONE,x,kappa),x)
            self.assertEqual(multiply_pair(J,J,kappa),Pair(kappa,0))

    def test_11_zero_divisors_only_in_plus_and_zero_examples(self):
        self.assertEqual(multiply_pair(ONE+J,ONE-J,1),ZERO)
        self.assertNotEqual(ONE+J,ZERO)
        self.assertNotEqual(ONE-J,ZERO)
        self.assertEqual(multiply_pair(J,J,0),ZERO)
        self.assertNotEqual(J,ZERO)
        # In Q(i), norm x^2+y^2 nonzero except at origin (proof independent).
        for a,b in product(range(-3,4),repeat=2):
            x=Pair(a,b)
            if x!=ZERO:
                inverse=Pair(Fraction(a,a*a+b*b),Fraction(-b,a*a+b*b))
                self.assertEqual(multiply_pair(x,inverse,-1),ONE)

    def test_12_coordinate_map_is_equivariant_with_turning(self):
        xs=[CQuantity(()),make(1,1),make(-1,-1),add(make(2,3),make(-4,5))]
        for kappa in (-1,0,1):
            for x in xs:
                self.assertEqual(coordinate_reading(signed_exchange(x,kappa)),
                                 multiply_pair(J,coordinate_reading(x),kappa))

    def test_13_standard_numeric_reading_cannot_be_rotation_equivariant(self):
        p=make(1,1)
        left=real_embed_product_reading(signed_exchange(p,-1))
        right=multiply_pair(J,real_embed_product_reading(p),-1)
        self.assertEqual(left,Pair(-1,0))
        self.assertEqual(right,Pair(0,1))
        self.assertNotEqual(left,right)
        # More generally, all nonzero ab fail over Q since independent coords.
        for a,b in product((-2,-1,1,2),repeat=2):
            p=make(a,b)
            self.assertNotEqual(real_embed_product_reading(signed_exchange(p)),
                                multiply_pair(J,real_embed_product_reading(p),-1))

    def test_14_double_minus_receipt_is_half_turn_not_an_i_root(self):
        p=make(1,1)
        self.assertEqual(iterate_exchange(p,2),make(-1,-1))
        self.assertEqual(native_reading(make(-1,-1)),1)
        self.assertEqual(coordinate_reading(make(-1,-1)),Pair(-1,-1))
        self.assertEqual(multiply_pair(J,J,-1),Pair(-1,0))
        self.assertNotEqual(coordinate_reading(make(-1,-1)),J)

    def test_15_external_pair_field_and_native_receipts_are_not_identical(self):
        p=make(1,0)
        self.assertEqual(native_reading(p),0)
        self.assertEqual(coordinate_reading(p),ONE)
        self.assertEqual(coordinate_reading(signed_exchange(p)),J)
        self.assertEqual(coordinate_reading(iterate_exchange(p,2)),Pair(-1,0))
        # Ring unit and imaginary element came from a CHANGED coordinate reading.

    def test_16_ring_epsilon_distinguished_by_real_linear_algebra(self):
        # j^2 differs at precisely the parameter kappa, an EXTRA choice.
        products=[multiply_pair(J,J,k) for k in (-1,0,1)]
        self.assertEqual(products,[Pair(-1,0),ZERO,ONE])
        self.assertEqual(len(set(products)),3)

    def test_17_neither_ring_multiplication_nor_receipt_self_product_native(self):
        c=make(1,1)
        self.assertIsNone(star(c,c))
        self.assertIsNone(star(Factor('A',1),Factor('A',2)))
        self.assertIsNone(add(Factor('A',1),Factor('B',1)))
        self.assertEqual(multiply_pair(J,J,-1),Pair(-1,0))

    def test_18_full_quarter_turn_preserves_recoverability_and_source_roles(self):
        for a,b in product(range(-3,4),repeat=2):
            c=signed_exchange(make(a,b))
            restored=unpack(c)
            self.assertEqual(restored,(Factor('A',-b),Factor('B',a)))
            self.assertEqual(iterate_exchange(c,3),make(a,b))


if __name__=='__main__':unittest.main()
