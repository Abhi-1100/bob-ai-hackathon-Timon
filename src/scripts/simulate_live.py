"""Replay a CSV file into TimonTrack's push ingestion endpoint."""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--min-delay", type=float, default=0.1)
    parser.add_argument("--max-delay", type=float, default=1.0)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/ingest/events")
    parser.add_argument("--batch-size", type=int, default=1)
    return parser.parse_args()


def send(url: str, api_key: str, events: list[dict[str, str]]) -> dict:
    request = Request(
        url,
        data=json.dumps({"events": events}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    args = parse_args()
    if args.min_delay < 0 or args.max_delay < args.min_delay:
        raise SystemExit("Invalid delay range")
    if not 1 <= args.batch_size <= 1000:
        raise SystemExit("--batch-size must be between 1 and 1000")

    with args.file.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    total = {"received": 0, "accepted": 0, "rejected": 0}
    for offset in range(0, len(rows), args.batch_size):
        batch = rows[offset:offset + args.batch_size]
        try:
            result = send(args.url, args.api_key, batch)
        except (HTTPError, URLError) as exc:
            raise SystemExit(f"Ingestion request failed: {exc}") from exc
        for key in total:
            total[key] += int(result.get(key, 0))
        print(f"sent={offset + len(batch)}/{len(rows)} result={result}", flush=True)
        if offset + args.batch_size < len(rows):
            time.sleep(random.uniform(args.min_delay, args.max_delay))
    print(f"complete={total}")


if __name__ == "__main__":
    main()
