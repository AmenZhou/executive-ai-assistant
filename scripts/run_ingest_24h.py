"""Run email ingest for the last 24 hours in smaller time chunks to avoid OpenAI rate limits."""
import argparse
import asyncio
import subprocess
import sys
import time
from typing import Optional


def run_chunk(
    minutes_since: int,
    minutes_until: int,
    url: Optional[str],
    rerun: int,
    early: int,
    delay: int,
):
    print(f"\n⏳ Processing window: {minutes_until}–{minutes_since} minutes ago...")
    cmd = [
        sys.executable,
        "scripts/run_ingest.py",
        "--minutes-since", str(minutes_since),
        "--minutes-until", str(minutes_until),
        "--rerun", str(rerun),
        "--early", str(early),
    ]
    if url:
        cmd += ["--url", url]

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"⚠️  Chunk {minutes_until}–{minutes_since} min ago exited with code {result.returncode}")

    if delay > 0:
        print(f"💤 Waiting {delay}s before next chunk...")
        time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest last 24 hours of emails in smaller time chunks."
    )
    parser.add_argument("--url", type=str, default=None, help="LangGraph deployment URL")
    parser.add_argument("--chunk-size", type=int, default=120, help="Minutes per chunk (default: 120)")
    parser.add_argument("--total-minutes", type=int, default=1440, help="Total minutes to look back (default: 1440 = 24h)")
    parser.add_argument("--delay", type=int, default=30, help="Seconds to wait between chunks (default: 30)")
    parser.add_argument("--rerun", type=int, default=1, help="Whether to rerun already-seen emails (default: 1)")
    parser.add_argument("--early", type=int, default=0, help="Whether to stop early on seen emails (default: 0)")
    parser.add_argument("--minutes-until", type=int, default=0, help="End of window in minutes ago (0 = now, default: 0)")
    args = parser.parse_args()

    chunk_size = args.chunk_size
    total = args.total_minutes
    start = args.minutes_until
    chunks = range(start, start + total, chunk_size)
    total_chunks = len(list(chunks))

    print(f"🚀 Running {total_chunks} chunks of {chunk_size} min over {total} min total")

    for i, minutes_until in enumerate(range(start, start + total, chunk_size)):
        minutes_since = minutes_until + chunk_size
        print(f"\n[{i + 1}/{total_chunks}]", end="")
        run_chunk(
            minutes_since=minutes_since,
            minutes_until=minutes_until,
            url=args.url,
            rerun=args.rerun,
            early=args.early,
            delay=args.delay if minutes_since < total else 0,
        )

    print("\n✅ Done processing all chunks.")


if __name__ == "__main__":
    main()
