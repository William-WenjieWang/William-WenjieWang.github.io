#!/usr/bin/env python3
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
COVER_DIR = ROOT / "image" / "bili-covers"
API = "https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
}


def fetch_json(url):
    request = Request(url, headers=HEADERS)
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url, destination):
    request = Request(url, headers=HEADERS)
    with urlopen(request, timeout=20) as response:
        destination.write_bytes(response.read())


def main():
    if not INDEX.exists():
        print(f"missing index.html: {INDEX}", file=sys.stderr)
        return 1

    html = INDEX.read_text(encoding="utf-8")
    bvids = sorted(set(re.findall(r"bvid=(BV[0-9A-Za-z]+)", html)))
    if not bvids:
        print("no bvid found")
        return 0

    COVER_DIR.mkdir(parents=True, exist_ok=True)
    successes = []
    failures = []

    for bvid in bvids:
        destination = COVER_DIR / f"{bvid}.jpg"
        try:
            info = fetch_json(API.format(bvid=bvid))
            if info.get("code") != 0:
                raise RuntimeError(info.get("message") or f"api code {info.get('code')}")

            pic = (info.get("data") or {}).get("pic")
            if not pic:
                raise RuntimeError("missing data.pic")

            if pic.startswith("//"):
                pic = "https:" + pic

            download_file(pic, destination)
            successes.append((bvid, str(destination.relative_to(ROOT))))
            print(f"OK   {bvid} -> {destination.relative_to(ROOT)}")
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError, OSError) as exc:
            failures.append((bvid, str(exc)))
            print(f"FAIL {bvid}: {exc}")

        time.sleep(0.25)

    print("\nSummary")
    print(f"success: {len(successes)}")
    print(f"failed: {len(failures)}")
    if failures:
        print("failures:")
        for bvid, reason in failures:
            print(f"- {bvid}: {reason}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
