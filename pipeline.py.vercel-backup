"""
End-to-End Outreach Pipeline Orchestrator.
Coordinates:
Discovery -> Filtering & Classification -> Profile Enrichment -> AI Personalization -> Sending Layer -> Outreach Tracking & Export.
"""

import os
import csv
import json
from typing import List, Dict, Any, Optional, Tuple

from models import InfluencerRecord, FilterCriteria, PersonalizedOutreach, OutreachLog
from database import Database
from discovery.collector import InfluencerDiscoveryEngine
from filtering.classifier import InfluencerClassifier
from enrichment.enricher import ProfileEnricher
from personalization.generator import AIPersonalizationEngine
from sending.dispatcher import OutreachDispatcher


class OutreachPipeline:
    """
    Main orchestrator for the Automated Micro-Influencer Outreach System.
    """

    def __init__(self, db_path: str = "data/outreach_system.db", company_name: str = "AuraFlow Collective"):
        self.db = Database(db_path)
        self.discovery_engine = InfluencerDiscoveryEngine()
        self.classifier = InfluencerClassifier()
        self.enricher = ProfileEnricher()
        self.personalizer = AIPersonalizationEngine(company_name=company_name)
        self.dispatcher = OutreachDispatcher(self.db, mode="SIMULATED")

    def run_full_pipeline(
        self, criteria: Optional[FilterCriteria] = None, send_mode: str = "SIMULATED"
    ) -> Dict[str, Any]:
        """
        Executes the entire 7-stage outreach workflow from discovery to tracking & exports.
        """
        self.dispatcher.mode = send_mode.upper()

        # Step 1: Discovery (50+ profiles)
        discovered = self.discovery_engine.discover_all()
        self.db.save_influencers(discovered)

        # Step 2: Filtering & Classification
        qualified, disqualified, filter_report = self.classifier.classify_all(discovered, criteria)
        self.db.save_influencers(discovered)

        # Step 3: Profile Enrichment
        enriched_qualified = self.enricher.enrich_batch(qualified)
        self.db.save_influencers(enriched_qualified)

        # Step 4: AI Message Personalization (Email + Instagram DM)
        outreach_messages = []
        for inf in enriched_qualified:
            msg = self.personalizer.generate_outreach(inf)
            self.db.save_outreach_message(msg)
            outreach_messages.append((inf, msg))
        self.db.save_influencers(enriched_qualified)

        # Step 5: Sending Layer (with Anti-duplicate checks)
        dispatch_logs = []
        for inf, msg in outreach_messages:
            log = self.dispatcher.dispatch_email(inf, msg)
            dispatch_logs.append(log)

        # Step 6: Export Deliverable Datasets
        self.export_all()

        # Step 7: Compile Run Summary
        stats = self.db.get_stats()
        return {
            "status": "success",
            "summary": {
                "discovered_count": len(discovered),
                "qualified_count": len(qualified),
                "disqualified_count": len(disqualified),
                "messages_generated": len(outreach_messages),
                "emails_dispatched": len([l for l in dispatch_logs if l.status in ["Sent", "Simulated"]]),
                "emails_skipped": len([l for l in dispatch_logs if l.status == "Skipped"]),
                "filter_audit": filter_report
            },
            "stats": stats
        }

    def export_influencer_dataset(
        self,
        csv_path: str = "data/influencer_dataset.csv",
        json_path: str = "data/influencer_dataset.json"
    ):
        """
        Exports all discovered & processed influencers matching the recommended assignment format:
        Name, Platform, Followers, Engagement, Niche, Email, Profile URL, Content Theme, Status
        """
        os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
        influencers = self.db.get_all_influencers()

        # 1. Export CSV
        headers = [
            "Name",
            "Platform",
            "Followers",
            "Engagement (%)",
            "Niche",
            "Email",
            "Profile URL",
            "Content Theme",
            "Status",
            "Audience Age",
            "Audience Gender",
            "Audience Geography",
            "Filter Passed",
            "Filter Reasons"
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for inf in influencers:
                writer.writerow([
                    inf.name,
                    inf.platform,
                    inf.followers,
                    f"{inf.engagement_rate}%",
                    inf.niche,
                    inf.email,
                    inf.profile_url,
                    ", ".join(inf.content_themes) if inf.content_themes else "",
                    inf.status,
                    inf.audience_age or "",
                    inf.audience_gender or "",
                    inf.audience_geography or "",
                    "YES" if inf.filter_passed else "NO",
                    "; ".join(inf.filter_reasons) if inf.filter_reasons else ""
                ])

        # 2. Export JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([inf.to_dict() for inf in influencers], f, indent=2)

    def export_outreach_tracker(
        self,
        csv_path: str = "data/outreach_tracker.csv",
        json_path: str = "data/outreach_tracker.json"
    ):
        """
        Exports the outreach tracker log matching assignment specifications:
        Influencer, Email, Message Generated, Sent Date, Status, Channel, Delivery Notes
        """
        os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
        logs = self.db.get_outreach_logs()

        # 1. Export CSV
        headers = [
            "Influencer",
            "Email",
            "Message Generated",
            "Sent Date",
            "Status",
            "Channel",
            "Email Pitch (60-90 words)",
            "Instagram DM (15-30 words)",
            "Delivery Notes"
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for log in logs:
                writer.writerow([
                    log.influencer_name,
                    log.email,
                    log.message_generated_type,
                    log.sent_date,
                    log.status,
                    log.channel,
                    log.email_pitch,
                    log.instagram_dm,
                    log.delivery_notes
                ])

        # 2. Export JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([log.to_dict() for log in logs], f, indent=2)

    def export_all(self):
        self.export_influencer_dataset()
        self.export_outreach_tracker()
