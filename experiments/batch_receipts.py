"""Recover unordered packing lots (box count, rate) from a merged Shipment and a tag."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from math import comb, inf

from packing_distribution import Shipment


class _Partitions:
    """Counts of partitions into at most k parts, shared by all rows of a shipment."""

    def __init__(self, maximum: int):
        self.table = [[1] + [0] * maximum]
        for k in range(1, maximum + 1):
            row = self.table[-1].copy()
            for n in range(k, maximum + 1):
                row[n] += row[n - k]
            self.table.append(row)

    def count(self, total: int, length: int, minimum: int) -> int:
        """Sorted lists of this fixed length and sum whose entries are >= minimum."""
        rest = total - length * minimum
        if rest < 0:
            return 0
        return self.table[min(rest, length)][rest]

    def rank(self, sizes: list[int], minimum: int) -> int:
        total, length, tag = sum(sizes), len(sizes), 0
        for size in sizes:
            # The skipped lists have first entry in [minimum, size).
            tag += self.count(total, length, minimum) - self.count(total, length, size)
            total -= size
            length -= 1
            minimum = size
        return tag

    def unrank(self, total: int, length: int, minimum: int, tag: int) -> list[int]:
        sizes = []
        for slots in range(length, 0, -1):
            for size in range(minimum, total // slots + 1):
                block = self.count(total - size, slots - 1, size)
                if tag < block:
                    sizes.append(size)
                    total -= size
                    minimum = size
                    break
                tag -= block
            else:
                raise AssertionError("A valid partition tag must have a continuation")
        return sizes


class BatchReceipts:
    """Rank the preimages of a known rate table, optionally given the total lot count.

    A zero-box lot records its declared rate. Tags preserve multiplicities and
    the two factor roles, with no ordering between independent lots.
    """

    def __init__(self, shipment: Shipment, *, allow_zero: bool = False):
        if type(allow_zero) is not bool:
            raise ValueError("allow_zero must be a boolean")
        self.rows = shipment.rows
        self.allow_zero = allow_zero
        self._minimum = 0 if allow_zero else 1
        self._partitions = _Partitions(max((n for _, n in self.rows), default=0))
        # For each suffix, count the positive partitions by number of positive lots.
        row_count = len(self.rows)
        self._positive = [[1] for _ in range(row_count + 1)]
        self._zero_rows = [0] * (row_count + 1)
        for i in reversed(range(row_count)):
            _, boxes = self.rows[i]
            self._zero_rows[i] = self._zero_rows[i + 1] + (boxes == 0)
            tail = self._positive[i + 1]
            if boxes == 0:
                self._positive[i] = tail
                continue
            counts = [0] * (len(tail) + boxes)
            for k in range(1, boxes + 1):
                ways = self._partitions.count(boxes, k, 1)
                for j, rest in enumerate(tail):
                    counts[k + j] += ways * rest
            self._positive[i] = counts

    def _ways(self, i: int, lots: int, *, cumulative: bool = False) -> int:
        """Suffix count for exactly (or at most) the specified number of lots."""
        if lots < 0:
            return 0
        d = len(self.rows) - i
        if d == 0:
            return int(cumulative or lots == 0)
        positive = self._positive[i]
        if not self.allow_zero:
            if self._zero_rows[i]:
                return 0
            if cumulative:
                return sum(positive[:lots + 1])
            return positive[lots] if lots < len(positive) else 0
        # Each declared zero-total row needs one witness. Distribute extra zeros
        # among all d declared rows, including those with positive totals.
        free = lots - self._zero_rows[i]
        bins = d if cumulative else d - 1
        return sum(positive[j] * comb(free - j + bins, bins)
                   for j in range(min(free + 1, len(positive))))

    def count(self, lot_count: int | None = None) -> int | float:
        if lot_count is not None:
            if type(lot_count) is not int or lot_count < 0:
                raise ValueError("The lot count must be a nonnegative integer")
            return self._ways(0, lot_count)
        if self.allow_zero and self.rows:
            return inf
        if self._zero_rows[0]:
            return 0
        return sum(self._positive[0])

    def fixed_bits(self, lot_count: int | None = None) -> int | None:
        """Optimal fixed length. None means unbounded, 0 means a unique receipt."""
        count = self.count(lot_count)
        if count == 0:
            raise ValueError("No receipt has the given data")
        return None if count == inf else (count - 1).bit_length()

    def _blocks(self, i: int, remaining: int) -> Iterator[tuple[int, int, int]]:
        """Lot count, local choices, suffix choices for each feasible row length."""
        after = len(self.rows) - i - 1
        boxes = self.rows[i][1]
        first = 1 if after else remaining
        last = remaining - after
        if not self.allow_zero:
            last = min(last, boxes)
        for k in range(max(1, first), last + 1):
            local = self._partitions.count(boxes, k, self._minimum)
            tail = self._ways(i + 1, remaining - k)
            if local and tail:
                yield k, local, tail

    def encode(self, lots: Iterable[tuple[int, int]], lot_count: int | None = None) -> int:
        self.count(lot_count)  # Validate the optional public count.
        groups: dict[int, list[int]] = {rate: [] for rate, _ in self.rows}
        for boxes, rate in lots:
            if type(boxes) is not int or boxes < self._minimum:
                raise ValueError("Invalid lot size")
            if type(rate) is not int or rate not in groups:
                raise ValueError("Undeclared packing rate")
            groups[rate].append(boxes)
        remaining = sum(map(len, groups.values()))
        if lot_count is not None and remaining != lot_count:
            raise ValueError("The given lot count does not match the receipt")
        tag = self._ways(0, remaining - 1, cumulative=True) if lot_count is None else 0
        for i, (rate, boxes) in enumerate(self.rows):
            sizes = sorted(groups[rate])
            if not sizes or sum(sizes) != boxes:
                raise ValueError("Each declared rate must occur and match its box count")
            for k, local, tail in self._blocks(i, remaining):
                if k == len(sizes):
                    tag += self._partitions.rank(sizes, self._minimum) * tail
                    remaining -= k
                    break
                tag += local * tail
            else:
                raise ValueError("No compatible distribution of lots among rates")
        return tag

    def decode(self, tag: int, lot_count: int | None = None) -> tuple[tuple[int, int], ...]:
        count = self.count(lot_count)
        if type(tag) is not int or tag < 0 or tag >= count:
            raise ValueError("No receipt with this tag")
        if lot_count is None:
            # Order receipts by total number of lots first, even for an infinite fibre.
            low, high = -1, len(self.rows)
            while self._ways(0, high, cumulative=True) <= tag:
                high = 2 * high + 1
            while high - low > 1:
                mid = (low + high) // 2
                if self._ways(0, mid, cumulative=True) > tag:
                    high = mid
                else:
                    low = mid
            lot_count = high
            tag -= self._ways(0, high - 1, cumulative=True)
        lots = []
        remaining = lot_count
        for i, (rate, boxes) in enumerate(self.rows):
            for k, local, tail in self._blocks(i, remaining):
                if tag < local * tail:
                    row_tag, tag = divmod(tag, tail)
                    sizes = self._partitions.unrank(boxes, k, self._minimum, row_tag)
                    lots.extend((n, rate) for n in sizes)
                    remaining -= k
                    break
                tag -= local * tail
            else:
                raise AssertionError("A valid receipt tag must have a continuation")
        return tuple(lots)


if __name__ == "__main__":
    one = BatchReceipts(Shipment(((3, 4),)))
    print("أربع علب عند المعدل 3 | الرمز | أحجام الدفعات")
    for tag in range(one.count()):
        print(tag, [n for n, _ in one.decode(tag)])
    two = Shipment(((3, 4), (5, 3)))
    for zeros in (False, True):
        book = BatchReceipts(two, allow_zero=zeros)
        zero_policy = "جائزة" if zeros else "مستبعدة"
        total = book.count()
        shown = "غير منتهٍ" if total == inf else str(total)
        print(f"دفعات من صفر علبة {zero_policy} | عدد السجلات {shown}"
              f" | عند أربع دفعات {book.count(4)} | البتّات عندئذ {book.fixed_bits(4)}")
    one_each = BatchReceipts(Shipment(((3, 1), (5, 1))), allow_zero=True)
    print("علبة عند كل من معدلين، وأربع دفعات | السجلات الثلاثة")
    for tag in range(one_each.count(4)):
        print(one_each.decode(tag, 4))
