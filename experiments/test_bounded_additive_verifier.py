"""End-to-end, independent tests for the capacity-two many-sorted C addition."""
import unittest
from itertools import combinations, product
from collections import defaultdict
from bounded_additive_verifier import Model, summarize, V, previous_verifier_adapter


class BoundedAdditiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=Model()
        cls.blocks,cls.rounds=cls.m.refine_fast()

    def test_01_exact_universe_and_full_nested_inputs(self):
        m=self.m
        self.assertEqual({s:len(t) for s,t in m.sorts.items()},
                         {'A':6,'B':6,'C':703,'D':4,'E':438,'F':1,'G':14})
        self.assertEqual(len(m.all),1172)
        self.assertEqual(len(set(m.atoms)),36)
        self.assertEqual(len(m.doubles),666)
        for c in m.atoms:
            a,b=c.inputs
            self.assertEqual((a.sort,b.sort),('A','B'))
            self.assertEqual(a.amount*b.amount,c.amount)
            self.assertEqual(m.byname['mul_AB'].table[(a,b)],c)

    def test_02_sums_are_bounded_commutative_and_have_identity(self):
        m=self.m
        self.assertEqual(len(m.byname['add_CC'].table),2701)
        for x,y in product(m.C,repeat=2):
            self.assertEqual(m.sum(x,y),m.sum(y,x))
            self.assertEqual(m.sum(x,m.empty),x)
        for a,b,c in product(m.atoms[:3],repeat=3):
            self.assertIsNone(m.sum(m.sum(a,b),c))
            self.assertIsNone(m.sum(a,m.sum(b,c)))
        for a in m.atoms:
            self.assertIsNotNone(m.sum(a,a))
            self.assertNotEqual(a,m.sum(a,a))

    def test_03_refined_exact_quotient_counts(self):
        self.assertEqual(summarize(self.m,self.blocks),
                         {'A':6,'B':6,'C':169,'D':4,'E':90,'F':1,'G':11})
        self.assertEqual(self.rounds,2)
        self.assertEqual(len(set(self.blocks.values())),287)

    def test_04_legacy_20_becomes_36_for_original_36_receipts(self):
        m=self.m
        self.assertEqual(len({m.old_key(c) for c in m.atoms}),20)
        self.assertEqual(len({self.blocks[c] for c in m.atoms}),36)
        self.assertEqual(len({c.amount for c in m.atoms}),14)

    def test_05_double_summary_analytical_oracle(self):
        m=self.m
        self.assertEqual(len({m.semantic_double_key(c) for c in m.doubles}),132)
        groups=defaultdict(set)
        reversed_groups=defaultdict(set)
        for x in m.C:
            groups[m.public_key(x)].add(self.blocks[x])
            reversed_groups[self.blocks[x]].add(m.public_key(x))
        self.assertEqual(len(groups),169)
        self.assertTrue(all(len(s)==1 for s in groups.values()))
        self.assertTrue(all(len(s)==1 for s in reversed_groups.values()))

    def test_06_full_unpruned_contexts_preserve_the_result(self):
        self.assertIsNone(self.m.valid_for_all_contexts(self.blocks))

    def test_07_reduced_alphabet_equals_generic_full_alphabet_on_small_model(self):
        small=Model(small=True)
        br,_=small.refine_fast(True)
        bf,_=small.refine_fast(False)
        self.assertEqual(summarize(small,br),summarize(small,bf))
        for x,y in product(small.all,repeat=2):
            self.assertEqual(br[x]==br[y],bf[x]==bf[y])
        self.assertIsNone(small.valid_for_all_contexts(br))

    def test_08_old_equivalent_pair_separated_by_add_then_probe(self):
        m=self.m
        x,y,z=m.atom(3,2),m.atom(-3,-2),m.atom(3,2)
        self.assertEqual(m.old_key(x),m.old_key(y))
        self.assertNotEqual(self.blocks[x],self.blocks[y])
        self.assertEqual(x.amount,y.amount)
        xx,yy=m.sum(x,z),m.sum(y,z)
        self.assertEqual(xx.amount,yy.amount)
        d=next(d for d in m.D if d.name=='homA')
        p=m.byname['mul_CD'].table
        self.assertIsNotNone(p.get((xx,d)))
        self.assertIsNone(p.get((yy,d)))
        w=m.witness(x,y)
        self.assertIsNotNone(w)
        self.assertEqual(len(w.steps),2)
        self.assertEqual([h.op for h in w.steps],['add_CC','mul_CD'])
        self.assertEqual(w.kind,'definedness')

    def test_09_atomic_shortest_witness_corresponds_to_all_630_pairs(self):
        m=self.m
        for x,y in combinations(m.atoms,2):
            w=m.witness(x,y)
            self.assertEqual(w is None,self.blocks[x]==self.blocks[y])
            self.assertIsNotNone(w)
            self.assertLessEqual(len(w.steps),2)

    def test_10_measurement_zero_is_not_empty_sum(self):
        m=self.m
        zero=m.sum(m.atom(1,2),m.atom(1,-2))
        self.assertEqual(zero.amount,m.empty.amount)
        self.assertNotEqual(zero,m.empty)
        self.assertNotEqual(self.blocks[zero],self.blocks[m.empty])
        self.assertEqual(len(m.terms[zero]),2)
        self.assertEqual(len(m.terms[m.empty]),0)
        seal=next(d for d in m.D if d.name=='seal')
        self.assertIsNotNone(m.byname['mul_CD'].table.get((zero,seal)))
        self.assertIsNone(m.byname['mul_CD'].table.get((m.empty,seal)))

    def test_11_raw_provenance_retained_in_every_nested_product(self):
        m=self.m
        for e in m.E:
            c,d=e.inputs
            self.assertEqual((c.sort,d.sort),('C','D'))
            self.assertEqual(e.amount,c.amount*d.amount)
            for atom in m.terms[c]:
                a,b=atom.inputs
                self.assertEqual((a.sort,b.sort),('A','B'))
        for g in m.G:
            e,f=g.inputs
            self.assertEqual((e.sort,f.sort),('E','F'))
            self.assertEqual(g.amount,e.amount*f.amount)
            self.assertIn(e,m.E)

    def test_12_capacity_artifact_and_distinct_double_multisets(self):
        m=self.m
        p=m.atom(1,2)
        a=m.sum(p,p)
        self.assertIsNone(m.sum(a,p))
        self.assertIsNotNone(m.sum(p,p))
        self.assertNotEqual(m.sum(p,p),m.sum(p,m.atom(1,-2)))
        self.assertEqual(m.sum(p,p),m.sum(p,p))
        self.assertIsNotNone(m.sum(a,m.empty))

    def test_13_base_partial_guards_restricted_to_atoms_unchanged(self):
        m=self.m
        byname={d.name:d for d in m.D}
        for x in m.atoms:
            a,b=(z.amount for z in x.inputs)
            self.assertEqual((x,byname['seal']) in m.byname['mul_CD'].table,b%2==0)
            self.assertEqual((x,byname['inspect']) in m.byname['mul_CD'].table,a%2==0)
            self.assertTrue((x,byname['homA']) in m.byname['mul_CD'].table)
            self.assertTrue((x,byname['homB']) in m.byname['mul_CD'].table)

    def test_14_right_operand_and_output_reading_semantics(self):
        m=self.m
        for d in m.D:
            seen=0
            for c in m.C:
                e=m.byname['mul_CD'].table.get((c,d))
                if e:
                    seen+=1
                    self.assertEqual(e.amount,c.amount*d.amount)
            self.assertGreater(seen,0)
        self.assertEqual(m.byname['mul_AB'].table.get((m.A[0],m.B[0])).sort,'C')

    def test_15_source_probe_control_isolation(self):
        m=Model(include_source_probes=False)
        classes,rounds=m.refine_fast()
        self.assertEqual(summarize(m,classes),
                         {'A':6,'B':6,'C':109,'D':2,'E':32,'F':1,'G':11})
        self.assertEqual(len({classes[x] for x in m.atoms}),32)
        self.assertEqual(len({m.old_key(x) for x in m.atoms}),20)
        self.assertEqual(len(m.all),846)
        self.assertIsNone(m.valid_for_all_contexts(classes))

    def test_16_small_model_integrates_with_round16_generic_verifier(self):
        from typed_context_verifier import refine_partition
        small=Model(small=True)
        generic=previous_verifier_adapter(small)
        generic_partition,_=refine_partition(generic)
        optimized_partition,_=small.refine_fast()
        for x,y in product(small.all,repeat=2):
            self.assertEqual(generic_partition[x]==generic_partition[y],
                             optimized_partition[x]==optimized_partition[y])

    def test_17_all_703_c_pairs_are_not_just_the_same_numbers(self):
        m=self.m
        self.assertLess(len({x.amount for x in m.C}),169)
        self.assertLess(169,703)
        q=defaultdict(list)
        for x in m.C:q[self.blocks[x]].append(x)
        self.assertEqual(sum(map(len,q.values())),703)
        self.assertTrue(any(len(v)>1 for v in q.values()))

if __name__=='__main__':unittest.main()
