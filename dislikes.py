#!/usr/bin/env python3
"""YouTube dislike count in bulk -> CSV.

Calls the yugenox/youtube-scraper Actor on Apify with includeDislikes on, then writes one CSV
row per video: views, likes, estimated dislikes (Return YouTube Dislike) and like/dislike ratio.

Usage:
    python dislikes.py <video-url> [<video-url> ...]
    python dislikes.py --file videos.txt
    python dislikes.py --channel @veritasium --max 25
    ...add --out my.csv to choose the output file (default: dislikes.csv)

Requires Python 3.10+, `pip install -r requirements.txt`, and APIFY_TOKEN in the environment
or in a .env file next to this script.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from decimal import Decimal
from pathlib import Path

from apify_client import ApifyClient

ACTOR = "yugenox/youtube-scraper"

COLUMNS = [
    "video_id", "title", "url", "channel", "published_at", "views", "likes",
    "dislikes_estimated", "like_dislike_ratio", "like_percent", "ryd_rating",
]


def load_dotenv(path: Path = Path(__file__).with_name(".env")) -> None:
    """Minimal .env reader so the script has no extra dependency."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _field(run, camel: str, snake: str):
    """apify-client v1/v2 return dicts, v3 returns a model object. Support both."""
    return run[camel] if isinstance(run, dict) else getattr(run, snake)


def ratio(likes, dislikes) -> str:
    if likes is None or not dislikes:
        return ""
    return f"{likes / dislikes:.1f}"


def like_percent(likes, dislikes) -> str:
    if likes is None or dislikes is None or likes + dislikes == 0:
        return ""
    return f"{likes / (likes + dislikes) * 100:.1f}"


def to_row(v: dict) -> dict:
    likes = v.get("likes") if isinstance(v.get("likes"), int) else None
    dislikes = v.get("dislikes") if isinstance(v.get("dislikes"), int) else None
    rating = v.get("rating")
    return {
        "video_id": v.get("id"),
        "title": v.get("title"),
        "url": v.get("url"),
        "channel": v.get("channelName"),
        "published_at": v.get("publishedAt") or v.get("date"),
        "views": v.get("viewCount"),
        "likes": likes,
        "dislikes_estimated": dislikes,
        "like_dislike_ratio": ratio(likes, dislikes),
        "like_percent": like_percent(likes, dislikes),
        "ryd_rating": f"{rating:.2f}" if isinstance(rating, (int, float)) else "",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Bulk YouTube dislike counts to CSV")
    p.add_argument("urls", nargs="*", help="YouTube video URLs")
    p.add_argument("--file", help="text file with one video URL per line")
    p.add_argument("--channel", action="append", default=[], help="channel name, @handle or URL")
    p.add_argument("--max", type=int, default=20, help="max videos per channel (default 20)")
    p.add_argument("--out", default="dislikes.csv", help="output CSV path")
    p.add_argument("--max-charge", type=float, default=1.0, help="cost cap for the run in USD")
    args = p.parse_args()

    urls = list(args.urls)
    if args.file:
        lines = Path(args.file).read_text().splitlines()
        urls += [s.strip() for s in lines if s.strip() and not s.strip().startswith("#")]
    if not urls and not args.channel:
        p.error("give at least one video URL, --file videos.txt, or --channel @handle")

    load_dotenv()
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("Set APIFY_TOKEN (see .env.example)")

    run_input: dict = {"includeDislikes": True, "maxItems": args.max}
    if urls:
        run_input["startUrls"] = urls
    if args.channel:
        run_input["channels"] = args.channel

    client = ApifyClient(token)
    print(f"Running {ACTOR} ...", file=sys.stderr)
    # max_total_charge_usd caps what this run can cost you (pay-per-event Actors only).
    run = client.actor(ACTOR).call(
        run_input=run_input, max_total_charge_usd=Decimal(str(args.max_charge))
    )
    if run is None:
        sys.exit("The run did not finish")
    print(f"Run {_field(run, 'id', 'id')} finished: {_field(run, 'status', 'status')}", file=sys.stderr)

    items = list(client.dataset(_field(run, "defaultDatasetId", "default_dataset_id")).iterate_items())
    videos = [it for it in items if not it.get("error")]
    for e in (it for it in items if it.get("error")):
        print(f"skipped {e.get('input') or e.get('url') or e.get('id')}: {e['error']}", file=sys.stderr)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for v in videos:
            w.writerow(to_row(v))
    print(f"Wrote {len(videos)} videos to {args.out}", file=sys.stderr)
    print("Dislike counts are estimates from Return YouTube Dislike (returnyoutubedislike.com).", file=sys.stderr)


if __name__ == "__main__":
    main()
