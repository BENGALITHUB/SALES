"""Command-line interface for the lead generation agent.

Example:
    python main.py --pincode 700075 --domain restaurant --min-records 20
    python main.py --city Kolkata --domain restaurant --min-records 20
"""

from __future__ import annotations

import argparse
import sys

import config
import places
from lead_generator import OPTIONAL_CONTACT_FIELDS, collect_leads


def main() -> None:
    parser = argparse.ArgumentParser(description="Local business lead generation agent")
    parser.add_argument("--pincode", default="", help="Optional postal/pin code to search")
    parser.add_argument("--city", default="", help="Optional city to search")
    parser.add_argument(
        "--domain",
        required=True,
        help="Business category, for example: restaurant, gym, salon",
    )
    parser.add_argument(
        "--min-records",
        type=int,
        default=config.MIN_RECORDS,
        help="Minimum number of records to attempt",
    )
    parser.add_argument(
        "--require",
        nargs="+",
        default=[],
        choices=OPTIONAL_CONTACT_FIELDS,
        help="Only keep leads that also have these contacts, e.g. --require email website",
    )
    args = parser.parse_args()

    def print_progress(event: dict) -> None:
        if event.get("stage") in {"searching", "processing"}:
            print(
                f"Page {event.get('current_page', 0)} | "
                f"Leads: {len(event.get('records') or [])} | "
                f"Candidates: {event.get('total_candidates', 0)}",
                end="\r",
                flush=True,
            )

    try:
        result = collect_leads(
            pincode=args.pincode,
            domain=args.domain,
            min_records=args.min_records,
            progress_callback=print_progress,
            export_excel=True,
            required_fields=args.require,
            city=args.city,
        )
    except (ValueError, places.PlacesAPIError) as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print()
    print(result["message"])
    if result["output_path"]:
        print(f"Excel file: {result['output_path']}")


if __name__ == "__main__":
    main()
