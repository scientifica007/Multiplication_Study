"""Exact tests for extending a Euclidean square by a free displacement in 3-space."""

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

from model import Undefined


Scalar = int | Fraction
Vector = tuple[Scalar, Scalar, Scalar]


class Goal(Enum):
    SOLID = "solid"
    RIGHT_PRISM = "right_prism"
    CUBE = "cube"


def dot(a: Vector, b: Vector) -> Scalar:
    return sum(x * y for x, y in zip(a, b))


def cross(a: Vector, b: Vector) -> Vector:
    x, y, z = a
    u, v, w = b
    return y * w - z * v, z * u - x * w, x * v - y * u


def axis(v: Vector) -> Vector | None:
    """Represent an unoriented line by making its first nonzero coordinate one."""
    pivot = next((x for x in v if x), None)
    if pivot is None:
        return None
    x, y, z = v
    return Fraction(x, pivot), Fraction(y, pivot), Fraction(z, pivot)


@dataclass(frozen=True)
class Segment:
    """A directed displacement. Zero is admitted as a probe for degeneracy."""

    vector: Vector

    def __post_init__(self):
        if not isinstance(self.vector, tuple) or len(self.vector) != 3:
            raise ValueError("A displacement needs three coordinates")
        if any(type(x) not in (int, Fraction) for x in self.vector):
            raise ValueError("Use integers or exact fractions for coordinates")

    @property
    def length_squared(self) -> Scalar:
        return dot(self.vector, self.vector)


@dataclass(frozen=True)
class Square:
    """A base keeps the two ordered, directed sides issuing from the origin."""

    first: Segment
    second: Segment

    def __post_init__(self):
        if not isinstance(self.first, Segment) or not isinstance(self.second, Segment):
            raise Undefined("A square base needs two segments")
        size = self.first.length_squared
        if not size or self.second.length_squared != size or dot(self.first.vector, self.second.vector):
            raise Undefined("Square sides must be nonzero, perpendicular and of equal length")

    @property
    def normal(self) -> Vector:
        return cross(self.first.vector, self.second.vector)

    def unpack(self) -> tuple[Segment, Segment]:
        return self.first, self.second


@dataclass(frozen=True)
class Description:
    """The square's normal line or the segment's line, and the size if needed."""

    axis: Vector | None
    length_squared: Scalar | None


def describe(item: Square | Segment, goal: Goal) -> Description:
    """A minimal description within the specified role for one admissibility test."""
    if not isinstance(goal, Goal):
        raise ValueError("Unknown geometric goal")
    if isinstance(item, Square):
        line = axis(item.normal)
        length_squared = item.first.length_squared
    elif isinstance(item, Segment):
        line = axis(item.vector)
        length_squared = item.length_squared
    else:
        raise TypeError("Expected a square or a segment")
    return Description(line, length_squared if goal is Goal.CUBE else None)


def allows(base: Square | Segment, step: Square | Segment, goal: Goal) -> bool:
    if not isinstance(base, Square) or not isinstance(step, Segment):
        return False
    square = describe(base, goal)
    segment = describe(step, goal)
    if segment.axis is None:
        return False
    if goal is Goal.SOLID:
        return dot(square.axis, segment.axis) != 0
    # For a right prism only the axes are stored. The cube also compares sizes.
    return square == segment


@dataclass(frozen=True)
class Extension:
    base: Square
    step: Segment
    goal: Goal = field(compare=False)  # A test of the construction, not a third operand.

    def __post_init__(self):
        if not allows(self.base, self.step, self.goal):
            raise Undefined("This ordered pair cannot produce the requested solid")

    @property
    def volume(self) -> Scalar:
        return abs(dot(self.base.normal, self.step.vector))

    def unpack(self) -> tuple[Square, Segment]:
        return self.base, self.step


if __name__ == "__main__":
    base = Square(Segment((5, 0, 0)), Segment((0, 5, 0)))
    print("قاعدة مربعة ضلعها 5 سم في المستوى xy")
    print("الإزاحة (سم) | جسم ذو حجم | منشور قائم | مكعب | الحجم (سم³)")
    for vector in ((5, 0, 0), (3, 0, 4), (0, 0, 3), (0, 0, 5), (3, 0, 5), (0, 0, -5)):
        step = Segment(vector)
        verdicts = ["نعم" if allows(base, step, goal) else "لا" for goal in Goal]
        volume = str(Extension(base, step, Goal.SOLID).volume) if allows(base, step, Goal.SOLID) else "—"
        print(" | ".join([str(vector), *verdicts, volume]))
