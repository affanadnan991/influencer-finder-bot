"""Command-line entrypoint for the influencer discovery bot."""

import argparse
from discovery_engine.engine import DiscoveryEngine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Instagram Influencer Finder — Find profiles by keywords in followings' bios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single keyword
  python collector_runner.py --target "nike" --keyword "fitness"

  # Multiple keywords (up to 7) — if ANY matches, profile is saved
  python collector_runner.py --target "nike" --keyword "fitness" "gym" "workout"

  # More followings harvest karo
  python collector_runner.py --target "nike" --keyword "food" "blogger" --max-following 500
        """,
    )
    parser.add_argument("--target", required=True, help="Instagram username jis ke followings check karne hain")
    parser.add_argument(
        "--keyword",
        nargs="*",
        default=[],
        help="Keywords jo bio mein dhundne hain (max 7, case-insensitive). Optional — agar na do to sab profiles save honge",
    )
    parser.add_argument("--max-following", type=int, default=200, help="Maximum followings to harvest (default: 200)")
    args = parser.parse_args()

    # Limit to 7 keywords
    keywords = args.keyword[:7] if args.keyword else []

    engine = DiscoveryEngine(
        target=args.target,
        keywords=keywords,
    )
    results = engine.discover(max_following=args.max_following)

    print(f"\n--- Final Report ---")
    report = engine.get_report()
    for key, value in report["counters"].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
