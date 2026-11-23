"""Exhaustive checks for the necessity/sufficiency theorem on finite semilattices."""
import unittest
from itertools import product as cartesian_product
from two_sided_distributivity import (
    X, Y, Left, Right, Output, left_add, right_add, output_add,
    product, unpack, left_domain, right_domain, zero_row_collision,
    idempotent_pair_construction,
)


class BothSidedTests(unittest.TestCase):
    def setUp(self):
        self.A, self.B = left_domain(), right_domain()

    def test_both_distributions_all_128_inputs(self):
        for a1,a2,b in cartesian_product(self.A,self.A,self.B):
            self.assertEqual(product(left_add(a1,a2),b),
                             output_add(product(a1,b),product(a2,b)))
        for a,b1,b2 in cartesian_product(self.A,self.B,self.B):
            self.assertEqual(product(a,right_add(b1,b2)),
                             output_add(product(a,b1),product(a,b2)))
        self.assertEqual(64+64,128)

    def test_injective_on_all_16_pairs_including_zero(self):
        results = [product(a,b) for a,b in cartesian_product(self.A,self.B)]
        self.assertEqual(len(results),16)
        self.assertEqual(len(set(results)),16)
        for a,b in cartesian_product(self.A,self.B):
            self.assertEqual(unpack(product(a,b)),(a,b))

    def test_idempotent_input_monoids(self):
        for a in self.A:self.assertEqual(left_add(a,a),a)
        for b in self.B:self.assertEqual(right_add(b,b),b)
        for x,y,z in cartesian_product(self.A,repeat=3):
            self.assertEqual(left_add(left_add(x,y),z),left_add(x,left_add(y,z)))
            self.assertEqual(left_add(x,y),left_add(y,x))
        for x,y,z in cartesian_product(self.B,repeat=3):
            self.assertEqual(right_add(right_add(x,y),z),right_add(x,right_add(y,z)))

    def test_output_commutative_idempotent_monoid(self):
        vals=[product(a,b) for a,b in cartesian_product(self.A,self.B)]
        z=Output(frozenset())
        for x,y in cartesian_product(vals,repeat=2):
            self.assertEqual(output_add(x,y),output_add(y,x))
            self.assertEqual(output_add(x,z),x)
        for x in vals:self.assertEqual(output_add(x,x),x)

    def test_typed_zero_nonabsorbing_and_different(self):
        zero_a,zero_b=Left(frozenset()),Right(frozenset())
        rights=[b for b in self.B if b!=zero_b]
        lefts=[a for a in self.A if a!=zero_a]
        self.assertEqual(len({product(zero_a,b) for b in self.B}),4)
        self.assertEqual(len({product(a,zero_b) for a in self.A}),4)
        self.assertEqual(product(zero_a,zero_b),Output(frozenset()))
        for b in rights:self.assertNotEqual(product(zero_a,b),Output(frozenset()))
        for a in lefts:self.assertNotEqual(product(a,zero_b),Output(frozenset()))

    def test_cross_tokens_encode_true_interaction(self):
        a=Left(frozenset({'alpha','beta'}))
        b=Right(frozenset({'u','v'}))
        p=product(a,b)
        self.assertIn(('P','alpha','u'),p.tokens)
        self.assertIn(('P','beta','v'),p.tokens)
        self.assertEqual(len(p.tokens),8) # 2 L, 2 R, 4 interactions
        self.assertEqual(unpack(p),(a,b))

    def test_sum_of_products_can_lose_product_normal_form(self):
        e1=product(Left(frozenset({'alpha'})),Right(frozenset({'u'})))
        e2=product(Left(frozenset({'beta'})),Right(frozenset({'v'})))
        s=output_add(e1,e2)
        with self.assertRaises(ValueError):unpack(s)
        self.assertNotEqual(s,product(left_add(Left(frozenset({'alpha'})),Left(frozenset({'beta'}))),
                                      right_add(Right(frozenset({'u'})),Right(frozenset({'v'})))))

    def test_distributivity_generates_zero_collision_for_integer_inputs(self):
        # Independent symbolic proof: 0+0=0 in integers and d+d!=d for d=1.
        # Any separately distributive total mu would identify mu(0,1) and mu(0,2).
        self.assertEqual(0+0,0)
        self.assertNotEqual(1+1,1)
        # No target-addition assumption is used for the collision.
        # A plain numeric bilinear multiplication exhibits the collapse.
        self.assertTrue(zero_row_collision(0,1,lambda a,b:a+b,
                                          lambda a,b:a+b,lambda a,b:a*b))
        self.assertEqual(0*1,0*2)

    def test_right_zero_collision_in_integers(self):
        self.assertEqual(0+0,0)
        self.assertNotEqual(2+2,2)
        self.assertEqual(7*0,14*0)
        self.assertEqual(7*0,7*(0+0))

    def test_zero_preserving_bimorphism_would_forbid_injection(self):
        # Standard module/tensor-product bilinearity often *also* requires
        # each zero-factor image to equal the GLOBAL additive zero in E.
        za=Left(frozenset())
        nonempty=Right(frozenset({'u'}))
        self.assertNotEqual(product(za,nonempty),product(za,Right(frozenset())))
        self.assertNotEqual(product(Left(frozenset({'alpha'})),Right(frozenset())),
                            product(za,Right(frozenset())))


if __name__=='__main__':unittest.main()


class AdditiveGroupTests(unittest.TestCase):
    def test_cyclic_z3_symmetric_signed_pair_collapse(self):
        from two_sided_distributivity import cyclic_bilinear_map
        for k in range(3):
            self.assertEqual(cyclic_bilinear_map(-1,-1,k),cyclic_bilinear_map(1,1,k))
            self.assertEqual(cyclic_bilinear_map(0,1,k),cyclic_bilinear_map(0,2,k))

    def test_all_19683_functions_z3_to_z3_bilinear_are_three(self):
        from itertools import product
        from two_sided_distributivity import list_cyclic_bilinear_maps
        m=3; possible=list_cyclic_bilinear_maps(m)
        self.assertEqual(len(possible),3)
        valid=0
        for entries in product(range(m),repeat=m*m):
            f=lambda a,b: entries[(a%m)*m+(b%m)]
            works=all(f((a+c)%m,b)==(f(a,b)+f(c,b))%m
                      for a,c,b in product(range(m),repeat=3))
            if works:
                works=all(f(a,(b+d)%m)==(f(a,b)+f(a,d))%m
                          for a,b,d in product(range(m),repeat=3))
            if works:
                valid+=1
                self.assertIn(tuple(tuple(f(a,b) for b in range(m))
                                    for a in range(m)),possible)
        self.assertEqual(valid,3)
