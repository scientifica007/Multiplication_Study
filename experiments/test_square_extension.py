"""Cross-check square-extension decisions, minimal descriptions and ordered records."""

import unittest
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import permutations, product

from model import Undefined
from square_extension import Extension, Goal, Segment, Square, allows, describe


def scale(v, factor):
    return tuple(factor*x for x in v)


def catalog():
    # Three orthonormal frames; the first two share only the vertical axis.
    frames = [
        ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        (scale((3, 4, 0), Fraction(1, 5)), scale((-4, 3, 0), Fraction(1, 5)), (0, 0, 1)),
        tuple(scale(v, Fraction(1, 3)) for v in ((1, 2, 2), (2, 1, -2), (-2, 2, -1))),
    ]
    bases, segments = set(), set()
    for frame in frames:
        for length in (1, 2):
            for a, b in permutations(frame, 2):
                for sign_a, sign_b in product((-1, 1), repeat=2):
                    first = Segment(scale(a, sign_a*length))
                    second = Segment(scale(b, sign_b*length))
                    bases.add(Square(first, second))
                    segments.add(first)
    return tuple(bases), tuple(segments)


def direct(base, step):
    # Independent of normal vectors and axis normalization. Project onto both sides.
    a, b, w = base.first.vector, base.second.vector, step.vector
    q = sum(x*x for x in a)
    r = sum(x*x for x in w)
    h1 = sum(x*y for x, y in zip(a, w))
    h2 = sum(x*y for x, y in zip(b, w))
    perpendicular_part = q*r - h1*h1 - h2*h2
    right = r > 0 and h1 == 0 and h2 == 0
    return (perpendicular_part > 0, right, right and q == r), q*perpendicular_part


def partition(keys):
    groups = defaultdict(set)
    for i, key in enumerate(keys):
        groups[key].add(i)
    return {frozenset(members) for members in groups.values()}


def vertices(solid):
    a, b, w = solid.base.first.vector, solid.base.second.vector, solid.step.vector
    return frozenset(tuple(i*x + j*y + k*z for x, y, z in zip(a, b, w))
                     for i, j, k in product((0, 1), repeat=3))


class SquareExtensionChecks(unittest.TestCase):
    def test_fixed_base_examples(self):
        base = Square(Segment((5, 0, 0)), Segment((0, 5, 0)))
        cases = [
            ((5, 0, 0), (False, False, False), None),
            ((3, 0, 4), (True, False, False), 100),
            ((0, 0, 3), (True, True, False), 75),
            ((0, 0, 5), (True, True, True), 125),
            ((3, 0, 5), (True, False, False), 125),
            ((0, 0, -5), (True, True, True), 125),
        ]
        for vector, decisions, volume in cases:
            step = Segment(vector)
            for goal, expected in zip(Goal, decisions):
                self.assertEqual(allows(base, step, goal), expected, (vector, goal))
                if expected:
                    solid = Extension(base, step, goal)
                    self.assertEqual((solid.volume, solid.unpack()), (volume, (base, step)))
                else:
                    with self.assertRaises(Undefined):
                        Extension(base, step, goal)

    def test_decisions_volumes_and_profile_minimality_on_catalog(self):
        bases, steps = catalog()
        self.assertEqual((len(bases), len(steps)), (144, 32))
        matrices = {goal: [[] for _ in bases] for goal in Goal}
        for i, base in enumerate(bases):
            for step in steps:
                expected, volume_squared = direct(base, step)
                for goal, ok in zip(Goal, expected):
                    self.assertEqual(allows(base, step, goal), ok, (base, step, goal))
                    matrices[goal][i].append(ok)
                if expected[0]:
                    self.assertEqual(Extension(base, step, Goal.SOLID).volume**2, volume_squared)
        for goal, matrix in matrices.items():
            rows = partition(tuple(row) for row in matrix)
            cols = partition(zip(*matrix))
            self.assertEqual(rows, partition(describe(s, goal) for s in bases))
            self.assertEqual(cols, partition(describe(v, goal) for v in steps))
            classes = 16 if goal is Goal.CUBE else 8
            self.assertEqual((len(rows), len(cols)), (classes, classes))
        accepted = [sum(map(sum, matrix)) for matrix in matrices.values()]
        self.assertEqual(accepted, [3200, 576, 288])

    def test_readings_directions_and_full_operands(self):
        x, y, z = (Segment(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
        xy, xz, yx = Square(x, y), Square(x, z), Square(y, x)
        up, side, swapped = (Extension(b, s, Goal.CUBE) for b, s in ((xy, z), (xz, y), (yx, z)))
        self.assertEqual(up, Extension(xy, z, Goal.SOLID))
        self.assertEqual(vertices(up), vertices(side))
        self.assertEqual(vertices(up), vertices(swapped))
        self.assertEqual(len({up, side, swapped}), 3)
        self.assertEqual(side.unpack(), (xz, y))
        self.assertEqual(side.unpack()[0].unpack(), (x, z))
        self.assertFalse(allows(xz, z, Goal.CUBE))
        self.assertFalse(allows(z, xy, Goal.CUBE))
        self.assertFalse(allows(xy, xy, Goal.CUBE))
        self.assertFalse(allows(z, z, Goal.SOLID))
        with self.assertRaises(Undefined):
            Extension(z, xy, Goal.CUBE)
        down = Segment((0, 0, -1))
        self.assertEqual(describe(z, Goal.CUBE), describe(down, Goal.CUBE))
        self.assertNotEqual(vertices(up), vertices(Extension(xy, down, Goal.CUBE)))
        for goal in Goal:
            self.assertEqual(describe(xy, goal), describe(yx, goal))

    def test_archive_unit_axes_recovered(self):
        unit_axes = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        steps = [Segment(scale(v, sense)) for v in unit_axes for sense in (-1, 1)]
        bases = [Square(a, b) for a, b in permutations(steps, 2)
                 if sum(x*y for x, y in zip(a.vector, b.vector)) == 0]
        positions = Counter(vertices(Extension(base, step, Goal.CUBE))
                            for base, step in product(bases, steps) if allows(base, step, Goal.CUBE))
        self.assertEqual((len(bases), len(bases)*len(steps), sum(positions.values())), (24, 144, 48))
        self.assertEqual((len(positions), set(positions.values())), (8, {6}))
        base_classes = Counter(describe(base, Goal.CUBE) for base in bases)
        step_classes = Counter(describe(step, Goal.CUBE) for step in steps)
        self.assertEqual((len(base_classes), set(base_classes.values())), (3, {8}))
        self.assertEqual((len(step_classes), set(step_classes.values())), (3, {2}))

    def test_degenerate_and_exact_inputs(self):
        a = Segment((1, 0, 0))
        base = Square(a, Segment((0, 1, 0)))
        zero = Segment((0, 0, 0))
        for goal in Goal:
            self.assertFalse(allows(base, zero, goal))
        for bad in (zero, a, Segment((-1, 0, 0)), Segment((0, 2, 0))):
            with self.assertRaises(Undefined):
                Square(a, bad)
        for malformed in ((1, 2), (True, 0, 0), (0, 0, 0.1)):
            with self.assertRaises(ValueError):
                Segment(malformed)
        epsilon = Fraction(1, 10**30)
        nearly_flat = Segment((1, 0, epsilon))
        self.assertEqual(Extension(base, nearly_flat, Goal.SOLID).volume, epsilon)
        self.assertFalse(allows(base, nearly_flat, Goal.RIGHT_PRISM))
        tiny = Square(Segment((epsilon, 0, 0)), Segment((0, epsilon, 0)))
        self.assertEqual(Extension(tiny, Segment((0, 0, -epsilon)), Goal.CUBE).volume, epsilon**3)

    def test_fewer_partners_can_merge_descriptions(self):
        x, y, z = (Segment(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
        xy, yz = Square(x, y), Square(y, z)
        self.assertNotEqual(describe(x, Goal.CUBE), describe(y, Goal.CUBE))
        self.assertEqual(allows(xy, x, Goal.CUBE), allows(xy, y, Goal.CUBE))
        self.assertNotEqual(allows(yz, x, Goal.CUBE), allows(yz, y, Goal.CUBE))
        small, big = xy, Square(Segment((2, 0, 0)), Segment((0, 2, 0)))
        self.assertEqual(describe(small, Goal.SOLID), describe(big, Goal.SOLID))
        self.assertNotEqual(allows(small, z, Goal.CUBE), allows(big, z, Goal.CUBE))


if __name__ == "__main__":
    unittest.main(verbosity=2)
