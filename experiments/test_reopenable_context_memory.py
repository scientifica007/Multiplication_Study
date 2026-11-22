"""Seven independent tests for the translated-period contextual-memory theorem."""
import unittest
from itertools import product
from math import ceil, log2

from reopenable_context_memory import (
    State, empty, transition, reachable, minimization, periods, predicted,
    contextual_key, standard_repairs,
)


class ReopenMemoryTests(unittest.TestCase):
    def test_all_repair_functions_small_moduli(self):
        # Every map Z_m -> Z_m for m=1,2,3,4; 1+4+27+256=288 functions.
        n_cases = 0
        for m in range(1, 5):
            for rho in product(range(m), repeat=m):
                N, h = 2, 1
                states, blocks = minimization(N, h, m, rho)
                full, minimal = predicted(N, h, m, rho)
                self.assertEqual(len(states), full)
                self.assertEqual(len(set(blocks.values())), minimal)
                key = {s: contextual_key(s, h, rho) for s in states}
                self.assertEqual(len(set(key.values())), minimal)
                for i, x in enumerate(states):
                    for y in states[i:]:
                        self.assertEqual(blocks[x] == blocks[y], key[x] == key[y],
                                         (m, rho, x, y))
                n_cases += 1
        self.assertEqual(n_cases, 288)

    def test_larger_reachable_models_and_minimization(self):
        for N, h, m in ((3, 2, 3), (3, 2, 6), (4, 3, 2)):
            for label, rho in standard_repairs(m).items():
                states, classes = minimization(N, h, m, rho)
                full, minimum = predicted(N, h, m, rho)
                self.assertEqual((len(states), len(set(classes.values()))),
                                 (full, minimum), (N, h, m, label))

    def test_all_divisor_index_possibilities_mod6(self):
        N, h, m = 3, 2, 6
        counts = {1: 67, 2: 91, 3: 115, 6: 187}
        for divisor, minimum in counts.items():
            rho = tuple(x % divisor for x in range(m))
            self.assertEqual(m // len(periods(rho)), divisor)
            self.assertEqual(predicted(N, h, m, rho), (187, minimum))

    def test_prime_modulus_nonconstant_repair_restores_full_memory(self):
        N, h, m = 3, 2, 3
        rho = (0, 0, 1)  # Only two repair outputs, yet all residues observable.
        self.assertEqual(periods(rho), (0,))
        self.assertEqual(predicted(N, h, m, rho), (97, 97))
        self.assertEqual(predicted(N, h, m, (0, 0, 0)), (97, 49))

    def test_partial_repair_domain_and_typing(self):
        N, h, m = 3, 2, 3
        rho = tuple(range(m))
        state = empty()
        self.assertIsNone(transition(state, 'repair', N, h, m, rho))
        state = transition(state, (0, -1), N, h, m, rho)
        state = transition(state, (1, 1), N, h, m, rho)
        self.assertIsNone(transition(state, 'repair', N, h, m, rho))
        state = transition(state, (2, 1), N, h, m, rho)
        self.assertEqual(state.window, ((1, 1), (2, 1)))
        self.assertTrue(state.negative_since_repair)
        repaired = transition(state, 'repair', N, h, m, rho)
        self.assertFalse(repaired.negative_since_repair)
        self.assertEqual(repaired.residue, state.residue)
        self.assertEqual(repaired.window, state.window)
        self.assertIsNone(transition(state, (2, 1), N, h, m, rho))
        with self.assertRaises(ValueError):
            transition(state, (1, 0), N, h, m, rho)

    def test_exact_number_of_closed_context_classes(self):
        N, h, m = 3, 2, 6
        for rho, expected in (
            (tuple(range(m)), 187),
            ((0,)*m, 67),
            (tuple(x % 3 for x in range(m)), 115),
        ):
            states, classes = minimization(N, h, m, rho)
            self.assertEqual(len(set(classes.values())), expected)
            selected = [s for s in states if s.window == ((0, 1), (1, 1))
                        and s.negative_since_repair]
            self.assertEqual(len(selected), m)
            self.assertEqual(len({classes[s] for s in selected}),
                             m // len(periods(rho)))

    def test_bit_count_is_about_state_encoding_not_event_stream(self):
        self.assertEqual(ceil(log2(67)), 7)
        self.assertEqual(ceil(log2(187)), 8)
        self.assertEqual(predicted(3, 2, 3, tuple(range(3))), (97, 97))
        self.assertEqual(predicted(3, 2, 3, (0, 0, 0)), (97, 49))


if __name__ == '__main__':
    unittest.main()
