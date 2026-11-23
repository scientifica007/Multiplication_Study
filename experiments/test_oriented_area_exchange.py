"""Exact independent certificates for the conditional orientation thesis."""
import unittest
from fractions import Fraction
from itertools import product as cartesian
from oriented_area_exchange import (
    Vector, EA, EB, omega, Matrix, IDENTITY, MINUS_IDENTITY,
    J_STANDARD, swap, normalized_swap, TypedFactor, receipt, product,
    transform_receipt, FormalReceiptSum, formal_basis, formal_wedge,
)


class OrientedAreaTests(unittest.TestCase):
    def test_01_native_typed_product_not_redefined_as_geometric_wedge(self):
        a, b = TypedFactor('A', 2), TypedFactor('B', 3)
        p = product(a, b)
        self.assertEqual(p.unpack(), (a, b))
        self.assertEqual(p.reading, 6)
        self.assertIsNone(product(b, a))
        self.assertIsNone(product(a, a))
        self.assertIsNone(product(b, b))
        self.assertIsNone(product(EA, EB))

    def test_02_oriented_area_is_alternating_and_bilinear(self):
        vectors = [EA, EB, Vector(2, 3), Vector(-1, Fraction(3, 2))]
        for x, y, z in cartesian(vectors, repeat=3):
            self.assertEqual(omega(x, y), -omega(y, x))
            self.assertEqual(omega(x, x), 0)
            self.assertEqual(omega(x+y, z), omega(x, z)+omega(y, z))
            self.assertEqual(omega(x, y+z), omega(x, y)+omega(x, z))
        self.assertEqual(omega(EA, EB), 1)
        self.assertEqual(omega(EB, EA), -1)

    def test_03_determinant_covariance_exact_for_many_nonzero_matrices(self):
        coeffs=(-2,-1,0,Fraction(1,2),1,2)
        vectors=(EA,EB,Vector(2,-3),Vector(Fraction(1,2),Fraction(2,3)))
        for a,b,c,d in cartesian(coeffs,repeat=4):
            m=Matrix(a,b,c,d)
            for u,v in cartesian(vectors,repeat=2):
                self.assertEqual(omega(m(u),m(v)),m.determinant*omega(u,v))

    def test_04_pure_role_swap_area_preservation_iff_alpha_beta_minus_one(self):
        coeffs=(-3,-2,-1,Fraction(-1,2),0,Fraction(1,2),1,2,3)
        for alpha,beta in cartesian(coeffs,repeat=2):
            t=swap(alpha,beta)
            self.assertEqual(t.signed_area_preserving(),alpha*beta==-1)
            self.assertEqual(t@t,Matrix(alpha*beta,0,0,alpha*beta))
            self.assertEqual(omega(t(EA),t(EB)),-alpha*beta)

    def test_05_normalized_beta_one_selects_exactly_negative_one(self):
        for alpha in (-3,-2,-1,0,1,2,3):
            self.assertEqual(normalized_swap(alpha).signed_area_preserving(),alpha==-1)
        self.assertEqual(normalized_swap(-1),J_STANDARD)
        self.assertEqual(J_STANDARD@J_STANDARD,MINUS_IDENTITY)
        self.assertEqual(J_STANDARD@J_STANDARD@J_STANDARD@J_STANDARD,IDENTITY)

    def test_06_orientation_preservation_is_weaker_than_area_preservation(self):
        t=swap(-2,1)
        self.assertEqual(t.determinant,2)
        self.assertTrue(t.orientation_preserving())
        self.assertFalse(t.signed_area_preserving())
        self.assertEqual(t@t,Matrix(-2,0,0,-2))
        self.assertNotEqual(t@t,MINUS_IDENTITY)

    def test_07_absolute_area_and_metric_do_not_select_the_sign(self):
        unsigned_swap=swap(1,1)
        self.assertTrue(unsigned_swap.absolute_area_preserving())
        self.assertFalse(unsigned_swap.signed_area_preserving())
        self.assertTrue(unsigned_swap.euclidean_metric_preserving())
        self.assertTrue(J_STANDARD.euclidean_metric_preserving())
        self.assertEqual(unsigned_swap@unsigned_swap,IDENTITY)
        self.assertEqual(unsigned_swap.determinant,-1)

    def test_08_area_alone_not_enough_without_axis_exchange(self):
        shear=Matrix(1,1,0,1)
        self.assertTrue(shear.signed_area_preserving())
        self.assertTrue(shear.orientation_preserving())
        self.assertNotEqual(shear@shear,MINUS_IDENTITY)
        self.assertEqual(shear@shear,Matrix(1,2,0,1))
        self.assertFalse(shear.euclidean_metric_preserving())

    def test_09_infinitely_many_area_preserving_axis_swaps(self):
        for beta in (Fraction(1,3),Fraction(1,2),1,2,-3):
            alpha=-Fraction(1,1)/Fraction(beta)
            t=swap(alpha,beta)
            self.assertEqual(t.determinant,1)
            self.assertEqual(t@t,MINUS_IDENTITY)
            diagonal=Matrix(beta,0,0,1)
            self.assertEqual(diagonal.inverse()@J_STANDARD@diagonal,t)
            self.assertEqual(t.inverse(),Matrix(0,-alpha,-beta,0))
        self.assertNotEqual(swap(-2,Fraction(1,2)),J_STANDARD)

    def test_10_scaling_nonzero_form_keeps_same_invariance_condition(self):
        for lam in (-3, Fraction(2,3), 1, 4):
            for alpha,beta in ((-1,1),(-2,1),(1,1),(-2,Fraction(1,2))):
                t=swap(alpha,beta)
                self.assertEqual(omega(t(EA),t(EB),lam)==omega(EA,EB,lam),
                                 alpha*beta==-1)
        # The identically zero 'area' would make every map preserve it.
        self.assertEqual(omega(swap(1,1)(EA),swap(1,1)(EB),0),omega(EA,EB,0))

    def test_11_transformed_full_receipts_are_recoverable(self):
        for alpha,beta in ((-1,1),(-2,Fraction(1,2)),(1,1)):
            t=swap(alpha,beta)
            for a,b in cartesian((-2,-1,0,1,2),repeat=2):
                p=receipt(a,b)
                q=transform_receipt(p,t)
                self.assertEqual(q.unpack(),(TypedFactor('A',alpha*b),TypedFactor('B',beta*a)))
                self.assertEqual(q.reading,alpha*beta*p.reading)
            with self.assertRaises(ValueError):transform_receipt(receipt(1,2),Matrix(1,1,0,1))

    def test_12_record_scalar_reading_flips_but_basis_area_is_preserved(self):
        p=receipt(2,3)
        t=J_STANDARD
        q=transform_receipt(p,t)
        self.assertEqual(p.reading,6)
        self.assertEqual(q.reading,-6)
        self.assertEqual(omega(t(EA),t(EB)),omega(EA,EB))
        self.assertNotEqual(p,q)
        # The two-vector area and one-record reading are not the same observable.

    def test_13_signed_formal_wedge_projects_to_numeric_area(self):
        vec=(EA,EB,Vector(2,3),Vector(-4,1),Vector(Fraction(1,3),Fraction(-1,2)))
        for u,v in cartesian(vec,repeat=2):
            self.assertEqual(formal_wedge(u,v).read(),omega(u,v))
            self.assertEqual(formal_wedge(u,v),-formal_wedge(v,u))
            self.assertEqual(formal_wedge(u,u),FormalReceiptSum.from_items(()))

    def test_14_formal_wedge_is_not_bilinear_in_free_receipt_group(self):
        u,v,w=EA,2*EA,EB
        left=formal_wedge(u+v,w)
        right=formal_wedge(u,w)+formal_wedge(v,w)
        self.assertNotEqual(left,right)
        self.assertEqual(left.read(),right.read())
        self.assertEqual(left.read(),3)

    def test_15_area_numeric_invariant_but_full_signed_provenance_not(self):
        before=formal_wedge(EA,EB)
        after=formal_wedge(J_STANDARD(EA),J_STANDARD(EB))
        self.assertNotEqual(before,after)
        self.assertEqual(before.read(),after.read())
        self.assertEqual(before.read(),1)
        self.assertEqual(before,formal_basis(1,1)-formal_basis(0,0))
        self.assertEqual(after,formal_basis(0,0)-formal_basis(-1,1))

    def test_16_several_signed_symmetries_have_different_normalizations(self):
        t1=swap(-1,1);t2=swap(-2,Fraction(1,2))
        for u,v in cartesian((EA,EB,Vector(-2,3)),repeat=2):
            self.assertEqual(omega(t1(u),t1(v)),omega(u,v))
            self.assertEqual(omega(t2(u),t2(v)),omega(u,v))
        self.assertNotEqual(t1(EA),t2(EA))
        self.assertNotEqual(t1(EB),t2(EB))

    def test_17_zero_swap_and_singular_matrices_do_not_preserve_area(self):
        t=swap(0,1)
        self.assertEqual(t.determinant,0)
        self.assertEqual(omega(t(EA),t(EB)),0)
        self.assertEqual(t@t,Matrix(0,0,0,0))
        with self.assertRaises(ZeroDivisionError):t.inverse()

    def test_18_metric_preservation_adds_extra_normalization(self):
        t=swap(-2,Fraction(1,2))
        self.assertTrue(t.signed_area_preserving())
        self.assertFalse(t.euclidean_metric_preserving())
        for alpha,beta in cartesian((-2,-1,1,2),repeat=2):
            t=swap(alpha,beta)
            if t.signed_area_preserving() and t.euclidean_metric_preserving():
                self.assertIn((alpha,beta),((-1,1),(1,-1)))

    def test_19_antisymmetry_of_area_not_same_as_native_operand_swap(self):
        self.assertEqual(omega(EA,EB),-omega(EB,EA))
        self.assertIsNone(product(TypedFactor('B',1),TypedFactor('A',1)))
        self.assertEqual(receipt(-1,-1).reading,1)
        self.assertEqual(J_STANDARD@J_STANDARD,MINUS_IDENTITY)
        self.assertNotEqual(formal_basis(-1,-1),-formal_basis(1,1))


if __name__ == '__main__':
    unittest.main()
