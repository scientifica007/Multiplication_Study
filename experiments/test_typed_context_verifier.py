"""Independent checks: exact quotients, shortest witnesses, and typed partiality."""
import unittest
from itertools import combinations, product
from typed_context_verifier import (
    Value, Operation, FiniteSortedAlgebra, build_product_model, c_receipt,
    initial_partition, refine_partition, quotient_counts, verify_candidate,
    shortest_witness,
)


class FiniteManySortedVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = build_product_model(False)
        cls.public_blocks, cls.public_rounds = refine_partition(cls.public)
        cls.full = build_product_model(True)
        cls.full_blocks, cls.full_rounds = refine_partition(cls.full)

    def test_01_complete_typed_receipts_and_distinct_sorts(self):
        m = self.public
        self.assertEqual({s: len(v) for s, v in m.sorts.items()},
                         {'A': 6, 'B': 6, 'C': 36, 'D': 2, 'E': 36, 'F': 1, 'G': 4})
        self.assertEqual(len(set(m.elements)),len(m.elements))
        for c in m.sorts['C']:
            a,b=c.inputs
            self.assertEqual((a.sort,b.sort),('A','B'))
            self.assertEqual(c.amount,a.amount*b.amount)
            self.assertEqual(m.apply('multiply_AB',(a,b)),c)
        for e in m.sorts['E']:
            c,d=e.inputs
            self.assertEqual((c.sort,d.sort),('C','D'))
            self.assertEqual(e.amount,c.amount*d.amount)
            self.assertEqual(m.apply('multiply_CD',(c,d)),e)
        for g in m.sorts['G']:
            e,f=g.inputs
            self.assertEqual((e.sort,f.sort),('E','F'))
            self.assertEqual(m.apply('multiply_EF',(e,f)),g)

    def test_02_public_coarsest_strong_congruence_exact_counts(self):
        m=self.public
        self.assertEqual(quotient_counts(m,self.public_blocks),
                         {'A': 6, 'B': 6, 'C': 20, 'D': 2, 'E': 16, 'F': 1, 'G': 4})
        self.assertEqual(self.public_rounds,2)
        self.assertIsNone(verify_candidate(m,lambda x:self.public_blocks[x]))

    def test_03_full_unpacking_increases_c_classes_to_36(self):
        m=self.full
        self.assertEqual(quotient_counts(m,self.full_blocks),
                         {'A': 6, 'B': 6, 'C': 36, 'D': 2, 'E': 36, 'F': 1, 'G': 4})
        self.assertIsNone(verify_candidate(m,lambda x:self.full_blocks[x]))
        self.assertEqual(m.apply('unpack_C_left',(c_receipt(m,1,6),)).amount,1)
        self.assertEqual(m.apply('unpack_C_right',(c_receipt(m,1,6),)).amount,6)

    def test_04_measurement_alone_fails_under_partial_guards(self):
        m=self.public
        violation=verify_candidate(m,lambda x:x.amount)
        self.assertIsNotNone(violation)
        self.assertIn(violation.kind,('definedness','output-class'))
        a,b=c_receipt(m,1,6),c_receipt(m,2,3)
        self.assertEqual(a.amount,b.amount)
        witness=shortest_witness(m,a,b)
        self.assertEqual(witness.kind,'definedness')
        self.assertEqual(len(witness.steps),1)
        self.assertIn('multiply_CD',witness.steps[0].describe())

    def test_05_direct_one_step_looks_equal_but_two_steps_distinguish(self):
        m=self.public
        a,b=c_receipt(m,1,6),c_receipt(m,3,2)
        self.assertEqual(a.amount,b.amount)
        for hole in m.contexts['C']:
            x,y=m.apply_hole(hole,a),m.apply_hole(hole,b)
            self.assertEqual(x is None,y is None)
            if x is not None:
                self.assertEqual(x.amount,y.amount)
        witness=shortest_witness(m,a,b)
        self.assertEqual(witness.kind,'definedness')
        self.assertEqual(len(witness.steps),2)
        self.assertEqual([h.operation for h in witness.steps],
                         ['multiply_CD','multiply_EF'])
        self.assertNotEqual(self.public_blocks[a],self.public_blocks[b])

    def test_06_full_unpack_shortens_the_witness_to_one_step(self):
        m=self.full
        a,b=c_receipt(m,1,6),c_receipt(m,3,2)
        witness=shortest_witness(m,a,b)
        self.assertEqual(witness.kind,'observation')
        self.assertEqual(len(witness.steps),1)
        self.assertEqual(witness.steps[0].operation,'unpack_C_left')

    def test_07_all_630_c_pairs_bfs_match_partition_both_modes(self):
        for m,blocks in ((self.public,self.public_blocks), (self.full,self.full_blocks)):
            seen=0
            for a,b in combinations(m.sorts['C'],2):
                self.assertEqual(shortest_witness(m,a,b) is None,
                                 blocks[a]==blocks[b],(a.name,b.name))
                seen+=1
            self.assertEqual(seen,630)

    def test_08_strong_congruence_checked_by_all_one_hole_contexts(self):
        m=self.public
        blocks=self.public_blocks
        for s,values in m.sorts.items():
            for x,y in combinations(values,2):
                if blocks[x]!=blocks[y]:
                    continue
                for hole in m.contexts[s]:
                    ax,by=m.apply_hole(hole,x),m.apply_hole(hole,y)
                    self.assertEqual(ax is None,by is None)
                    if ax is not None:
                        self.assertEqual(blocks[ax],blocks[by])

    def test_09_specific_output_class_mismatch_even_when_both_defined(self):
        x=Value('X','x',0);y=Value('X','y',0)
        t=Value('T','t',0)
        u=Value('U','u',1);v=Value('U','v',2)
        op=Operation('f',('X','T'),'U',{(x,t):u,(y,t):v})
        m=FiniteSortedAlgebra({'X':(x,y),'T':(t,),'U':(u,v)},(op,),lambda z:z.amount)
        fault=verify_candidate(m,lambda z:z.amount)
        self.assertEqual(fault.kind,'output-class')
        w=shortest_witness(m,x,y)
        self.assertEqual(w.kind,'observation')
        self.assertEqual(len(w.steps),1)
        self.assertEqual(w.steps[0].position,0)

    def test_10_hole_can_be_in_the_right_operand_position(self):
        x=Value('X','x',0);y=Value('X','y',0)
        t=Value('T','t',0)
        u=Value('U','u',1)
        op=Operation('f',('T','X'),'U',{(t,x):u})
        m=FiniteSortedAlgebra({'T':(t,),'X':(x,y),'U':(u,)},(op,),lambda z:z.amount)
        fault=verify_candidate(m,lambda z:z.amount)
        self.assertEqual(fault.kind,'definedness')
        self.assertEqual(fault.steps[0].position,1)
        self.assertEqual(fault.steps[0].describe(),'f(t, □)')
        w=shortest_witness(m,x,y)
        self.assertEqual(len(w.steps),1)

    def test_11_same_output_reading_but_different_complete_input_records(self):
        m=self.public
        a,b=c_receipt(m,-1,-6),c_receipt(m,1,6)
        self.assertEqual(a.amount,b.amount)
        self.assertNotEqual(a.inputs,b.inputs)
        self.assertNotEqual(a,b)
        self.assertIsNotNone(shortest_witness(m,a,b))
        self.assertEqual(len(shortest_witness(m,a,b).steps),2)

    def test_12_type_validation_and_bad_partitions(self):
        m=self.public
        a=m.sorts['A'][0];d=m.sorts['D'][0]
        with self.assertRaises(ValueError):m.apply('multiply_AB',(a,d))
        with self.assertRaises(ValueError):shortest_witness(m,a,d)
        with self.assertRaises(ValueError):refine_partition(m,{a:0})
        with self.assertRaises(ValueError):FiniteSortedAlgebra(
            {'A': (a,)},(Operation('oops',('A',),'B',{}),),lambda x:x.amount)

    def test_13_identity_quotient_safe_but_larger_than_observational_minimum(self):
        m=self.public
        self.assertIsNone(verify_candidate(m,lambda x:x))
        self.assertEqual(len(set(m.sorts['C'])),36)
        self.assertLess(len({self.public_blocks[x] for x in m.sorts['C']}),36)
        self.assertEqual(len({x.amount for x in m.sorts['C']}),14)

    def test_14_primitive_context_positions_and_no_false_domain_zero(self):
        m=self.public
        c=c_receipt(m,1,6)
        d=m.sorts['D'][0]
        e=m.apply('multiply_CD',(c,d))
        self.assertIsNotNone(e)
        f=m.sorts['F'][0]
        self.assertIsNotNone(m.apply('multiply_EF',(e,f)))
        self.assertIsNone(m.apply('multiply_CD',(c,m.sorts['D'][1])))
        # None means forbidden; no numeric zero was manufactured.
        self.assertTrue(all(0 != val.amount for val in m.sorts['C']))


if __name__=='__main__':
    unittest.main()
