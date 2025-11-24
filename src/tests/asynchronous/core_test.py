from obelisk.asynchronous.core import QueryParams
from obelisk.types.core import Filter, Comparison


def test_query_param_serialize():
    q = QueryParams(
        dataset="83989232",
        filter_="(metric=='smartphone.application::string')",
        dataType="string",
    )
    dump = q.to_dict()
    assert "filter" in dump


def test_comma_separate_string():
    data = QueryParams(
        dataset="dummy",
        groupBy=["dataset", "timestamp"],
        fields=["timestamp", "labels", "value"],
        orderBy=["timestamp", "value"],
        dataType="string",
    ).to_dict()

    assert data["fields"] == "timestamp,labels,value"
    assert data["groupBy"] == "dataset,timestamp"
    assert data["orderBy"] == "timestamp,value"



def test_filter_serialize():
    filter_ = Filter().add_and(Comparison.equal("metric", "smartphone.acceleration::number[]"), Comparison.greater_equal("timestamp", 123456))
    q = QueryParams(
        dataset="83989232",
        filter_=filter_,
        dataType="number[]",
    )
    dump = q.to_dict()
    assert "filter" in dump
