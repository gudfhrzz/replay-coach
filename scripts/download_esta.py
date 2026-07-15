"""ESTA 데이터셋 일부를 내려받는다 (프로토타입용 서브셋).

사용법:
    uv run python scripts/download_esta.py -n 40 -o data/esta [--subset lan|online]

출처: https://github.com/pnxenopoulos/esta (CC BY-SA 4.0)
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

API = "https://api.github.com/repos/pnxenopoulos/esta/contents/data/{subset}"
RAW = "https://raw.githubusercontent.com/pnxenopoulos/esta/main/data/{subset}/{name}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=40, help="내려받을 파일 수")
    ap.add_argument("-o", "--out", default="data/esta")
    ap.add_argument("--subset", default="lan", choices=["lan", "online"])
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(API.format(subset=args.subset)) as r:
        files = [f["name"] for f in json.load(r) if f["name"].endswith(".json.xz")]

    targets = files[: args.n]
    for i, name in enumerate(targets, 1):
        dest = out / name
        if dest.exists():
            print(f"[{i}/{len(targets)}] 있음: {name}")
            continue
        print(f"[{i}/{len(targets)}] 다운로드: {name}")
        urllib.request.urlretrieve(RAW.format(subset=args.subset, name=name), dest)
    print(f"완료: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
