"""FACEIT 데모 수집 클라이언트 — Data API(v4) + Downloads API(v2).

승인 전 준비용 스캐폴드 (계정·키 발급은 GitHub 이슈 #1 진행 중):
- Data API(매치 목록, 매치 상세의 demo_url 조회)는 서버사이드 키만 있으면
  앱 생성 직후 바로 동작한다.
- Downloads API(signed URL 발급 → 실제 .dem.gz 다운로드)는 Downloads 스코프
  토큰이 필요하다 — 신청 심사(약 30일) 통과 후 발급.
  신청서: Docs/faceit-downloads-api-application.md

인증 (환경변수):
    FACEIT_API_KEY        — Data API 서버사이드 키
    FACEIT_DOWNLOADS_KEY  — Downloads API 액세스 토큰 (승인 후)

엔드포인트 출처: docs.faceit.com (Data API v4, Downloads API 가이드).
"""

from __future__ import annotations

import gzip
import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlparse

import httpx

DATA_BASE = "https://open.faceit.com/data/v4"
DOWNLOAD_ENDPOINT = "https://open.faceit.com/download/v2/demos/download"
PAGE_SIZE_MAX = 100  # Data API limit 파라미터 상한


class FaceitClient:
    def __init__(
        self,
        api_key: str | None = None,
        downloads_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        self._api_key = api_key or os.environ.get("FACEIT_API_KEY", "")
        self._downloads_key = downloads_key or os.environ.get("FACEIT_DOWNLOADS_KEY", "")
        self._http = httpx.Client(timeout=60, transport=transport, follow_redirects=True)

    # --- Data API (서버사이드 키) ---

    def _get(self, path: str, **params) -> dict:
        r = self._http.get(
            f"{DATA_BASE}{path}",
            params=params,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        r.raise_for_status()
        return r.json()

    def championship_matches(
        self, championship_id: str, *, type: str = "past", offset: int = 0, limit: int = PAGE_SIZE_MAX
    ) -> dict:
        return self._get(
            f"/championships/{championship_id}/matches", type=type, offset=offset, limit=limit
        )

    def hub_matches(
        self, hub_id: str, *, type: str = "past", offset: int = 0, limit: int = PAGE_SIZE_MAX
    ) -> dict:
        return self._get(f"/hubs/{hub_id}/matches", type=type, offset=offset, limit=limit)

    def match(self, match_id: str) -> dict:
        return self._get(f"/matches/{match_id}")

    def iter_matches(self, kind: str, entity_id: str, *, type: str = "past") -> Iterator[dict]:
        """championship/hub의 매치를 페이지네이션 넘어 순회한다."""
        fetch = {"championship": self.championship_matches, "hub": self.hub_matches}[kind]
        offset = 0
        while True:
            items = fetch(entity_id, type=type, offset=offset, limit=PAGE_SIZE_MAX).get("items", [])
            yield from items
            if len(items) < PAGE_SIZE_MAX:
                return
            offset += PAGE_SIZE_MAX

    def demo_resource_urls(self, match: dict) -> list[str]:
        """매치 객체(목록 항목 또는 상세)에서 데모 resource URL들을 꺼낸다.

        목록 응답에 demo_url이 없으면 상세를 한 번 더 조회한다.
        """
        urls = match.get("demo_url")
        if urls is None and "match_id" in match:
            urls = self.match(match["match_id"]).get("demo_url")
        return urls or []

    # --- Downloads API (승인 후 토큰) ---

    def signed_demo_url(self, resource_url: str) -> str:
        if not self._downloads_key:
            raise RuntimeError(
                "FACEIT_DOWNLOADS_KEY가 없습니다 — Downloads API는 신청 승인 후 사용 가능"
            )
        r = self._http.post(
            DOWNLOAD_ENDPOINT,
            json={"resource_url": resource_url},
            headers={"Authorization": f"Bearer {self._downloads_key}"},
        )
        r.raise_for_status()
        return r.json()["payload"]["download_url"]

    def download_demo(self, resource_url: str, dest_dir: Path) -> Path:
        """resource URL → signed URL 발급 → .dem.gz 다운로드 → 압축 해제한 .dem 경로."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = Path(urlparse(resource_url).path).name  # 예: 1-xxxx-1-1.dem.gz
        gz_path = dest_dir / name
        dem_path = gz_path.with_suffix("") if name.endswith(".gz") else gz_path

        signed = self.signed_demo_url(resource_url)
        with self._http.stream("GET", signed) as r:
            r.raise_for_status()
            with open(gz_path, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)

        if gz_path != dem_path:
            with gzip.open(gz_path, "rb") as src, open(dem_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            gz_path.unlink()
        return dem_path
