"""
Types specific to Obelisk CORE, including an RSQL filter implementation

To create a filter, look at :class:`Filter`.
Example:

>>> from datetime import datetime
>>> f = (Filter().add_and(
...     Comparison.equal('source', 'test source'),
...     Comparison.is_in('metricType', ['number', 'number[]']),
... ).add_or(
...     Comparison.less('timestamp', datetime.fromtimestamp(1757422128))
... ))
>>> print(f)
((('source'=='test source');('metricType'=in=('number', 'number[]'))),('timestamp'<'2025-09-09T14:48:48'))
"""
from __future__ import annotations
from abc import ABC
from datetime import datetime
from typing import Any, Iterable, List


FieldName = str # TODO: validate field names?
"""https://obelisk.pages.ilabt.imec.be/obelisk-core/query.html#available-data-point-fields
Field names are not validated at this time, due to the inherent complexity.
"""


class Constraint(ABC):
    pass


class Comparison():
    left: FieldName
    right: Any
    op: str

    def __init__(self, left: FieldName, right: Any, op: str):
        self.left = left
        self.right = right
        self.op = op

    def __str__(self) -> str:
        right = self._sstr(self.right)
        if not right.startswith('('):
            right = f"'{right}'"

        return f"('{self.left}'{self.op}{right})"

    @staticmethod
    def _sstr(item: Any):
        """Smart string conversion"""
        if isinstance(item, datetime):
            return item.isoformat()
        return str(item)

    @staticmethod
    def _iterable_to_group(iter: Iterable[Any]) -> str:
        """Produces a group of the form ("a","b")"""
        return str(tuple([Comparison._sstr(x) for x in iter]))

    @classmethod
    def equal(cls, left: FieldName, right: Any) -> Comparison:
        return Comparison(left, right, "==")

    @classmethod
    def not_equal(cls, left: FieldName, right: Any) -> Comparison:
        return Comparison(left, right, "!=")

    @classmethod
    def less(cls, left: FieldName, right: Any) -> Comparison:
        return Comparison(left, right, "<")

    @classmethod
    def less_equal(cls, left: FieldName, right: Any) -> Comparison:
        return Comparison(left, right, "<=")

    @classmethod
    def greater(cls, left: FieldName, right: Any) -> Comparison:
        return Comparison(left, right, ">")

    @classmethod
    def greater_equal(cls, left: FieldName, right: Any) -> Comparison:
        return Comparison(left, right, ">=")

    @classmethod
    def is_in(cls, left: FieldName, right: Iterable[Any]) -> Comparison:
        return Comparison(left, cls._iterable_to_group(right), "=in=")

    @classmethod
    def is_not_in(cls, left: FieldName, right: Iterable[Any]) -> Comparison:
        return Comparison(left, cls._iterable_to_group(right), "=out=")

    @classmethod
    def null(cls, left: FieldName) -> Comparison:
        return Comparison(left, "", "=null=")

    @classmethod
    def not_null(cls, left: FieldName) -> Comparison:
        return Comparison(left, "", "=notnull=")


Item = Constraint | Comparison


class And(Constraint):
    content: List[Item]

    def __init__(self, *args: Item):
        self.content = list(args)

    def __str__(self) -> str:
        return "(" + ";".join([str(x) for x in self.content]) + ")"


class Or(Constraint):
    content: List[Item]

    def __init__(self, *args: Item):
        self.content = list(args)

    def __str__(self) -> str:
        return "(" + ",".join([str(x) for x in self.content]) + ")"


class Filter():
    content: Item | None = None

    def __init__(self, content: Constraint | None = None):
        self.content = content

    def __str__(self) -> str:
        return str(self.content)

    def add_and(self, *other: Item) -> Filter:
        if self.content is None:
            self.content = And(*other)
        else:
            self.content = And(self.content, *other)
        return self

    def add_or(self, *other: Item) -> Filter:
        if self.content is None:
            self.content = Or(*other)
        else:
            self.content = Or(self.content, *other)
        return self
