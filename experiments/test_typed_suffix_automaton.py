"""Independent finite checks for contextual-state theorems G1-G4."""
import unittest
from itertools import product
from typed_suffix_automaton import (
    State, initial, step, observe_word, can_test, output, reachable,
    minimal_partition, refine_partial, predicted_full, predicted_guard_only,
    shortest_distinguishing_continuation,
)


class TypedSuffixTests(unittest.TestCase):
    def test_all_reachable_and_formula(self):
        for m,h in product(range(1,7),range(1,5)):
            states = reachable(m,h)
            self.assertEqual(len(states),predicted_full(m,h))
            full = minimal_partition(m,h,True)
            self.assertEqual(len(set(full.values())),len(states))
            guard = minimal_partition(m,h,False)
            self.assertEqual(len(set(guard.values())),predicted_guard_only(m,h))

    def test_concrete_m3_h2(self):
        self.assertEqual(len(reachable(3,2)),18)
        self.assertEqual(len(set(minimal_partition(3,2).values())),10)
        self.assertEqual(predicted_full(3,2),18)
        self.assertEqual(predicted_guard_only(3,2),10)

    def test_full_negative_residue_can_be_forgotten(self):
        x=observe_word('-++',3,2)
        y=observe_word('-+++',3,2)
        self.assertNotEqual(x.residue,y.residue)
        self.assertEqual(x.suffix,y.suffix)
        self.assertTrue(x.negative_ever and y.negative_ever)
        self.assertIsNone(shortest_distinguishing_continuation(x,y,3,2))
        self.assertEqual(minimal_partition(3,2)[x],minimal_partition(3,2)[y])
        self.assertEqual(shortest_distinguishing_continuation(x,y,3,2,True),'')

    def test_guard_current_same_future_different(self):
        x=observe_word('++',3,2)
        y=observe_word('++++',3,2)
        self.assertEqual(output(x),output(y))
        self.assertFalse(can_test(x))
        self.assertFalse(can_test(y))
        witness=shortest_distinguishing_continuation(x,y,3,2)
        self.assertEqual(witness,'+')
        self.assertNotEqual(output(step(x,witness,3,2)),output(step(y,witness,3,2)))

    def test_commutative_aggregation_erases_event_order(self):
        x,y='+-','-+'
        self.assertEqual(sum(1 if c=='+' else -1 for c in x),
                         sum(1 if c=='+' else -1 for c in y))
        self.assertEqual({c:x.count(c) for c in '+-'},
                         {c:y.count(c) for c in '+-'})
        self.assertNotEqual(observe_word(x,3,1).suffix,observe_word(y,3,1).suffix)

    def test_partition_matches_pairwise_future_distinguishability(self):
        for m,h in ((2,1),(3,2),(3,3)):
            states=reachable(m,h)
            for expose in (False,True):
                classes=minimal_partition(m,h,expose)
                for i,s in enumerate(states):
                    for t in states[i:]:
                        witness=shortest_distinguishing_continuation(s,t,m,h,expose)
                        self.assertEqual(classes[s]==classes[t],witness is None)

    def test_general_partial_transition_refinement(self):
        states = ('enabled', 'blocked', 'also_blocked')
        def transition(state, letter):
            if state == 'enabled' and letter == 'check':
                return 'blocked'
            return None
        colors = refine_partial(states, ('check',), transition, lambda state: 'same')
        self.assertNotEqual(colors['enabled'], colors['blocked'])
        self.assertEqual(colors['blocked'], colors['also_blocked'])
        with self.assertRaises(ValueError):
            refine_partial(states, ('check',), lambda st,a:'outside', lambda st:'same')

    def test_event_validation_and_empty(self):
        self.assertEqual(observe_word('',3,2),initial())
        with self.assertRaises(ValueError): step(initial(),'0',3,2)
        with self.assertRaises(ValueError): reachable(0,2)
        with self.assertRaises(ValueError): reachable(3,0)


if __name__ == '__main__': unittest.main()
