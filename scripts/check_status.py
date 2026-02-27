"""Check the processing status of all email threads."""
import argparse
import asyncio
from langgraph_sdk import get_client


async def main(url: str, limit: int):
    client = get_client(url=url)

    counts = {"idle": 0, "busy": 0, "interrupted": 0, "error": 0}
    failed_threads = []
    pending_threads = []

    offset = 0
    while True:
        threads = await client.threads.search(limit=100, offset=offset)
        if not threads:
            break

        for thread in threads:
            status = thread["status"]
            counts[status] = counts.get(status, 0) + 1

            if status == "error":
                runs = await client.runs.list(thread["thread_id"], limit=5)
                last_run = runs[0] if runs else None
                failed_threads.append({
                    "thread_id": thread["thread_id"],
                    "subject": thread.get("metadata", {}).get("email_id", "unknown"),
                    "run_status": last_run["status"] if last_run else "no runs",
                    "attempts": len(runs),
                })
            elif status == "busy":
                pending_threads.append(thread["thread_id"])

        if len(threads) < 100:
            break
        offset += 100

    total = sum(counts.values())
    print(f"\n{'='*50}")
    print(f"  EMAIL PROCESSING STATUS ({total} threads)")
    print(f"{'='*50}")
    print(f"  ✅ Done (idle):        {counts.get('idle', 0)}")
    print(f"  ⏳ In progress (busy): {counts.get('busy', 0)}")
    print(f"  ⚠️  Interrupted:        {counts.get('interrupted', 0)}")
    print(f"  ❌ Failed (error):     {counts.get('error', 0)}")
    print(f"{'='*50}")

    if pending_threads:
        print(f"\n⏳ Still processing ({len(pending_threads)} threads)...")

    if failed_threads:
        print(f"\n❌ Failed threads ({len(failed_threads)}):")
        for t in failed_threads[:limit]:
            print(f"  thread={t['thread_id']}  attempts={t['attempts']}  last_run={t['run_status']}")
        if len(failed_threads) > limit:
            print(f"  ... and {len(failed_threads) - limit} more")

    if counts.get("error", 0) == 0 and counts.get("busy", 0) == 0:
        print("\n✅ All emails processed successfully.")
    elif counts.get("busy", 0) > 0:
        print(f"\n⏳ {counts['busy']} thread(s) still running. Re-run this script to check again.")
    if counts.get("error", 0) > 0:
        print(f"\n💡 To retry failed threads, re-run start.sh or run_ingest_24h.py with --rerun 1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check email processing status.")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:2024", help="LangGraph server URL")
    parser.add_argument("--limit", type=int, default=20, help="Max failed threads to show (default: 20)")
    args = parser.parse_args()
    asyncio.run(main(url=args.url, limit=args.limit))
