"""Independent exhaustive/bounded tests of the provenance monoid model."""
import unittest
from itertools import product
from distributivity_provenance import (
    LABELS, RIGHT_READING, Left, Right, Output, zero, plus,
    multiply, unpack_product, reading, erase_provenance, local_inverse,
    raw_decomposition_left,
)

class DistributivityTests(unittest.TestCase):
    def test_full_distributivity_including_zero_and_negative_cancellation(self):
        for label,a,b in product(LABELS,range(-5,6),range(-5,6)):
            d=Right(label)
            lhs=multiply(Left(a+b),d)
            rhs=plus(multiply(Left(a),d),multiply(Left(b),d))
            self.assertEqual(lhs,rhs,(label,a,b))
            self.assertEqual(unpack_product(rhs),(Left(a+b),d))

    def test_complete_input_unpacked_and_injection(self):
        image=set()
        for label,a in product(LABELS,range(-8,9)):
            c=Left(a); d=Right(label);e=multiply(c,d)
            self.assertEqual(unpack_product(e),(c,d))
            self.assertNotIn(e,image)
            image.add(e)
        self.assertEqual(len(image),3*17)

    def test_tagged_zero_is_not_global_zero(self):
        allzero=[multiply(Left(0),Right(d)) for d in LABELS]
        self.assertEqual(len(set(allzero)),len(LABELS))
        for e in allzero:
            self.assertNotEqual(e,zero())
            self.assertEqual(plus(e,e),e)
            self.assertEqual(reading(e),0)
            self.assertEqual(erase_provenance(e),zero().vector)

    def test_non_cancellativity_and_local_inverse(self):
        e=multiply(Left(0),Right('positive'))
        self.assertEqual(plus(zero(),e),plus(e,e))
        self.assertNotEqual(zero(),e)
        for label,n in product(LABELS,range(-6,7)):
            u=multiply(Left(n),Right(label))
            inv=local_inverse(u)
            self.assertEqual(plus(u,inv),multiply(Left(0),Right(label)))
            self.assertNotEqual(plus(u,inv),zero())
            self.assertEqual(plus(u,plus(inv,u)),u)

    def test_additive_monoid_associative_commutative_and_identity(self):
        vals=[zero()]+[multiply(Left(n),Right(d)) for d,n in
                      product(LABELS,(-2,0,2))]
        for a,b,c in product(vals,repeat=3):
            self.assertEqual(plus(a,b),plus(b,a))
            self.assertEqual(plus(plus(a,b),c),plus(a,plus(b,c)))
        for a in vals:
            self.assertEqual(plus(a,zero()),a)

    def test_group_valued_reading_and_signed_products(self):
        for label,n in product(LABELS,range(-5,6)):
            e=multiply(Left(n),Right(label))
            self.assertEqual(reading(e),n*RIGHT_READING[label])
        x=multiply(Left(-1),Right('negative'))
        y=multiply(Left(+1),Right('positive'))
        self.assertEqual(reading(x),reading(y))
        self.assertNotEqual(x,y)
        self.assertNotEqual(unpack_product(x),unpack_product(y))

    def test_projection_group_forgets_distinct_typed_zeros(self):
        for label in LABELS:
            self.assertEqual(erase_provenance(multiply(Left(0),Right(label))),zero().vector)
        vals=[zero()]+[multiply(Left(n),Right(d)) for d,n in product(LABELS,range(-3,4))]
        for a,b in product(vals,repeat=2):
            self.assertEqual(erase_provenance(plus(a,b)),
                             tuple(x+y for x,y in zip(erase_provenance(a),erase_provenance(b))))

    def test_two_additive_decompositions_but_single_product_unpack(self):
        d=Right('double')
        r1=raw_decomposition_left(1,3,d)
        r2=raw_decomposition_left(2,2,d)
        self.assertEqual(r1,r2)
        self.assertEqual(r1,multiply(Left(4),d))
        self.assertEqual(unpack_product(r1),(Left(4),d))
        self.assertNotEqual((1,3),(2,2))
        with self.assertRaises(ValueError):
            unpack_product(plus(multiply(Left(1),Right('positive')),
                                multiply(Left(1),Right('negative'))))

    def test_zero_collapse_in_untagged_group_model(self):
        for x,y in product(LABELS,repeat=2):
            if x==y:continue
            self.assertEqual(erase_provenance(multiply(Left(0),Right(x))),
                             erase_provenance(multiply(Left(0),Right(y))))

    def test_supported_vectors_and_invalid_sort_inputs(self):
        with self.assertRaises(ValueError):Output((1,0,0),frozenset())
        with self.assertRaises(ValueError):Output((0,0,0),frozenset(('invalid',)))
        with self.assertRaises(TypeError):multiply(Right('positive'),Left(2))
        with self.assertRaises(TypeError):plus(Left(2),zero())
        with self.assertRaises(ValueError):unpack_product(zero())
        with self.assertRaises(ValueError):Right('bad')

if __name__=='__main__':unittest.main()
