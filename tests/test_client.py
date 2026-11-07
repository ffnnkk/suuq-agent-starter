import httpx
import pytest

from suuq_client import SuuqClient, SuuqError


def _client(handler) -> SuuqClient:
    return SuuqClient(base_url="https://x.test", transport=httpx.MockTransport(handler))


def test_search_drops_empty_fields():
    seen = {}

    def h(req):
        seen["body"] = req.read().decode()
        return httpx.Response(200, json=[])

    _client(h).search("abc")
    assert seen["body"] == '{"query":"abc","page_size":20}'


def test_register_stores_token_and_sends_it():
    def h(req):
        if req.url.path == "/agents/register":
            return httpx.Response(201, json={"token": "T", "api_key": "K"})
        assert req.headers["authorization"] == "Bearer T"
        return httpx.Response(200, json={"id": "1"})

    c = _client(h)
    c.register("starter-abcd")
    assert c.me() == {"id": "1"}


def test_error_detail_is_raised():
    c = _client(lambda r: httpx.Response(403, json={"detail": "Trial agents are read-only."}))
    with pytest.raises(SuuqError) as e:
        c.create_listing("a", 1.0, 1)
    assert e.value.status == 403 and "read-only" in e.value.detail


def test_http_base_url_is_rejected():
    with pytest.raises(ValueError):
        SuuqClient(base_url="http://api.example.com")
    SuuqClient(base_url="http://localhost:7500")  # lokal erlaubt


def test_error_with_json_list_body_does_not_crash():
    c = _client(lambda r: httpx.Response(500, json=["boom"]))
    with pytest.raises(SuuqError):
        c.me()
