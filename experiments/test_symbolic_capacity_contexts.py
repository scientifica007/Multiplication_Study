"""Independent tests of bounded (H=1..3) and free unbounded contextual equality."""
import unittest
from itertools import combinations, combinations_with_replacement, product
from math import comb
from symbolic_capacity_contexts import (
    ATOMS, A_VALUES, B_VALUES, EMPTY, SourceReceipt, Hist,
    histories_by_length, append_atom, add_hist, direct_profile,
    unlimited_summary, merge_unlimited_summaries, profile_from_unlimited_summary,
    bounded_contextual_quotient, verify_generator_congruence,
    distinguish_by_capacity, summary_classes_on_prefix,
)


def idx(a,b):
    return ATOMS.index(SourceReceipt(a,b))


def hist(*ab_pairs):
    return tuple(sorted(idx(a,b) for a,b in ab_pairs))


class SymbolicCapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.quotients={
            (h,probes):bounded_contextual_quotient(h,source_probes=probes)
            for h in (1,2,3) for probes in (False,True)
        }

    def test_01_atom_receipts_are_ordered_and_recoverable(self):
        self.assertEqual(len(ATOMS),36)
        self.assertEqual(len(set(ATOMS)),36)
        for c in ATOMS:
            self.assertEqual(c.unpack(),(('A',c.a),('B',c.b)))
            self.assertEqual(c.reading,c.a*c.b)
        self.assertNotEqual(SourceReceipt(-1,-6),SourceReceipt(1,6))
        self.assertEqual(SourceReceipt(-1,-6).reading,SourceReceipt(1,6).reading)

    def test_02_combinatorial_counts_for_histories(self):
        for h,count in ((1,37),(2,703),(3,9139)):
            layers=histories_by_length(h)
            self.assertEqual(tuple(len(x) for x in layers),tuple(comb(36+j-1,j) if j else 1 for j in range(h+1)))
            self.assertEqual(sum(map(len,layers)),count)

    def test_03_exact_round17_h2_recovery_with_both_probe_sets(self):
        self.assertEqual(self.quotients[2,True].counts,(1,36,132))
        self.assertEqual(self.quotients[2,True].total,169)
        self.assertEqual(self.quotients[2,False].counts,(1,32,76))
        self.assertEqual(self.quotients[2,False].total,109)

    def test_04_exact_round18_h3_full_counts(self):
        self.assertEqual(self.quotients[3,True].counts,(1,36,241,227))
        self.assertEqual(self.quotients[3,True].total,505)
        self.assertEqual(self.quotients[3,True].state_count,9139)

    def test_05_h3_without_source_guard_counts(self):
        self.assertEqual(self.quotients[3,False].counts,(1,32,105,131))
        self.assertEqual(self.quotients[3,False].total,269)

    def test_06_capacity_one_counts_and_sticky_limit(self):
        for probes in (False,True):
            self.assertEqual(self.quotients[1,probes].counts,(1,20))
            self.assertEqual(self.quotients[1,probes].total,21)

    def test_07_independent_generator_congruence_for_all_models(self):
        for quotient in self.quotients.values():
            self.assertTrue(verify_generator_congruence(quotient))

    def test_08_probes_separate_all_nonzero_primary_factors_at_h_ge_2(self):
        for h in (2,3):
            q=self.quotients[h,True]
            singles=q.layers[1]
            self.assertEqual(len({q.block[x] for x in singles}),36)
            # Independent one-atom witness, using ONLY direct observable guards.
            for x,y in combinations(singles,2):
                if direct_profile(x)==direct_profile(y):
                    self.assertTrue(any(direct_profile(add_hist(x,(i,)))!=
                                        direct_profile(add_hist(y,(i,)))
                                        for i in range(36)))

    def test_09_without_homogeneity_probes_32_singleton_classes_stabilize(self):
        for h in (2,3):
            self.assertEqual(len({self.quotients[h,False].block[x]
                                  for x in self.quotients[h,False].layers[1]}),32)

    def test_10_bounded_capacity_makes_length_observable_even_when_free_Q_same(self):
        x=hist((1,6),(2,-3))
        y=hist((1,2),(1,2),(2,-2))
        self.assertEqual(unlimited_summary(x),unlimited_summary(y))
        self.assertNotEqual(self.quotients[3,True].block[x],self.quotients[3,True].block[y])
        self.assertEqual(distinguish_by_capacity(x,y,3),(0,))
        self.assertIsNotNone(append_atom(x,0,capacity=3))
        self.assertIsNone(append_atom(y,0,capacity=3))

    def test_11_saturated_bounded_equivalence_but_free_Q_distinguishes(self):
        x=hist((3,2),(3,2),(3,2))
        y=hist((-3,-2),(-3,-2),(-3,-2))
        self.assertEqual(direct_profile(x),direct_profile(y))
        self.assertEqual(self.quotients[3,True].block[x],self.quotients[3,True].block[y])
        self.assertNotEqual(unlimited_summary(x),unlimited_summary(y))
        z=(idx(3,2),)
        self.assertNotEqual(direct_profile(add_hist(x,z)),direct_profile(add_hist(y,z)))
        self.assertIsNone(add_hist(x,z,capacity=3))
        self.assertIsNone(add_hist(y,z,capacity=3))

    def test_12_h2_same_saturated_pair_separated_after_h3_extension(self):
        x=hist((3,2),(3,2))
        y=hist((-3,-2),(-3,-2))
        self.assertTrue(self.quotients[2,True].same(x,y))
        self.assertFalse(self.quotients[3,True].same(x,y))
        z=(idx(3,2),)
        self.assertNotEqual(direct_profile(add_hist(x,z)),direct_profile(add_hist(y,z)))

    def test_13_singletons_can_be_equal_at_h1_but_not_h2(self):
        x=hist((3,2));y=hist((-3,-2))
        self.assertTrue(self.quotients[1,True].same(x,y))
        self.assertFalse(self.quotients[2,True].same(x,y))

    def test_14_full_layer_quotient_is_exactly_direct_observation(self):
        for h in (1,2,3):
            for source_probes in (False,True):
                q=self.quotients[h,source_probes]
                bykey={};byclass={}
                for x in q.layers[h]:
                    key=direct_profile(x,source_probes=source_probes)
                    bykey.setdefault(key,set()).add(q.block[x])
                    byclass.setdefault(q.block[x],set()).add(key)
                self.assertTrue(all(len(s)==1 for s in bykey.values()))
                self.assertTrue(all(len(s)==1 for s in byclass.values()))

    def test_15_h3_two_term_class_oracle_by_one_future_observation(self):
        q=self.quotients[3,True]
        bykey={};byclass={}
        for x in q.layers[2]:
            key=(direct_profile(x),tuple(direct_profile(append_atom(x,i))
                                         for i in range(36)))
            bykey.setdefault(key,set()).add(q.block[x])
            byclass.setdefault(q.block[x],set()).add(key)
        self.assertEqual(len(bykey),241)
        self.assertTrue(all(len(s)==1 for s in bykey.values()))
        self.assertTrue(all(len(s)==1 for s in byclass.values()))

    def test_16_unbounded_summary_is_additive_for_all_atom_extensions(self):
        layers=histories_by_length(3)
        for layer in layers:
            for x in layer:
                q=unlimited_summary(x)
                self.assertEqual(profile_from_unlimited_summary(q),direct_profile(x))
                for j in range(36):
                    nxt=add_hist(x,(j,))
                    self.assertEqual(unlimited_summary(nxt),
                                     merge_unlimited_summaries(q,unlimited_summary((j,))))

    def test_17_unbounded_Q_is_minimal_on_a_84_history_sample(self):
        ids=(idx(-1,-2),idx(-1,2),idx(1,-2),idx(1,2),idx(2,-3),idx(2,3))
        sample=(EMPTY,)+tuple(tuple(sorted(x)) for n in (1,2,3)
                               for x in combinations_with_replacement(ids,n))
        self.assertEqual(len(sample),84)
        for x,y in combinations(sample,2):
            qx,qy=unlimited_summary(x),unlimited_summary(y)
            if qx==qy:
                self.assertEqual(direct_profile(x),direct_profile(y))
                self.assertTrue(all(direct_profile(add_hist(x,(i,)))==
                                    direct_profile(add_hist(y,(i,))) for i in range(36)))
            else:
                self.assertTrue(direct_profile(x)!=direct_profile(y) or
                                any(direct_profile(add_hist(x,(i,)))!=
                                    direct_profile(add_hist(y,(i,))) for i in range(36)))

    def test_18_unbounded_Q_classes_on_truncated_samples(self):
        self.assertEqual(tuple(summary_classes_on_prefix(h) for h in (1,2,3)),
                         (37,278,542))

    def test_19_all_distinctions_with_same_length_follow_unbounded_Q(self):
        q=self.quotients[3,True]
        groups={}
        for layer in q.layers:
            for x in layer:
                groups.setdefault((len(x),unlimited_summary(x)),set()).add(q.block[x])
        self.assertTrue(all(len(v)==1 for v in groups.values()))

    def test_20_invalid_capacity_or_atom_and_commutative_addition(self):
        with self.assertRaises(ValueError):histories_by_length(-1)
        with self.assertRaises(ValueError):append_atom(EMPTY,36)
        a=hist((1,6));b=hist((-3,-2))
        self.assertEqual(add_hist(a,b),add_hist(b,a))
        self.assertIsNone(add_hist(a,b,capacity=1))
        self.assertNotEqual(add_hist(a,b,capacity=2),None)

if __name__=='__main__':unittest.main()
