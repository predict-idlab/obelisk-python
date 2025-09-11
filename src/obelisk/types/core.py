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
(('source'=='test source';'metricType'=in=('number', 'number[]')),'timestamp'<'2025-09-09T14:48:48')
"""
from __future__ import annotations
from abc import ABC
from datetime import datetime
from typing import Any, Iterable, List


FieldName = str
"""https://obelisk.pages.ilabt.imec.be/obelisk-core/query.html#available-data-point-fields
Field names are not validated at this time, due to the inherent complexity.
"""


class Constraint(ABC):
    """
    Constraints are simply groups of :class:`Comparison`,
    such as :class:`And`, or :class:`Or`.

    These constraints always enclose their contents in parentheses,
    to avoid confusing precendence situations in serialised format.
    """
    pass


class Comparison():
    """
    Comparisons are the basic items of a :class:`Filter`.
    They consist of a field name, operator, and possibly a value on the right.

    It is strongly suggested you create comparisons by using the staticmethods
    on this class, rather than trying to construct them yourselves.

    When serializing to RSQL format,
    each argument is single quoted as to accept any otherwise reserved characters,
    and serialised using :func:`str`.
    """
    left: FieldName
    right: Any
    op: str

    def __init__(self, left: FieldName, right: Any, op: str):
        self.left = left
        self.right = right
        self.op = op

    def __str__(self) -> str:
        right = self._sstr(self.right)
        if not right.startswith('(') and len(right) > 0:
            right = f"'{right}'"

        return f"'{self.left}'{self.op}{right}"

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
    """
    Filter is an easier way to programatically create filters for the Obelisk CORE platform.

    We still recommend you familiarise yourself with the CORE filter documentation,
    as not everything is typechecked.
    Specifically, the left hand side of any comparison is left unchecked.
    Checking this would be borderline impossible with the optional arguments to some fields,
    and the dot notation for labels.

    As this field is not checked, we also do not check whether the type of left operand
    and right operand make sense in the provided comparison.
    """
    content: Item | None = None

    def __init__(self, content: Constraint | None = None):
        self.content = content

    def __str__(self) -> str:
        return str(self.content)

    def add_and(self, *other: Item) -> Filter:
        """
        Encloses the current filter contents, if any,
        in an :class:`And`, along with any other provided Items.

        >>> str(Filter(Comparison.not_null('labels.username'))
        ... .add_and(Comparison.equal('labels.username', 'stpletin'), Comparison.less_equal('timestamp', '2025-01-12T00:00:00Z')))
        "('labels.username'=notnull=;'labels.username'=='stpletin';'timestamp'<='2025-01-12T00:00:00Z')"
        """
        if self.content is None:
            self.content = And(*other)
        else:
            self.content = And(self.content, *other)
        return self

    def add_or(self, *other: Item) -> Filter:
        """
        Encloses the current filter contents, if any,
        in an :class:`Or`, along with any other provided Items.

        >>> str(Filter(Comparison.not_null('labels.username'))
        ... .add_or(Comparison.equal('labels.username', 'stpletin'), Comparison.less_equal('timestamp', '2025-01-12T00:00:00Z')))
        "('labels.username'=notnull=,'labels.username'=='stpletin','timestamp'<='2025-01-12T00:00:00Z')"
        """
        if self.content is None:
            self.content = Or(*other)
        else:
            self.content = Or(self.content, *other)
        return self
