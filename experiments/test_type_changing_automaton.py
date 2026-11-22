"""Independent model checker and provenance tests for typed state transitions."""
import unittest
from itertools import combinations
from type_changing_automaton import (
    Control, Command, initial, transition, typed_step, unpack, reachable,
    period_subgroup, predicted_class_count, minimization, shortest_witness,
    stage_partition,
)


class TypedTransitionChecks(unittest.TestCase):
    def test_noncoset_witness_at_modulus_four(self):
        m,D=4,frozenset((0,1))
        self.assertEqual(len(reachable(m,D)),12)
        self.assertEqual(len(set(minimization(m,D).values())),10)
        self.assertEqual(stage_partition(m,D,'Held'),((0,1),(2,3)))
        self.assertEqual(stage_partition(m,D,'Active'),((0,),(1,),(2,),(3,)))
        self.assertEqual(stage_partition(m,D,'Released'),((0,),(1,),(2,),(3,)))
        self.assertEqual(period_subgroup(m,D),(0,))
        self.assertIsNone(shortest_witness(Control('Held',0),Control('Held',1),m,D))
        self.assertEqual(shortest_witness(Control('Held',1),Control('Held',2),m,D),('release',))
        self.assertIsNone(shortest_witness(Control('Held',2),Control('Held',3),m,D))

    def test_restore_tick_recovers_coset_partition(self):
        m,D=4,frozenset((0,1))
        self.assertEqual(stage_partition(m,D,'Held',True),((0,),(1,),(2,),(3,)))
        self.assertEqual(len(set(minimization(m,D,True).values())),12)
        self.assertIsNotNone(shortest_witness(Control('Held',0),Control('Held',1),m,D,True))
        self.assertEqual(stage_partition(4,frozenset((0,2)),'Held',True),((0,2),(1,3)))

    def test_all_domains_up_to_modulus_seven(self):
        for m in range(1,8):
            for mask in range(1<<m):
                D=frozenset(x for x in range(m) if mask>>x & 1)
                for optional_tick in (False, True):
                    states=reachable(m,D,optional_tick)
                    blocks=minimization(m,D,optional_tick)
                    self.assertEqual(len(set(blocks.values())),
                                     predicted_class_count(m,D,optional_tick),
                                     (m,D,optional_tick))
                    self.assertEqual(len(states),3*m if D else 2*m)

    def test_pairwise_witness_matches_quotient(self):
        for m in range(1,6):
            for mask in range(1<<m):
                D=frozenset(i for i in range(m) if mask>>i & 1)
                for optional_tick in (False,True):
                    blocks=minimization(m,D,optional_tick)
                    for s,t in combinations(blocks,2):
                        self.assertEqual(blocks[s]==blocks[t],
                                         shortest_witness(s,t,m,D,optional_tick) is None)

    def test_type_change_with_loss_of_shift(self):
        m,D=4,frozenset((0,1))
        a=Control('Active',0)
        h=transition(a,'freeze',m,D)
        self.assertEqual(h,Control('Held',0))
        self.assertIsNone(transition(h,'tick',m,D))
        r=transition(h,'release',m,D)
        self.assertEqual(r,Control('Released',0))
        self.assertEqual(transition(r,'tick',m,D),Control('Released',1))
        self.assertIsNone(transition(r,'freeze',m,D))
        self.assertIsNone(transition(Control('Released',1),'check',m,D))
        self.assertEqual(transition(r,'check',m,D),r)

    def test_full_provenance_retained_by_typed_records(self):
        m,D=4,frozenset((0,1))
        root=initial()
        state=root
        for _ in range(4):
            nxt=typed_step(state,Command('tick'),m,D)
            self.assertEqual(unpack(nxt),(state,Command('tick')))
            state=nxt
        self.assertEqual(root.control,state.control)
        self.assertNotEqual(root,state)
        frozen=typed_step(state,Command('freeze'),m,D)
        self.assertEqual(frozen.control.stage,'Held')
        self.assertEqual(unpack(frozen),(state,Command('freeze')))
        released=typed_step(frozen,Command('release'),m,D)
        self.assertEqual(released.control,Control('Released',0))
        self.assertEqual(unpack(released),(frozen,Command('release')))
        self.assertIsNone(typed_step(frozen,Command('tick'),m,D))
        with self.assertRaises(ValueError):unpack(root)
        with self.assertRaises(TypeError):typed_step(root,Command('tick','Active'),m,D)

    def test_empty_and_full_release_domains(self):
        for m in range(1,8):
            self.assertEqual(predicted_class_count(m,frozenset()),2)
            self.assertEqual(predicted_class_count(m,frozenset(range(m))),m+2)
            self.assertEqual(stage_partition(m,frozenset(),'Held'),(tuple(range(m)),))

    def test_shift_is_not_a_congruence_when_forbidden(self):
        m,D=4,frozenset((0,1))
        groups=stage_partition(m,D,'Held')
        self.assertIn((0,1),groups)
        self.assertNotIn((1,2),groups)
        cls=minimization(m,D)
        self.assertEqual(cls[Control('Held',0)],cls[Control('Held',1)])
        self.assertNotEqual(cls[Control('Held',1)],cls[Control('Held',2)])


if __name__=='__main__': unittest.main()
