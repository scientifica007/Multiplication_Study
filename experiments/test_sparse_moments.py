"""Independent finite tests for exact moment reconstruction and obstructions."""
import unittest
from itertools import combinations, product
from sparse_moments import (moments, reconstruct, finite_difference_collision,
                            rational_solve, integer_roots_monic)


class SparseMomentChecks(unittest.TestCase):
    def test_complete_small_exhaustion_h1_to_h3(self):
        cases = {1: (-2,-1,0,1,2), 2: (-3,-2,-1,0,1,2,3), 3: (-2,-1,0,1,2)}
        for h, labels in cases.items():
            seen = {}
            for k in range(h+1):
                for selected in combinations(labels, k):
                    for weights in product((-2,-1,1,2), repeat=k):
                        hist = tuple(zip(selected, weights))
                        enc = moments(hist, h)
                        self.assertNotIn(enc, seen, (h, hist, seen.get(enc)))
                        seen[enc] = hist
                        self.assertEqual(reconstruct(enc), hist)
            self.assertTrue(len(seen)>1)

    def test_same_label_impossibility_even_at_exact_two(self):
        # Raw histories violate the distinct-label hypothesis, but their
        # additive moment observations coincide at every degree.
        def obs(hist, h):
            return tuple(sum(n*a**j for a,n in hist) for j in range(2*h))
        a=7
        self.assertNotEqual(((a,1),(a,3)), ((a,2),(a,2)))
        self.assertEqual(obs(((a,1),(a,3)), 4), obs(((a,2),(a,2)), 4))
        with self.assertRaises(ValueError):
            moments(((a,1),(a,3)), 2)

    def test_sharp_truncated_moment_collisions(self):
        for h in range(1, 7):
            left,right = finite_difference_collision(h)
            full_left = moments(left, h)
            full_right = moments(right, h)
            self.assertEqual(full_left[:-1], full_right[:-1])
            self.assertNotEqual(full_left[-1], full_right[-1])
            self.assertEqual(abs(full_left[-1]-full_right[-1]),
                             __import__('math').factorial(2*h-1))

    def test_additive_and_typed_reading(self):
        h = 3
        one = ((-3,2),)
        two = ((4,-2),)
        self.assertEqual(moments(one+two,h),
                         tuple(a+b for a,b in zip(moments(one,h),moments(two,h))))
        self.assertEqual(moments(one+two,h)[1], -14)
        self.assertEqual(reconstruct((0,0,0,0,0,0)), ())

    def test_signed_cancellations_may_hide_first_moment(self):
        hist = ((-1,1),(1,1))
        obs = moments(hist,2)
        self.assertEqual(obs[1], 0)
        self.assertEqual(reconstruct(obs), hist)
        # signed weights may make m0 zero too
        hist = ((-1,-1),(1,1))
        obs = moments(hist,2)
        self.assertEqual(obs[0], 0)
        self.assertEqual(reconstruct(obs), hist)

    def test_invalid_moment_vectors(self):
        with self.assertRaises(ValueError):
            moments(((3,0),), 2)
        with self.assertRaises(ValueError):
            moments(((0,2),(0,3)), 2)
        with self.assertRaises(ValueError):
            reconstruct((0,))
        with self.assertRaises(ValueError):
            reconstruct((1, 0, 0, 7))
        with self.assertRaises(ValueError):
            rational_solve([[0]], [1])
        self.assertEqual(integer_roots_monic((0,-1,1)), (0,1))


if __name__ == '__main__':
    unittest.main()
