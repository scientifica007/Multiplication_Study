"""One exact distributive law for box counts, with ordered recoverable factors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import overload

from model import Atom, Undefined


BOX = "box"
RATE = "screws_per_box"
Row = tuple[int, int]  # (declared rate, box count)


@dataclass(frozen=True)
class Shipment:
    """One row per declared rate. A zero count keeps the rate of an empty order."""

    rows: tuple[Row, ...] = ()

    def __post_init__(self):
        counts: dict[int, int] = {}
        for rate, count in self.rows:
            if type(rate) is not int or rate < 0 or type(count) is not int or count < 0:
                raise ValueError("Rates and box counts must be nonnegative integers")
            counts[rate] = counts.get(rate, 0) + count
        object.__setattr__(self, "rows", tuple(sorted(counts.items())))

    @property
    def box_count(self) -> int:
        return sum(count for _, count in self.rows)

    @property
    def screw_count(self) -> int:
        return sum(rate * count for rate, count in self.rows)

    def unpack(self) -> tuple[Atom, Atom]:
        """Invert a product with one declared rate, even if its box count is zero."""
        if len(self.rows) != 1:
            raise Undefined("A single packing product has exactly one declared rate")
        rate, count = self.rows[0]
        return Atom(BOX, count), Atom(RATE, rate)

    def without_empty_rates(self) -> Shipment:
        """Project to the ordinary histogram of physical boxes."""
        return Shipment(tuple(row for row in self.rows if row[1] > 0))


def pack(boxes: Atom, rate: Atom) -> Shipment:
    """The only product is (box count, screws per box), in this order."""
    if not isinstance(boxes, Atom) or boxes.kind != BOX:
        raise Undefined("The first factor must be a box count")
    if not isinstance(rate, Atom) or rate.kind != RATE:
        raise Undefined("The second factor must be a packing rate")
    return Shipment(((rate.amount, boxes.amount),))


@overload
def add(left: Atom, right: Atom) -> Atom: ...


@overload
def add(left: Shipment, right: Shipment) -> Shipment: ...


def add(left: Atom | Shipment, right: Atom | Shipment) -> Atom | Shipment:
    """Add typed input values or merge the rows of two shipments."""
    if isinstance(left, Shipment) and isinstance(right, Shipment):
        return Shipment(left.rows + right.rows)
    if isinstance(left, Atom) and isinstance(right, Atom):
        if left.kind == right.kind and left.kind in (BOX, RATE):
            return Atom(left.kind, left.amount + right.amount)
    raise Undefined("Addition requires two box counts, two rates, or two shipments")


if __name__ == "__main__":
    boxes, rate = Atom(BOX, 2), Atom(RATE, 3)
    batch = pack(boxes, rate)
    cases = (
        ("جمع دفعتين من علبتين ثم تطبيق المعدل", pack(add(boxes, boxes), rate)),
        ("تعبئة كل دفعة ثم دمج السجلين", add(batch, batch)),
        ("مضاعفة المعدل في العلبتين", pack(boxes, add(rate, rate))),
        ("علبتان فارغتان", pack(boxes, Atom(RATE, 0))),
        ("طلب لعدد صفر من العلب بمعدل مقرّر", pack(Atom(BOX, 0), rate)),
    )
    for title, shipment in cases:
        count, per_box = shipment.unpack()
        print(f"{title} | عدد العلب {count.amount} | المعدل {per_box.amount} | عدد المسامير {shipment.screw_count}")
    empty = pack(Atom(BOX, 0), rate)
    print(f"طلب لعدد صفر من العلب | خانات المعدلات المقرّرة {len(empty.rows)}"
          f" | الخانات الظاهرة بعد عدّ العلب الفعلية {len(empty.without_empty_rates().rows)}")
