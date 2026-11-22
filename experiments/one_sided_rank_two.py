"""Rank-two witness for injective partial right-additive typed multiplication.

Not a field multiplication. A and B are distinct sorts, and right factor zero
is excluded. The image is only elementary one-step products; adding them does
not retain the entire sequence of operations.
"""
from dataclasses import dataclass
from signed_provenance import Atom


@dataclass(frozen=True, order=True)
class Output:
    rate: int
    reading: int

    def __post_init__(self):
        if not isinstance(self.rate, int) or not isinstance(self.reading, int):
            raise TypeError('Integer coordinates required')

    def __add__(self, other):
        if not isinstance(other, Output):
            return NotImplemented
        return Output(self.rate + other.rate, self.reading + other.reading)

    def __neg__(self):
        return Output(-self.rate, -self.reading)

    def __sub__(self, other):
        if not isinstance(other, Output):
            return NotImplemented
        return self + -other


def multiply(left: Atom, right: Atom) -> Output:
    if left.sort != 'A' or right.sort != 'B' or right.amount == 0:
        raise ValueError('Domain is A x (B without zero) in that order')
    return Output(right.amount, left.amount * right.amount)


def unpack(record: Output) -> tuple[Atom, Atom]:
    """Partial inverse on the elementary product image only.

    An aggregate of receipts can also lie in this image; the inverse then
    identifies its *value* as a product, NOT the history of its addition.
    """
    if not isinstance(record, Output) or record.rate == 0:
        raise ValueError('Not a one-step receipt')
    a, residue = divmod(record.reading, record.rate)
    if residue:
        raise ValueError('Coordinates not in the elementary product image')
    return Atom('A', a), Atom('B', record.rate)


def output_measure(record: Output) -> int:
    return record.reading


def left_defect(a: int, b: int, n: int) -> Output:
    """f(a+b,n)-f(a,n)-f(b,n) = (-n,0) for n != 0."""
    if n == 0:
        raise ValueError('Zero right factor is not admissible')
    rate = Atom('B', n)
    return (multiply(Atom('A', a + b), rate)
            - multiply(Atom('A', a), rate)
            - multiply(Atom('A', b), rate))


def multiply_with_zero(left: Atom, right: Atom) -> Output:
    """All A x B pairs retained, but NO distributivity law at right zero.

    For n != 0 output (2n, a*n); for n=0 output (2a+1, 0).
    Product reading is always a*n. Even/odd first coordinates separate
    the regular and zero-factor images in the rank-two target.
    """
    if left.sort != 'A' or right.sort != 'B':
        raise ValueError('Only ordered A x B')
    a, n = left.amount, right.amount
    return Output(2*n, a*n) if n else Output(2*a + 1, 0)


def unpack_with_zero(record: Output) -> tuple[Atom, Atom]:
    if not isinstance(record, Output):
        raise TypeError('Expected rank-two record')
    x, y = record.rate, record.reading
    if x % 2:
        if y:
            raise ValueError('Zero-factor receipt must have zero reading')
        return Atom('A', (x-1)//2), Atom('B', 0)
    if x == 0:
        raise ValueError('Not in elementary product image')
    n = x//2
    a, residue = divmod(y, n)
    if residue:
        raise ValueError('Not in elementary product image')
    return Atom('A', a), Atom('B', n)


def proportional_vectors(u: tuple[int, int], v: tuple[int, int]) -> bool:
    """Rational dependence of two vectors in Z^2 (not a generic test)."""
    return u[0] * v[1] == u[1] * v[0]


if __name__ == '__main__':
    for a, n in ((1, 1), (1, -1), (-1, 1), (-1, -1), (0, -3)):
        y = multiply(Atom('A', a), Atom('B', n))
        print(f'f(A_{a}, B_{n}) = {y}, inverse = {unpack(y)}')
    print('left defect at a=2, b=-3, n=-2:', left_defect(2, -3, -2))
    print('same-sum counterexample:',
          multiply(Atom('A', 1), Atom('B', 1)) + multiply(Atom('A', 3), Atom('B', 1)),
          multiply(Atom('A', 0), Atom('B', 1)) + multiply(Atom('A', 4), Atom('B', 1)))
