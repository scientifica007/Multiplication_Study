"""Standalone independent check of the batch-size moment bound.

This checks a classical Newton-identities corollary, NOT a novel theorem.
Run: python3 research/audit-2026-11-22/audit_moment_bound.py
"""
from itertools import combinations_with_replacement


def power_sums(batches, bound):
    return tuple(sum(x**j for x in batches) for j in range(1, bound + 1))


def recover_positive_multiset(moments):
    """Recover <=K positive integer sizes, when K=len(moments) is known.

    Pad with zeros to exactly K; Newton identities recover a monic
    polynomial whose roots are the K padded sizes. Brute-force integer
    root extraction here is intentionally small-scale, for validation.
    """
    k = len(moments)
    elementary = [1]
    for j in range(1, k + 1):
        numerator = sum((-1)**(i - 1) * elementary[j - i] * moments[i - 1]
                        for i in range(1, j + 1))
        if numerator % j:
            raise ValueError("Non-integral elementary symmetric coefficient")
        elementary.append(numerator // j)
    polynomial = [(-1)**j * elementary[j] for j in range(k + 1)]
    roots = []
    while len(polynomial) > 1:
        for root in range((moments[0] if moments else 0) + 1):
            quotient = [polynomial[0]]
            for coefficient in polynomial[1:-1]:
                quotient.append(coefficient + root * quotient[-1])
            if polynomial[-1] + root * quotient[-1] == 0:
                roots.append(root)
                polynomial = quotient
                break
        else:
            raise ValueError("Polynomial did not split into nonnegative integer roots")
    return tuple(sorted(root for root in roots if root > 0))


def test():
    for k in range(1, 7):
        count = 0
        for n in range(k + 1):
            for sizes in combinations_with_replacement(range(1, 8), n):
                moments = power_sums(sizes, k)
                assert recover_positive_multiset(moments) == sizes, (k, sizes)
                count += 1
        print(f"K={k}: {count} independent multiset trials PASS")
    assert power_sums((1, 4, 4), 2) == power_sums((2, 2, 5), 2) == (9, 33)
    assert power_sums((2, 3), 4) == power_sums((0, 2, 3), 4)
    print("Two-moment collision and zero-batch invisibility: PASS")


if __name__ == "__main__":
    test()
