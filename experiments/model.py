"""One model of the axioms, with nonnegative counts and ordered finite terms."""

from __future__ import annotations

from dataclasses import dataclass, field


PRODUCTS = {
    ("apple", "times"): "apple",
    ("box", "screws_per_box"): "screw",
    ("screws_per_box", "box"): "screw",
    ("bundle", "boxes_per_bundle"): "box",
    ("boxes_per_bundle", "screws_per_box"): "screws_per_bundle",
    ("bundle", "screws_per_bundle"): "screw",
}
LIFTS = {
    ("apple", "fruit"), ("pear", "fruit"), ("fruit", "thing"),
    ("apple", "thing"), ("pear", "thing"),
}
KINDS = frozenset(
    {kind for pair in PRODUCTS for kind in pair}
    | set(PRODUCTS.values())
    | {kind for pair in LIFTS for kind in pair}
)


class Undefined(ValueError):
    """The proposed operation has no value on these typed operands."""


@dataclass(frozen=True)
class Atom:
    kind: str
    amount: int

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"Unknown kind: {self.kind}")
        if type(self.amount) is not int or self.amount < 0:
            raise ValueError("Counts must be nonnegative integers")


@dataclass(frozen=True)
class Lift:
    source: Quantity
    kind: str

    def __post_init__(self):
        if (self.source.kind, self.kind) not in LIFTS:
            raise Undefined(f"No lift from {self.source.kind} to {self.kind}")

    @property
    def amount(self) -> int:
        return self.source.amount


@dataclass(frozen=True)
class Binary:
    operator: str
    left: Quantity
    right: Quantity
    kind: str = field(init=False)
    amount: int = field(init=False)

    def __post_init__(self):
        kinds = (self.left.kind, self.right.kind)
        if self.operator == "+":
            if kinds[0] != kinds[1]:
                raise Undefined(f"Addition requires the same declared kind: {kinds}")
            kind = self.left.kind
            amount = self.left.amount + self.right.amount
        elif self.operator == "*":
            if kinds[0] == kinds[1] or kinds not in PRODUCTS:
                raise Undefined(f"No product for {kinds}")
            kind = PRODUCTS[kinds]
            amount = self.left.amount * self.right.amount
        else:
            raise ValueError(f"Unknown operation: {self.operator}")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "amount", amount)


Quantity = Atom | Lift | Binary


def add(a: Quantity, b: Quantity) -> Binary:
    return Binary("+", a, b)


def multiply(a: Quantity, b: Quantity) -> Binary:
    return Binary("*", a, b)


def reading(a: Quantity) -> tuple[str, int]:
    return a.kind, a.amount


def unpack(product: Quantity) -> tuple[Quantity, Quantity]:
    if not isinstance(product, Binary) or product.operator != "*":
        raise Undefined("Only a product has two multiplication operands")
    return product.left, product.right
