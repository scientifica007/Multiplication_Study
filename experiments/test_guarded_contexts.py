"""Bounded independent checks of contextual equality and non-group memory."""
import itertools
import unittest
from guarded_contexts import (
    checked_history, weights, has_negative, summarize, add_states,
    append_event, contextual_equivalent, right_distributivity_on_state,
    fiber_state_count, sparse_negative_decision, State,
)


class ContextTests(unittest.TestCase):
    def test_cancellation_counterexample_and_fixed_length(self):
        h1, h2 = ((2,1),), ((2,2),(2,-1))
        self.assertEqual(weights(h1), weights(h2))
        self.assertNotEqual(has_negative(h1), has_negative(h2))
        self.assertFalse(contextual_equivalent(h1,h2))
        # Even if both histories are known to have exactly two receipts:
        x, y = ((2,1),(2,1)), ((2,3),(2,-1))
        self.assertEqual(weights(x), weights(y))
        self.assertEqual(len(x), len(y))
        self.assertNotEqual(has_negative(x), has_negative(y))

    def test_append_context_congruence_exhaustively(self):
        events = ((0,1),(0,-1),(1,1),(1,-1))
        histories = [()] + [seq for k in range(1,4)
                         for seq in itertools.combinations_with_replacement(events,k)]
        for h in histories:
            for k in histories:
                self.assertEqual(summarize(h+k), add_states(summarize(h),summarize(k)))
                self.assertEqual(summarize(h+k), add_states(summarize(k),summarize(h)))
        for h in histories:
            for k in histories:
                if summarize(h) != summarize(k):
                    continue
                for suffix in ((),((0,1),),((0,-1),),((1,1),),((1,-1),)):
                    self.assertEqual(summarize(h+suffix), summarize(k+suffix))

    def test_group_completion_erases_idempotent_flag(self):
        empty = summarize(())
        canceled = summarize(((0,1),(0,-1)))
        self.assertEqual(empty.weight,canceled.weight)
        self.assertNotEqual(empty,canceled)
        self.assertEqual(add_states(canceled,canceled),canceled)
        self.assertEqual(add_states(canceled,empty),canceled)

    def test_exact_fiber_shapes_for_small_observed_weights(self):
        # q=False implies all W coefficients nonnegative; q=True always possible.
        for a in range(-3,4):
            for b in range(-3,4):
                w = tuple((lab,coef) for lab,coef in ((0,a),(1,b)) if coef)
                self.assertEqual(fiber_state_count(w),
                                 1 if (a < 0 or b < 0) else 2)
        self.assertEqual(fiber_state_count(()),2)

    def test_partial_right_distribution_and_guard_failure(self):
        for m in range(-5,6):
            for n in range(-5,6):
                if not m or not n or not(m+n):
                    continue
                expected = ((m+n<0) == (m<0 or n<0))
                self.assertEqual(right_distributivity_on_state(4,m,n),expected)
        self.assertFalse(right_distributivity_on_state(4,2,-1))
        self.assertTrue(right_distributivity_on_state(4,-2,1))

    def test_sparse_guard_is_observable_from_signed_weights(self):
        for k in range(0,4):
            for labels in itertools.combinations((-2,-1,0,1),k):
                for ns in itertools.product((-2,-1,1,2),repeat=k):
                    h = tuple(zip(labels,ns))
                    self.assertEqual(sparse_negative_decision(h,3),has_negative(h))
        with self.assertRaises(ValueError):
            sparse_negative_decision(((1,2),(1,-1)),2)
        with self.assertRaises(ValueError):
            checked_history(((1,0),))


if __name__ == '__main__':
    unittest.main()
