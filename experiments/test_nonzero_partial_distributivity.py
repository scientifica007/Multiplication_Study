"""Proof-obligation checks for nonzero bilateral-distributivity obstruction."""
import unittest
from itertools import product
from nonzero_partial_distributivity import (
    receipt, unpack, reading, permitted_sum, diamond_pair,
    tagged_add, tagged_product, Tagged,
    one_sided_product, group_add, restricted_partial_product, vec_add,
    full_receipt_reading_additivity,
)


class NonzeroDistributivityTests(unittest.TestCase):
    def test_minimal_nonzero_diamond(self):
        x,y = diamond_pair(1,1)
        self.assertEqual(reading(x), reading(y))
        self.assertNotEqual(x,y)
        self.assertNotEqual(unpack(x),unpack(y))
        self.assertEqual(x.left.value,2)
        self.assertEqual(y.right.value,2)
        self.assertTrue(permitted_sum(1,1))

    def test_nonzero_diamond_all_signed_scales(self):
        for a,b in product(range(-7,8),repeat=2):
            if not a or not b:continue
            x,y = diamond_pair(a,b)
            self.assertNotEqual(unpack(x),unpack(y))
            self.assertEqual(reading(x),reading(y))

    def test_positive_all_two_sided_distribution_collapse(self):
        for a,b in product(range(1,10), repeat=2):
            t = tagged_product(a,b)
            self.assertEqual(t,Tagged(a*b,True))
            for aa in range(1,10):
                self.assertEqual(tagged_product(a+aa,b),
                                 tagged_add(t,tagged_product(aa,b)))
            for bb in range(1,10):
                self.assertEqual(tagged_product(a,b+bb),
                                 tagged_add(t,tagged_product(a,bb)))

    def test_all_signed_nonzero_distributive_relations(self):
        numbers = tuple(i for i in range(-5,6) if i)
        for a,b,c in product(numbers,repeat=3):
            if a+b:
                self.assertEqual(tagged_product(a+b,c), tagged_add(tagged_product(a,c),tagged_product(b,c)))
                self.assertEqual(tagged_product(c,a+b), tagged_add(tagged_product(c,a),tagged_product(c,b)))

    def test_signed_sign_reversal_collision_even_without_zero(self):
        x=tagged_product(-1,-1)
        y=tagged_product(1,1)
        self.assertEqual(x,y)
        self.assertEqual(x,Tagged(1,True))
        self.assertEqual(tagged_add(tagged_product(1,1),tagged_product(-1,1)),Tagged(0,True))
        self.assertNotEqual(Tagged(0,True),Tagged(0,False))

    def test_one_sided_injective_for_nonzero_signed_integers(self):
        domain=tuple(i for i in range(-5,6) if i)
        seen={}
        for a,b in product(domain,repeat=2):
            o=one_sided_product(a,b)
            self.assertNotIn(o,seen)
            seen[o]=(a,b)
        self.assertEqual(len(seen),100)
        for a,b,c in product(domain,repeat=3):
            if a+b:
                self.assertEqual(one_sided_product(a+b,c),group_add(one_sided_product(a,c),one_sided_product(b,c)))

    def test_one_sided_counterexample_to_right_distribution(self):
        left=one_sided_product(1,2)
        right=group_add(one_sided_product(1,1),one_sided_product(1,1))
        self.assertNotEqual(left,right)
        self.assertEqual(left,((2,1),))
        self.assertEqual(right,((1,2),))

    def test_partial_both_directions_on_disjoint_fibers_is_injective(self):
        domain=list(product((1,2,3),repeat=2))
        values={p:restricted_partial_product(*p) for p in domain}
        self.assertEqual(len(values),9)
        self.assertEqual(len(set(values.values())),9)
        self.assertEqual(values[2,1], vec_add(values[1,1],values[1,1]))
        self.assertEqual(values[3,2], vec_add(values[3,1],values[3,1]))
        self.assertNotEqual(values[1,2],vec_add(values[1,1],values[1,1]))

    def test_full_receipts_measure_distributivity_both_sides(self):
        nums=tuple(i for i in range(-4,5) if i)
        for a,b,c in product(nums,repeat=3):
            if not permitted_sum(a,b): continue
            for left in (True,False):
                ok,whole,pieces=full_receipt_reading_additivity(a,b,c,left=left)
                self.assertTrue(ok)
                self.assertNotEqual(whole,pieces)
                self.assertEqual(unpack(whole), (whole.left,whole.right))

    def test_type_order_and_nonzero_domain(self):
        with self.assertRaises(ValueError):receipt(0,1)
        with self.assertRaises(ValueError):receipt(1,0)
        with self.assertRaises(ValueError):one_sided_product(1,0)
        self.assertNotEqual(receipt(1,2),receipt(2,1))
        self.assertEqual(unpack(receipt(-1,-1))[0].sort,'A')
        self.assertEqual(unpack(receipt(-1,-1))[1].sort,'B')


if __name__=='__main__':unittest.main()
