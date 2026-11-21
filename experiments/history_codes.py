"""Exact codes for repetition histories starting at one, with integer factors >= 2."""

from functools import cache
from math import isqrt


@cache
def divisors(n: int) -> tuple[int, ...]:
    if type(n) is not int or n < 1:
        raise ValueError("A positive integer is required")
    small = [d for d in range(1, isqrt(n) + 1) if n % d == 0]
    large = [n // d for d in reversed(small) if d * d != n]
    return tuple(small + large)


@cache
def history_count(n: int) -> int:
    factors = divisors(n)
    if n == 1:
        return 1  # The empty sequence.
    return sum(history_count(n // d) for d in factors[1:])


def encode(steps: tuple[int, ...]) -> tuple[int, int]:
    """Return (measured product, rank), ordering blocks by their last factor."""
    n, rank = 1, 0
    for last in steps:
        if type(last) is not int or last < 2:
            raise ValueError("Each repetition factor must be an integer >= 2")
        n *= last
        rank += sum(history_count(n // d) for d in divisors(n) if 2 <= d < last)
    return n, rank


def decode(n: int, rank: int) -> tuple[int, ...]:
    if type(rank) is not int or not 0 <= rank < history_count(n):
        raise ValueError("Rank outside the histories available for this product")
    backwards = []
    while n > 1:
        for last in divisors(n)[1:]:
            block = history_count(n // last)
            if rank < block:
                backwards.append(last)
                n //= last
                break
            rank -= block
    return tuple(reversed(backwards))
