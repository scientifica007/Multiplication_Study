"""Round 22 exact tests; independent finite witnesses never replace proofs."""
import unittest
from fractions import Fraction
from itertools import combinations, product
from bilinear_provenance_quotients import (
    TypedFactor, Receipt, native_star, FreeQ, FREE_ZERO, basis, Vector,
    raw_wedge, area, affine_class, strict_bilinear_class,
    affine_normal_form, bilinear_p_relation,
    wedge_additivity_defect, wedge_homogeneity_defect,
    universal_affine_relation, finite_presentation_ranks, matrix_rank,
)


class BilinearProvenanceTests(unittest.TestCase):
    def test_01_original_native_types_and_unpack(self):
        for a,b in product((-2, -1, 0, 1, 2), repeat=2):
            aa,bb=TypedFactor('A',a),TypedFactor('B',b)
            p=native_star(aa,bb)
            self.assertEqual(p.unpack(),(aa,bb))
            self.assertEqual(p.reading,a*b)
            self.assertIsNone(native_star(aa,aa))
            self.assertIsNone(native_star(bb,bb))
            self.assertIsNone(native_star(bb,aa))
        with self.assertRaises(ValueError):TypedFactor('C',1)

    def test_02_original_records_do_not_collapse_when_product_reading_equal(self):
        pairs=[(2,3),(1,6),(-2,-3),(-1,-6)]
        self.assertEqual(len({Receipt(a,b) for a,b in pairs}),4)
        self.assertEqual(len({basis(a,b) for a,b in pairs}),4)
        self.assertEqual({basis(a,b).product_reading for a,b in pairs},{6})

    def test_03_raw_wedge_is_alternating_without_quotient(self):
        vectors=(Vector(0,0),Vector(1,0),Vector(0,1),Vector(2,3),Vector(-1,2))
        for u,v in product(vectors,repeat=2):
            self.assertEqual(raw_wedge(u,v),-raw_wedge(v,u))
            self.assertEqual(raw_wedge(u,u),FREE_ZERO)

    def test_04_raw_wedge_fails_additivity_with_full_provenance(self):
        u,up,v=Vector(1,0),Vector(2,0),Vector(0,1)
        defect=wedge_additivity_defect(u,up,v)
        self.assertNotEqual(defect,FREE_ZERO)
        self.assertEqual(affine_class(defect),(0,0))
        self.assertEqual(strict_bilinear_class(defect),0)

    def test_05_raw_wedge_fails_zero_and_homogeneity(self):
        u,v=Vector(1,0),Vector(0,1)
        self.assertNotEqual(raw_wedge(Vector(0,0),v),FREE_ZERO)
        defect=wedge_homogeneity_defect(2,u,v)
        self.assertNotEqual(defect,FREE_ZERO)
        self.assertEqual(affine_class(defect),(0,0))

    def test_06_affine_quotient_of_w_is_bilinear_over_q(self):
        vs=[Vector(0,0),Vector(1,0),Vector(0,1),Vector(2,-3),
            Vector(Fraction(1,2),Fraction(-3,5))]
        for u,up,v in product(vs,repeat=3):
            self.assertEqual(affine_class(wedge_additivity_defect(u,up,v)),(0,0))
            self.assertEqual(affine_class(wedge_additivity_defect(v,u,up)),(0,0))
        for lam,u,v in product((Fraction(-3,2),0,1,2),vs,vs):
            self.assertEqual(affine_class(wedge_homogeneity_defect(lam,u,v)),(0,0))

    def test_07_affine_wedge_is_exactly_area_in_second_coordinate(self):
        vs=(Vector(0,0),Vector(1,0),Vector(0,1),Vector(-2,3))
        for u,v in product(vs,repeat=2):
            self.assertEqual(affine_class(raw_wedge(u,v)),(0,area(u,v)))
            self.assertEqual(affine_class(raw_wedge(v,u)),(0,-area(u,v)))

    def test_08_affine_quotient_remembers_count_but_not_full_history(self):
        self.assertEqual(affine_class(basis(2,3)),(1,6))
        self.assertEqual(affine_class(basis(1,6)),(1,6))
        self.assertEqual(affine_class(basis(2,3)+basis(1,6)),(2,12))
        self.assertNotEqual(affine_class(basis(2,3)),affine_class(2*basis(2,3)))
        self.assertEqual(affine_class(2*basis(2,3)),(2,12))

    def test_09_affine_bilinearity_of_w_does_not_preserve_unpacked_inputs(self):
        x,y=basis(2,3),basis(1,6)
        self.assertEqual(affine_class(x),affine_class(y))
        self.assertNotEqual(x,y)
        self.assertNotEqual(x.coefficients[0][0].unpack(),y.coefficients[0][0].unpack())

    def test_10_affine_zero_receipts_remain_different_from_empty(self):
        self.assertEqual(affine_class(basis(0,7)),(1,0))
        self.assertEqual(affine_class(basis(4,0)),(1,0))
        self.assertEqual(affine_class(FREE_ZERO),(0,0))
        self.assertNotEqual(affine_class(basis(0,7)),affine_class(FREE_ZERO))
        self.assertNotEqual(basis(0,7),basis(4,0))

    def test_11_strict_quotient_makes_p_bilinear(self):
        vals=(-2,-1,0,1,2)
        for a,aa,b in product(vals,repeat=3):
            self.assertEqual(strict_bilinear_class(bilinear_p_relation(a,aa,b)),0)
            self.assertEqual(strict_bilinear_class(basis(a,b)),a*b)
            self.assertEqual(strict_bilinear_class(basis(a,aa+b)),
                             strict_bilinear_class(basis(a,aa)+basis(a,b)))

    def test_12_strict_quotient_loses_count_and_zero_receipt(self):
        self.assertEqual(strict_bilinear_class(basis(0,5)),0)
        self.assertEqual(strict_bilinear_class(FREE_ZERO),0)
        self.assertEqual(strict_bilinear_class(basis(2,3)),
                         strict_bilinear_class(basis(1,6)))

    def test_13_strict_quotient_of_w_is_numeric_determinant(self):
        for u,v in product((Vector(0,0),Vector(2,3),Vector(-4,1),
                            Vector(Fraction(1,3),Fraction(2,5))),repeat=2):
            self.assertEqual(strict_bilinear_class(raw_wedge(u,v)),area(u,v))

    def test_14_affine_normal_form_preserves_quotient_not_raw_records(self):
        records=(basis(0,0),basis(1,1),basis(2,3),basis(-2,3),basis(1,6))
        for coeff in product((-2,-1,0,1,2),repeat=3):
            x=sum((c*records[i+2] for i,c in enumerate(coeff)),FREE_ZERO)
            normal=affine_normal_form(x)
            self.assertEqual(affine_class(normal),affine_class(x))
        self.assertNotEqual(affine_normal_form(basis(2,3)),basis(2,3))

    def test_15_relations_for_w_bilinearity_have_zero_affine_class(self):
        values=(-2,-1,0,1,2,Fraction(1,3))
        for a,b in product(values,repeat=2):
            self.assertEqual(affine_class(universal_affine_relation(a,b)),(0,0))

    def test_16_w_bilinearity_does_not_force_p_bilinearity(self):
        defect=bilinear_p_relation(1,2,3)
        self.assertEqual(affine_class(defect),(-1,0))
        self.assertEqual(strict_bilinear_class(defect),0)
        self.assertNotEqual(affine_class(defect),(0,0))

    def test_17_finite_grid_w_relation_rank_23_dim_two(self):
        n,r,s=finite_presentation_ranks()
        self.assertEqual((n,r,n-r),(25,23,2))
        self.assertEqual((s,n-s),(24,1))

    def test_18_other_grids_verify_dimension_independent_of_grid_size(self):
        for labels in ((0,1),(-1,0,1),(-2,-1,0,1,2)):
            n,r,s=finite_presentation_ranks(labels)
            self.assertEqual((n-r,n-s),(2,1))
        with self.assertRaises(ValueError):finite_presentation_ranks((0,0,1))

    def test_19_count_difference_can_survive_with_same_product_total(self):
        x=basis(0,2)
        y=basis(0,3)+basis(0,4)
        self.assertEqual(strict_bilinear_class(x),strict_bilinear_class(y))
        self.assertNotEqual(affine_class(x),affine_class(y))

    def test_20_augmentation_is_homogeneous_but_receipt_scaling_is_not(self):
        x=basis(1,2)
        self.assertEqual(affine_class(basis(2,2)),(1,4))
        self.assertEqual(affine_class(2*x),(2,4))
        self.assertNotEqual(affine_class(basis(2,2)),affine_class(2*x))
        self.assertEqual(strict_bilinear_class(basis(2,2)),strict_bilinear_class(2*x))

    def test_21_two_channel_exposes_full_unpacked_pair_without_lie(self):
        x,y=basis(2,3),basis(1,6)
        packet_x=(affine_class(x),x)
        packet_y=(affine_class(y),y)
        self.assertNotEqual(packet_x,packet_y)
        self.assertEqual(packet_x[0],packet_y[0])
        self.assertNotEqual(packet_x[1].coefficients[0][0].unpack(),
                            packet_y[1].coefficients[0][0].unpack())

    def test_22_alternation_alone_does_not_collapse_raw_records(self):
        raw=raw_wedge(Vector(1,0),Vector(0,1))
        self.assertEqual(raw,basis(1,1)-basis(0,0))
        self.assertNotEqual(raw,FREE_ZERO)
        self.assertEqual(raw_wedge(Vector(0,1),Vector(1,0)),-raw)
        self.assertNotEqual(basis(2,3),basis(1,6))

    def test_23_rational_scalars_and_full_history_remain_distinct(self):
        x=basis(Fraction(1,2),6)
        y=basis(1,3)
        self.assertNotEqual(x,y)
        self.assertEqual(affine_class(x),affine_class(y))
        self.assertEqual(strict_bilinear_class(x),Fraction(3))

    def test_24_matrix_rank_rejects_invalid_width(self):
        self.assertEqual(matrix_rank([[1,2],[2,4]],2),1)
        self.assertEqual(matrix_rank([[1,2],[2,4],[0,1]],2),2)
        with self.assertRaises(ValueError):matrix_rank([[1,2,3]],2)


if __name__ == '__main__':
    unittest.main()
