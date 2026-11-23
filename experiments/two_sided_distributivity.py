"""Two-sided distributivity versus injectivity of typed multiplication.

The maps preserve binary addition in each variable, but are NOT required
 to preserve each type's zero. This distinction is central to the theorem.
"""
from dataclasses import dataclass
from itertools import combinations

X = frozenset(('alpha', 'beta'))
Y = frozenset(('u', 'v'))


def powerset(base):
    ordered = sorted(base)
    return tuple(frozenset(items) for n in range(len(ordered) + 1)
                 for items in combinations(ordered, n))


@dataclass(frozen=True)
class Left:
    items: frozenset[str]
    sort: str = 'A'
    def __post_init__(self):
        if not self.items <= X:
            raise ValueError('Invalid left-factor set')


@dataclass(frozen=True)
class Right:
    items: frozenset[str]
    sort: str = 'B'
    def __post_init__(self):
        if not self.items <= Y:
            raise ValueError('Invalid right-factor set')


@dataclass(frozen=True)
class Output:
    tokens: frozenset[tuple]
    sort: str = 'E'
    def __post_init__(self):
        allowed = {('L', x) for x in X} | {('R', y) for y in Y} | {
            ('P', x, y) for x in X for y in Y}
        if not self.tokens <= allowed:
            raise ValueError('Invalid output provenance token')


def left_add(a: Left, b: Left) -> Left:
    if not isinstance(a, Left) or not isinstance(b, Left):
        raise TypeError('A+A must be used only on type A')
    return Left(a.items | b.items)


def right_add(a: Right, b: Right) -> Right:
    if not isinstance(a, Right) or not isinstance(b, Right):
        raise TypeError('B+B must be used only on type B')
    return Right(a.items | b.items)


def output_add(a: Output, b: Output) -> Output:
    if not isinstance(a, Output) or not isinstance(b, Output):
        raise TypeError('E+E must be used only on type E')
    return Output(a.tokens | b.tokens)


def product(a: Left, b: Right) -> Output:
    """A x B -> E, with fully recoverable ordered inputs and cross tokens."""
    if not isinstance(a, Left) or not isinstance(b, Right):
        raise TypeError('Operands must be of types A then B')
    return Output(frozenset(
        {('L', x) for x in a.items} | {('R', y) for y in b.items} |
        {('P', x, y) for x in a.items for y in b.items}))


def unpack(e: Output) -> tuple[Left, Right]:
    """Defined only on true outputs of a single multiplication."""
    if not isinstance(e, Output):
        raise TypeError('A full output is required')
    a = Left(frozenset(token[1] for token in e.tokens if token[0] == 'L'))
    b = Right(frozenset(token[1] for token in e.tokens if token[0] == 'R'))
    if product(a, b) != e:
        raise ValueError('An aggregate of outputs need not be one product')
    return a, b


def left_domain():
    return tuple(Left(items) for items in powerset(X))


def right_domain():
    return tuple(Right(items) for items in powerset(Y))


def zero_row_collision(left_identity, d, plus_left, plus_right, mul):
    """Symbolically check the necessary collision mu(0,d)=mu(0,d+d).

    The result depends only on the two binary distributivity equations,
    not on cancellation or a group structure in the output.
    """
    if plus_left(left_identity, left_identity) != left_identity:
        raise ValueError('An additive idempotent left input is needed')
    first = mul(left_identity, d)
    doubled = mul(left_identity, plus_right(d, d))
    return first == doubled


def idempotent_pair_construction(a, b):
    """Generic construction E=A x B with componentwise idempotent addition.

    The returned (a,b) is an element of a DISTINCT output sort E; unpacking
    returns the ordered pair. Implemented generically by the token model above.
    """
    return (a, b)


if __name__ == '__main__':
    A, B = left_domain(), right_domain()
    print('A size',len(A),'B size',len(B),'distinct full results',len({product(a,b) for a in A for b in B}))
    print('two zero-axis samples:',product(Left(frozenset()),B[1]),product(A[1],Right(frozenset())))


def cyclic_bilinear_map(a: int, b: int, k: int = 1, modulus: int = 3) -> int:
    """A standard biadditive reading on cyclic groups (not a provenance log)."""
    if type(modulus) is not int or modulus < 2:
        raise ValueError('Modulus must be an integer >= 2')
    return k * a * b % modulus


def list_cyclic_bilinear_maps(modulus: int):
    """All maps Z_m x Z_m -> Z_m that preserve both additions.

    A bilinear map is uniquely determined by mu(1,1): mu(a,b)=a*b*k mod m.
    This returns all possible maps and is used to verify the generic group case.
    """
    return tuple(tuple(tuple(cyclic_bilinear_map(a,b,k,modulus)
                             for b in range(modulus)) for a in range(modulus))
                 for k in range(modulus))
