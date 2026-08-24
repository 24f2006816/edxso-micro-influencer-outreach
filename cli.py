"""
Command Line Interface (CLI) for the Automated Micro-Influencer Outreach System.
Allows running the full pipeline, individual stages, inspecting records, and exporting data.
"""

import sys
import argparse
import json
from models import FilterCriteria
from pipeline import OutreachPipeline


def print_banner():
    print("=" * 80)
    print("      EDXSO AI - AUTOMATED MICRO-INFLUENCER OUTREACH SYSTEM")
    print("=" * 80)


def print_table(headers, rows):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], min(len(str(val)), 30))
    
    fmt = " | ".join(f"{{:<{w}}}" for w in widths)
    print("-" * (sum(widths) + 3 * (len(headers) - 1)))
    print(fmt.format(*headers))
    print("-" * (sum(widths) + 3 * (len(headers) - 1)))
    for row in rows:
        truncated_row = [str(val)[:28] + ".." if len(str(val)) > 30 else str(val) for val in row]
        print(fmt.format(*truncated_row))
    print("-" * (sum(widths) + 3 * (len(headers) - 1)))


def main():
    parser = argparse.ArgumentParser(description="Automated Micro-Influencer Outreach System")
    parser.add_argument("--run-all", action="store_true", help="Execute the complete end-to-end outreach pipeline")
    parser.add_argument("--discover", action="store_true", help="Run influencer discovery layer (50+ profiles)")
    parser.add_argument("--filter-only", action="store_true", help="Run filtering & classification on discovered records")
    parser.add_argument("--personalize", action="store_true", help="Generate AI outreach messages for qualified creators")
    parser.add_argument("--send", action="store_true", help="Dispatch personalized emails through sending layer")
    parser.add_argument("--export", action="store_true", help="Export dataset and outreach tracker to CSV & JSON")
    parser.add_argument("--stats", action="store_true", help="Display current database metrics and counts")
    parser.add_argument("--niche", type=str, default=None, help="Filter by specific niche (e.g. Beauty, Tech, Fitness)")
    parser.add_argument("--min-followers", type=int, default=5000, help="Minimum followers for qualification")
    parser.add_argument("--max-followers", type=int, default=100000, help="Maximum followers for qualification")
    parser.add_argument("--min-engagement", type=float, default=2.0, help="Minimum engagement rate (%%)")
    parser.add_argument("--send-mode", type=str, default="SIMULATED", choices=["SIMULATED", "SMTP"], help="Sending mode")
    parser.add_argument("--preview-messages", action="store_true", help="Preview sample generated Email & DM messages")

    args = parser.parse_args()
    print_banner()

    pipeline = OutreachPipeline()

    criteria = FilterCriteria(
        min_followers=args.min_followers,
        max_followers=args.max_followers,
        min_engagement_rate=args.min_engagement,
        allowed_niches=[args.niche] if args.niche else [
            "Fitness", "Beauty", "Fashion", "Tech", "Fintech", "Crypto", "Parenting", "Gaming", "Lifestyle"
        ]
    )

    if args.run_all or len(sys.argv) == 1:
        print("\n[*] Running Complete 7-Stage Outreach Pipeline...\n")
        res = pipeline.run_full_pipeline(criteria=criteria, send_mode=args.send_mode)
        summary = res["summary"]

        print(f"[+] 1. Discovery Completed: {summary['discovered_count']} micro-influencer profiles ingested.")
        print(f"[+] 2. Filtering & Classification: {summary['qualified_count']} qualified, {summary['disqualified_count']} disqualified.")
        print(f"[+] 3. Profile Enrichment: 100% mandatory & optional metadata standardized.")
        print(f"[+] 4. AI Message Personalization: {summary['messages_generated']} custom Email pitches (60-90w) and Instagram DMs (15-30w) generated.")
        print(f"[+] 5. Sending Layer: {summary['emails_dispatched']} emails dispatched ({args.send_mode}), {summary['emails_skipped']} skipped (anti-duplicate/no-email).")
        print(f"[+] 6. Tracking & Deliverables Exported:")
        print(f"       - data/influencer_dataset.csv & .json")
        print(f"       - data/outreach_tracker.csv & .json")

        print("\n--- Current Pipeline Statistics ---")
        for k, v in res["stats"].items():
            if isinstance(v, dict):
                print(f"  {k}:")
                for sub_k, sub_v in v.items():
                    print(f"    - {sub_k}: {sub_v}")
            else:
                print(f"  {k}: {v}")

    elif args.discover:
        print("\n[*] Running Discovery Layer...")
        records = pipeline.discovery_engine.discover_all(target_niche=args.niche)
        pipeline.db.save_influencers(records)
        print(f"[+] Discovered {len(records)} creators.")

    elif args.stats:
        stats = pipeline.db.get_stats()
        print("\n--- Pipeline Database Overview ---")
        for k, v in stats.items():
            if isinstance(v, dict):
                print(f"  {k}:")
                for sub_k, sub_v in v.items():
                    print(f"    - {sub_k}: {sub_v}")
            else:
                print(f"  {k}: {v}")

    elif args.export:
        print("\n[*] Exporting Datasets & Outreach Tracker...")
        pipeline.export_all()
        print("[+] Export completed to data/ directory.")

    if args.preview_messages:
        print("\n=== SAMPLE GENERATED PERSONALIZED MESSAGES ===")
        influencers = pipeline.db.get_all_influencers(status="Sent") or pipeline.db.get_all_influencers()
        sample_count = 0
        for inf in influencers[:3]:
            msg = pipeline.db.get_outreach_message(inf.id)
            if msg:
                sample_count += 1
                print(f"\n--- Influencer: {inf.name} ({inf.platform} | {inf.niche} | {inf.followers:,} followers) ---")
                print(f"Angle: {msg.collaboration_angle} | Model: {msg.model_used}")
                print(f"\n[A] EMAIL PITCH ({msg.email_word_count} words):\n{msg.email_pitch}")
                print(f"\n[B] INSTAGRAM DM ({msg.dm_word_count} words):\n{msg.instagram_dm}")
                print("-" * 60)
        if sample_count == 0:
            print("No generated messages found. Run with --run-all to execute pipeline.")


if __name__ == "__main__":
    main()
