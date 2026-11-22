"""Exact integer moment encoding and Prony reconstruction for distinct labels.

The model is an additional one-sided-distributive many-sorted algebra, not a
consequence of the founding axioms alone. Exact arithmetic; no floating point.
"""
from fractions import Fraction
from itertools import combinations
from math import comb, isqrt


def moments(history, h):
    """History: iterable of (integer A-label, nonzero integer B-amount).

    One A-label per history, up to h terms. Order of terms is irrelevant.
    Returns 2h additive coordinates m_j=sum(n*a**j), j=0,...,2h-1.
    """
    if not isinstance(h, int) or h < 1:
        raise ValueError('h must be a positive integer')
    history = tuple(history)
    if len(history) > h or len({a for a, _ in history}) != len(history):
        raise ValueError('At most h terms, with distinct A-labels')
    if any(not isinstance(a, int) or not isinstance(n, int) or n == 0
           for a, n in history):
        raise ValueError('Integer labels and nonzero integer amounts required')
    return tuple(sum(n * a**j for a, n in history) for j in range(2*h))


def rational_solve(matrix, vector):
    """Exact solver for a nonsingular square system over rational numbers."""
    size = len(vector)
    if len(matrix) != size or any(len(row) != size for row in matrix):
        raise ValueError('Square system required')
    if not size:
        return ()
    a = [[Fraction(v) for v in row] + [Fraction(b)]
         for row, b in zip(matrix, vector)]
    for col in range(size):
        pivot = next((r for r in range(col, size) if a[r][col]), None)
        if pivot is None:
            raise ValueError('Singular system')
        a[col], a[pivot] = a[pivot], a[col]
        divisor = a[col][col]
        a[col] = [v / divisor for v in a[col]]
        for r in range(size):
            if r != col:
                factor = a[r][col]
                if factor:
                    a[r] = [x - factor*y for x, y in zip(a[r], a[col])]
    return tuple(row[-1] for row in a)


def nonsingular(matrix):
    try:
        rational_solve(matrix, [0]*len(matrix))
        return True
    except ValueError:
        return False


def integer_roots_monic(coefficients):
    """All distinct integer roots of a monic polynomial, low coefficient first.

    Used only on exact moment inputs known to originate from integer nodes.
    It is NOT a fast factoring algorithm. Raises ValueError for invalid input.
    """
    poly = [Fraction(c) for c in coefficients]
    if len(poly) < 2 or poly[-1] != 1:
        raise ValueError('Monic positive-degree polynomial required')
    if any(c.denominator != 1 for c in poly):
        raise ValueError('Nonintegral polynomial coefficients')
    roots = []
    while len(poly) > 1:
        const = int(poly[0])
        if const == 0:
            root = 0
        else:
            candidates = set()
            for d in range(1, isqrt(abs(const))+1):
                if const % d == 0:
                    candidates.update((d, -d, const//d, -(const//d)))
            root = next((candidate for candidate in sorted(candidates)
                         if sum(poly[j]*candidate**j for j in range(len(poly))) == 0), None)
        if root is None or root in roots:
            raise ValueError('Polynomial has no full set of distinct integer roots')
        roots.append(root)
        # Divide by X-root using exact synthetic division.
        quotient = [Fraction(0)]*(len(poly)-1)
        quotient[-1] = poly[-1]
        for j in range(len(quotient)-2, -1, -1):
            quotient[j] = poly[j+1]+root*quotient[j+1]
        if poly[0] + root*quotient[0] != 0:
            raise AssertionError('Internal polynomial division mismatch')
        poly = quotient
    return tuple(sorted(roots))


def reconstruct(moment_values):
    """Prony reconstruction, returning sorted ((a,n),...) for ≤ h distinct nodes.

    Input must have even length 2h and represent integer labels and nonzero
    integer weights. Rejects invalid observations. Exact arithmetic only.
    """
    values = tuple(moment_values)
    if len(values) < 2 or len(values) % 2 or any(not isinstance(z, int) for z in values):
        raise ValueError('Exactly 2h integer moments are required')
    h = len(values)//2
    r = next((q for q in range(h, 0, -1)
              if nonsingular([[values[i+j] for j in range(q)] for i in range(q)])), 0)
    if not r:
        if all(v == 0 for v in values):
            return ()
        raise ValueError('Invalid moment vector')
    hankel = [[values[i+j] for j in range(r)] for i in range(r)]
    p = rational_solve(hankel, [-values[r+i] for i in range(r)])
    roots = integer_roots_monic(tuple(p)+(Fraction(1),))
    amounts = rational_solve([[a**j for a in roots] for j in range(r)], values[:r])
    if any(n.denominator != 1 or n == 0 for n in amounts):
        raise ValueError('Not an integer distinct-label history')
    result = tuple((a, int(n)) for a, n in zip(roots, amounts))
    if moments(result, h) != values:
        raise ValueError('Invalid moment vector: failed forward verification')
    return result


def finite_difference_collision(h):
    """Two h-term positive-weight histories with equal first 2h-1 moments."""
    if not isinstance(h, int) or h < 1:
        raise ValueError('Positive h required')
    order = 2*h-1
    positive = tuple((a, comb(order, a)) for a in range(0, order+1, 2))
    negative = tuple((a, comb(order, a)) for a in range(1, order+1, 2))
    assert len(positive) == len(negative) == h
    return positive, negative
