import gzip
import json

import httpx
import pytest

from collect.faceit import DATA_BASE, DOWNLOAD_ENDPOINT, PAGE_SIZE_MAX, FaceitClient


def _client(handler) -> FaceitClient:
    return FaceitClient(
        api_key="data-key",
        downloads_key="dl-key",
        transport=httpx.MockTransport(handler),
    )


def test_championship_matches_request_shape():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["Authorization"]
        return httpx.Response(200, json={"items": []})

    _client(handler).championship_matches("champ-1", type="past", offset=20, limit=50)
    assert seen["url"].startswith(f"{DATA_BASE}/championships/champ-1/matches")
    assert "type=past" in seen["url"] and "offset=20" in seen["url"] and "limit=50" in seen["url"]
    assert seen["auth"] == "Bearer data-key"


def test_iter_matches_paginates_until_short_page():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params["offset"])
        calls.append(offset)
        n = PAGE_SIZE_MAX if offset == 0 else 3  # 두 번째 페이지가 마지막
        return httpx.Response(
            200, json={"items": [{"match_id": f"m{offset + i}"} for i in range(n)]}
        )

    matches = list(_client(handler).iter_matches("hub", "hub-1"))
    assert len(matches) == PAGE_SIZE_MAX + 3
    assert calls == [0, PAGE_SIZE_MAX]


def test_demo_resource_urls_falls_back_to_match_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/matches/m1")
        return httpx.Response(200, json={"match_id": "m1", "demo_url": ["https://demos.faceit.com/x.dem.gz"]})

    c = _client(handler)
    assert c.demo_resource_urls({"match_id": "m1"}) == ["https://demos.faceit.com/x.dem.gz"]
    # demo_url이 이미 있으면 추가 조회 없음 (핸들러 호출 시 assert에 걸림)
    assert c.demo_resource_urls({"demo_url": ["u"]}) == ["u"]
    assert c.demo_resource_urls({"match_id": "m1", "demo_url": []}) == []


def test_signed_demo_url_posts_resource_url():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == DOWNLOAD_ENDPOINT
        assert request.headers["Authorization"] == "Bearer dl-key"
        assert json.loads(request.content) == {"resource_url": "res-url"}
        return httpx.Response(200, json={"payload": {"download_url": "https://signed"}})

    assert _client(handler).signed_demo_url("res-url") == "https://signed"


def test_signed_demo_url_requires_downloads_key():
    c = FaceitClient(api_key="data-key", downloads_key="", transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    with pytest.raises(RuntimeError, match="FACEIT_DOWNLOADS_KEY"):
        c.signed_demo_url("res-url")


def test_download_demo_gunzips_to_dem(tmp_path):
    dem_bytes = b"PBDEMS2\0fake-demo-content"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(200, json={"payload": {"download_url": "https://signed/f.dem.gz"}})
        return httpx.Response(200, content=gzip.compress(dem_bytes))

    dem = _client(handler).download_demo("https://demos.faceit.com/cs2/match-1.dem.gz", tmp_path)
    assert dem.name == "match-1.dem"
    assert dem.read_bytes() == dem_bytes
    assert not (tmp_path / "match-1.dem.gz").exists()  # gz는 압축 해제 후 삭제
