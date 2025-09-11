from obelisk.asynchronous.core import QueryParams

def test_query_param_serialize():
    q = QueryParams(dataset="83989232", filter_="(metric=='smartphone.application::string')", dataType='string')
    dump = q.to_dict()
    assert "filter" in dump
