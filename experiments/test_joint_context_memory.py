"""Bounded independent validation of the exact joint-memory formulas J1-J4."""
import unittest
from itertools import combinations, permutations, product
from math import factorial

from joint_context_memory import (
    empty, parameters, advance, run, guard, reachable, partition,
    predicted_counts, balanced_code, decode_balanced, order_rank,
    order_unrank, window_from_code, minimal_key
)


class JointContextTests(unittest.TestCase):
    def test_counts_and_context_minimization(self):
        for N, h, m in ((2,1,1),(2,1,3),(3,1,3),(3,2,1),
                        (3,2,2),(3,2,3),(4,2,2),(4,3,2)):
            states = reachable(N,h,m)
            full, contextual = predicted_counts(N,h,m)
            self.assertEqual(len(states), full, (N,h,m))
            full_partition = partition(N,h,m,True)
            min_partition = partition(N,h,m,False)
            self.assertEqual(len(set(full_partition.values())),full)
            self.assertEqual(len(set(min_partition.values())),contextual)
            keys = {s:minimal_key(s,h) for s in states}
            self.assertEqual(len(set(keys.values())),contextual)
            for i,a in enumerate(states):
                for b in states[i:]:
                    self.assertEqual(keys[a]==keys[b],
                                     min_partition[a]==min_partition[b])

    def test_concrete_three_labels(self):
        self.assertEqual(predicted_counts(3,2,3),(97,49))
        self.assertEqual(len(set(partition(3,2,3).values())),49)

    def test_signed_encoding_and_chronological_permutation(self):
        N=5
        for size in range(5):
            for labels in combinations(range(N),size):
                for signs in product((-1,1),repeat=size):
                    sorted_events = tuple(zip(labels,signs))
                    code = balanced_code(sorted_events)
                    self.assertEqual(decode_balanced(code,N),sorted_events)
                    seen = set()
                    for order in permutations(sorted_events):
                        rank = order_rank(order)
                        self.assertNotIn(rank,seen)
                        seen.add(rank)
                        self.assertEqual(window_from_code(code,rank,N),order)
                    self.assertEqual(len(seen),factorial(size))

    def test_bare_signed_integer_erases_order(self):
        x=((0,1),(2,-1))
        y=x[::-1]
        self.assertEqual(balanced_code(x),-8)
        self.assertEqual(balanced_code(x),balanced_code(y))
        self.assertNotEqual(order_rank(x),order_rank(y))

    def test_expired_negative_changes_legal_future(self):
        N,h,m=3,2,3
        positive_prefix = run(((2,1),(0,1),(1,1)),N,h,m)
        negative_prefix = run(((2,-1),(0,1),(1,1)),N,h,m)
        self.assertEqual(positive_prefix.window,negative_prefix.window)
        self.assertTrue(guard(positive_prefix))
        self.assertFalse(guard(negative_prefix))
        self.assertNotEqual(minimal_key(positive_prefix,h),
                            minimal_key(negative_prefix,h))
        states=reachable(N,h,m)
        closed=[s for s in states if s.window==positive_prefix.window and s.ever_negative]
        self.assertEqual(len(closed),m)
        self.assertEqual(len({minimal_key(s,h) for s in closed}),1)

    def test_partial_legal_label_transitions(self):
        N,h,m=3,2,3
        s=run(((0,1),(1,-1)),N,h,m)
        self.assertIsNone(advance(s,(1,1),N,h,m))
        self.assertIsNotNone(advance(s,(0,1),N,h,m))
        self.assertEqual(len(run(((0,1),),N,h,m).window),1)
        with self.assertRaises(ValueError):
            run(((0,1),(0,-1)),N,h,m)
        with self.assertRaises(ValueError):
            advance(empty(),(1,0),N,h,m)
        with self.assertRaises(ValueError):
            parameters(2,2,3)

    def test_future_positive_events_distinguish_open_residues(self):
        N,h,m=3,2,3
        states=reachable(N,h,m)
        suffix=((0,1),(1,1))
        opens=[s for s in states if s.window==suffix and not s.ever_negative]
        self.assertEqual(len(opens),m)
        for s in opens:
            for k in range(m):
                t=s
                for _ in range(k):
                    available=next(a for a in range(N)
                                   if a not in {label for label,n in t.window[1:]})
                    t=advance(t,(available,1),N,h,m)
                self.assertEqual(guard(t),(s.residue+k)%m==0)


if __name__=='__main__':
    unittest.main()
