"""Independent finite-model checks for THEOREM.md.

No imports from the original repository. Python 3.10+ only.
Passing finite tests does not establish a general theorem or originality.
"""
from itertools import product

BITS = (0, 1)


def apply(table, a, b):
    return table[2*a+b]


def test_all_binary_operations():
    tables = tuple(product(BITS, repeat=4))
    counts = {(True, True):0, (True, False):0,
              (False, True):0, (False, False):0}
    for A, B in product(tables, repeat=2):
        def a(x, y): return apply(A, x, y)
        def b(x, y): return apply(B, x, y)
        def f(x, y): return (x, y)
        def c(x, y): return (a(x[0], y[0]), b(x[1], y[1]))
        left = all(f(a(x, x2), y) == c(f(x, y), f(x2, y))
                   for x, x2, y in product(BITS, repeat=3))
        right = all(f(x, b(y, y2)) == c(f(x, y), f(x, y2))
                    for x, y, y2 in product(BITS, repeat=3))
        assert left == all(b(y, y) == y for y in BITS)
        assert right == all(a(x, x) == x for x in BITS)
        counts[left, right] += 1
    assert counts == {(True, True):16, (True, False):48,
                      (False, True):48, (False, False):144}
    return counts


def test_sharp_semigroup_construction():
    tables = tuple(product(BITS, repeat=4))
    associative = [A for A in tables if all(
        apply(A, apply(A, x, y), z) == apply(A, x, apply(A, y, z))
        for x, y, z in product(BITS, repeat=3))]
    assert len(associative) == 8
    for A in associative:
        idem_A = sum(apply(A, x, x) == x for x in BITS)
        for m in (1, 2, 3, 4):
            C = tuple(product(BITS, range(m)))
            def merge(x, y):
                return (apply(A, x[0], y[0]), max(x[1], y[1]))
            assert all(merge(merge(x, y), z) == merge(x, merge(y, z))
                       for x, y, z in product(C, repeat=3))
            assert all((apply(A, x, y), b) == merge((x, b), (y, b))
                       for x, y, b in product(BITS, BITS, range(m)))
            assert len([x for x in C if merge(x, x) == x]) == m*idem_A
    return len(associative)*4


def test_three_zero_tiers():
    for m in range(1, 7):
        # Level I: m output idempotents. One zero product equals empty.
        T1 = {(0, b) for b in range(m)}
        assert len(T1) == m and (0, 0) in T1
        # Level II: empty distinct from all zero-rate products.
        T2 = {(0, b+1) for b in range(m)} | {(0, 0)}
        assert len(T2) == m+1
        for b, n, p in product(range(m), range(4), range(4)):
            assert (n+p, b+1) == (n+p, max(b+1, b+1))
    for m in range(1, 6):
        zero = (0,)*m
        subsets = {(zero, mask) for mask in range(1 << m)}
        assert len(subsets) == 2**m
        # The tag OR operation and coordinate sum form a commutative monoid.
        for b, n, p in product(range(m), range(4), range(4)):
            x = tuple(n if k == b else 0 for k in range(m))
            y = tuple(p if k == b else 0 for k in range(m))
            merged = (tuple(i+j for i, j in zip(x, y)),
                      (1 << b) | (1 << b))
            expected = (tuple(n+p if k == b else 0 for k in range(m)),
                        1 << b)
            assert merged == expected
        for mask in range(1 << m):
            x = (zero, mask)
            assert (tuple(i+i for i in x[0]), mask | mask) == x
    return "m<=6 for tiers I-II; m<=5 for tier III"


def main():
    outcomes = test_all_binary_operations()
    constructions = test_sharp_semigroup_construction()
    tiers = test_three_zero_tiers()
    print("PASS binary tables (256):", outcomes)
    print("PASS sharp idempotent capacity:", constructions, "associative models")
    print("PASS three zero-declaration tiers:", tiers)
    print("These are finite checks, not formal proofs or novelty evidence.")


if __name__ == "__main__":
    main()
