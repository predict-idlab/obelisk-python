from obelisk.types.core import Filter, Comparison
from datetime import datetime


def test_basic_filter():
    test_dt = datetime.now()
    f = Filter() \
        .add_and(
            Comparison.equal('source', 'test source'),
        )\
        .add_or(
            Comparison.less('timestamp', test_dt)
        )\
        .add_or(
            Comparison.is_in('metricType', ['number', 'number[]']),
        )

    expected = f"((('source'=='test source'),'timestamp'<'{test_dt.isoformat()}'),'metricType'=in=('number', 'number[]'))"
    assert str(f) == expected
