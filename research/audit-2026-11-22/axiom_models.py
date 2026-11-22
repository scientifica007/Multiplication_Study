"""Four finite models of the user's core axioms; distributions vary independently."""
from itertools import product

VALUES = (0, 1)


def op(name, a, b):
    if name == "max":
        return max(a, b)
    if name == "xor":
        return a ^ b
    raise ValueError(name)


def check(left_op, right_op):
    def add_a(a, x): return op(left_op, a, x)
    def add_b(b, y): return op(right_op, b, y)
    def add_c(p, q): return (add_a(p[0], q[0]), add_b(p[1], q[1]))
    def mul(a, b): return (a, b)  # type A × type B -> type C
    def unpack(z): return z

    for a, b in product(VALUES, repeat=2):
        assert unpack(mul(a, b)) == (a, b)
    left = all(
        mul(add_a(a, aa), b) == add_c(mul(a, b), mul(aa, b))
        for a, aa, b in product(VALUES, repeat=3)
    )
    right = all(
        mul(a, add_b(b, bb)) == add_c(mul(a, b), mul(a, bb))
        for a, b, bb in product(VALUES, repeat=3)
    )
    return left, right


def test():
    expected = {
        ("max", "max"): (True, True),
        ("xor", "max"): (True, False),
        ("max", "xor"): (False, True),
        ("xor", "xor"): (False, False),
    }
    for ops, result in expected.items():
        observed = check(*ops)
        assert observed == result, (ops, observed, result)
        print(f"A={ops[0]} B={ops[1]}: left={observed[0]}, right={observed[1]} PASS")


if __name__ == "__main__":
    test()
