"""
Timeslicing module. Offers discrete stepping through time and resolving time step placeholders in patterns.

The Dekad class implements dekadal time stepping.

Author: Rob Marjot, March 2023
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional, Union

from dateutil.relativedelta import relativedelta


class Slice(ABC):
    """
    Base class for time slicing cursor. Implementing classes implement a scheme, such as dekadal
    """

    def __init__(self) -> None:
        super().__init__()

    def resolve(self, pattern: str, m: Optional[Dict[str, str]] = None) -> str:
        pattern = pattern.replace("$(yyyy)", str(self.year))
        pattern = pattern.replace("$(mm)", f"{self.month:02d}")
        pattern = pattern.replace("$(dd)", f"{self.day:02d}")
        if m is not None:
            for key, value in m.items():
                pattern = pattern.replace(f"$({key})", value)
        return pattern

    @property
    @abstractmethod
    def year(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def seqno(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def month(self) -> int:
        """Month part for date"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def day(self) -> int:
        """Day in month part for cursor"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def slice_count(self):
        raise NotImplementedError()

    def equals(self, otherSlice: "Slice") -> bool:
        return self.year == otherSlice.year and self.seqno == otherSlice.year

    def greater_than(self, otherSlice: "Slice") -> bool:
        return self.year > otherSlice.year or (
            self.year == otherSlice.year and self.seqno > otherSlice.seqno
        )

    def diff(self, other_slice: "Slice") -> int:
        return ((self.year - other_slice.year) * self.slice_count) + (
            self.seqno - other_slice.seqno
        )

    def subtract(self, diff) -> "Slice":
        return self.add(-1 * diff)

    @abstractmethod
    def add(self, deltaSlices: int) -> "Slice":
        raise NotImplementedError()

    def next(self) -> "Slice":
        return self.add(1)

    def prev(self) -> "Slice":
        return self.add(-1)

    def next_year(self) -> "Slice":
        return self.add(self.slice_count)

    def prev_year(self) -> "Slice":
        return self.add(-1 * self.slice_count)

    def get_slice_start(self) -> datetime:
        return datetime(self.year, self.month, self.day)

    @abstractmethod
    def get_slice_mid(self) -> datetime:
        raise NotImplementedError()

    def get_slice_end(self) -> datetime:
        return self.next().get_slice_start() - relativedelta(seconds=1)

    def starts_before(self, dte: Union[datetime, "Slice"]) -> bool:
        if isinstance(dte, Slice):
            dte = dte.get_slice_end()
        return self.get_slice_start() < dte

    def ends_after(self, dte: Union[datetime, "Slice"]) -> bool:
        if isinstance(dte, Slice):
            dte = dte.get_slice_end()
        return self.get_slice_end() > dte

    @abstractmethod
    def to_string(self, fmt) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return "{}{:02d}{:02d}".format(self.year, self.month, self.day)

    def __add__(self, diff: int) -> "Slice":
        return self.add(diff)


class Dekad(Slice):
    """
    Implements the dekadal time slicing scheme. A Dekad instance represents a dekad.
    """

    def __init__(self, date_or_year: Union[datetime, int] = None, seqno: int = None) -> None:
        super().__init__()
        if not isinstance(date_or_year, datetime):
            assert isinstance(date_or_year, int)
            assert isinstance(seqno, int)
            self.__year = date_or_year
            self.__seqno = seqno
        else:
            assert seqno is None
            self.__year = date_or_year.year
            self.__seqno = ((date_or_year.month - 1) * 3) + (
                min(2, (date_or_year.day - 1) // 10) + 1
            )

    @property
    def year(self) -> int:
        return self.__year

    @property
    def seqno(self) -> int:
        return self.__seqno

    @property
    def month(self) -> int:
        return ((self.__seqno - 1) // 3) + 1

    @property
    def day(self) -> int:
        """Day in month part for cursor"""
        return (((self.__seqno - 1) % 3) * 10) + 1

    @property
    def slice_count(self):
        return 36

    def resolve(self, pattern: str, m: Optional[Dict[str, str]] = None) -> str:
        return super().resolve(pattern, m).replace("$(mdekad)", f"{(((self.seqno-1)%3)+1):02d}")

    def add(self, diff) -> Slice:
        dekads = (self.year * 36) + self.seqno + diff
        if (dekads % 36) == 0:
            return Dekad((dekads // 36) - 1, 36)
        else:
            return Dekad(dekads // 36, (dekads % 36))

    def get_slice_mid(self) -> datetime:
        return self.get_slice_start() + relativedelta(days=4)

    def to_string(self, fmt):
        return self.get_slice_start().strftime(fmt)
