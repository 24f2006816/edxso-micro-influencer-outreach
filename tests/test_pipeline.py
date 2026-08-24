"""
Automated Test Suite for the Micro-Influencer Outreach System.
Validates:
1. Discovery Layer (50+ records minimum requirement)
2. Filtering & Classification Logic (Boundary conditions & reasons)
3. Profile Enrichment Data Integrity
4. AI Personalization Word Count Constraints (Email: 60-90w, DM: 15-30w)
5. Anti-Duplicate Outreach Prevention & Idempotency
6. SQLite Database & Data Export Integrity
"""

import unittest
import os
import tempfile
from models import InfluencerRecord, FilterCriteria
from database import Database
from discovery.collector import InfluencerDiscoveryEngine
from filtering.classifier import InfluencerClassifier
from enrichment.enricher import ProfileEnricher
from personalization.generator import AIPersonalizationEngine
from sending.dispatcher import OutreachDispatcher
from pipeline import OutreachPipeline


class TestMicroInfluencerOutreachPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db = Database(self.temp_db.name)
        self.discovery = InfluencerDiscoveryEngine()
        self.classifier = InfluencerClassifier()
        self.enricher = ProfileEnricher()
        self.personalizer = AIPersonalizationEngine(company_name="TestCorp AI")
        self.dispatcher = OutreachDispatcher(self.db, mode="SIMULATED")

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_01_discovery_minimum_count(self):
        """Test Requirement: Fetch at least 50 influencers for the test run."""
        records = self.discovery.discover_all()
        self.assertGreaterEqual(len(records), 50, "Discovery must return at least 50 influencer records.")
        
        # Verify required initial fields
        for r in records:
            self.assertTrue(r.id)
            self.assertTrue(r.name)
            self.assertTrue(r.platform in ["Instagram", "YouTube", "TikTok", "Twitch"])
            self.assertTrue(r.profile_url.startswith("http"))
            self.assertGreater(r.followers, 0)
            self.assertGreater(r.engagement_rate, 0.0)

    def test_02_filtering_and_classification(self):
        """Test Filtering Logic: Category, Follower Tier (5k-100k), Engagement, and Reasons."""
        criteria = FilterCriteria(min_followers=5000, max_followers=100000, min_engagement_rate=2.0)

        # Test Case 1: Valid Micro-influencer
        valid_inf = InfluencerRecord(
            id="test_valid", name="Valid Creator", platform="Instagram",
            profile_url="https://instagram.com/valid", followers=25000, engagement_rate=4.5,
            niche="Beauty", email="valid@creator.com"
        )
        res_valid = self.classifier.evaluate(valid_inf, criteria)
        self.assertTrue(res_valid.passed)
        self.assertTrue(any("Qualified" in r for r in res_valid.reasons))

        # Test Case 2: Macro Influencer (>100k)
        macro_inf = InfluencerRecord(
            id="test_macro", name="Macro Star", platform="YouTube",
            profile_url="https://youtube.com/@macro", followers=150000, engagement_rate=3.0,
            niche="Technology", email="macro@star.com"
        )
        res_macro = self.classifier.evaluate(macro_inf, criteria)
        self.assertFalse(res_macro.passed)
        self.assertTrue(any("exceeds the micro-influencer maximum" in r for r in res_macro.reasons))

        # Test Case 3: Low Engagement Rate (<2.0%)
        low_eng_inf = InfluencerRecord(
            id="test_low_eng", name="Low Eng", platform="TikTok",
            profile_url="https://tiktok.com/@low", followers=15000, engagement_rate=0.8,
            niche="Fitness", email="low@eng.com"
        )
        res_low_eng = self.classifier.evaluate(low_eng_inf, criteria)
        self.assertFalse(res_low_eng.passed)
        self.assertTrue(any("Engagement rate" in r for r in res_low_eng.reasons))

    def test_03_profile_enrichment(self):
        """Test Profile Enrichment: Mandatory fields, email validation, and strict 'Not Found' handling."""
        inf_with_email = InfluencerRecord(
            id="test_e1", name="Elena Style", platform="Instagram",
            profile_url="https://instagram.com/elena", followers=20000, engagement_rate=3.5,
            niche="Fashion", email="ELENA@FASHION.COM"
        )
        self.enricher.enrich(inf_with_email)
        self.assertEqual(inf_with_email.email, "elena@fashion.com")
        self.assertTrue(len(inf_with_email.content_themes) > 0)

        # Test invalid/missing email handling (must be 'Not Found', not guessed)
        inf_missing_email = InfluencerRecord(
            id="test_e2", name="Mystery Creator", platform="TikTok",
            profile_url="https://tiktok.com/@mystery", followers=30000, engagement_rate=4.0,
            niche="Gaming", email=""
        )
        self.enricher.enrich(inf_missing_email)
        self.assertEqual(inf_missing_email.email, "Not Found")

    def test_04_ai_personalization_word_counts(self):
        """Test Personalization: Email pitch (60-90 words) & Instagram DM (15-30 words)."""
        inf = InfluencerRecord(
            id="test_p1", name="Sarah Johnson", platform="Instagram",
            profile_url="https://instagram.com/sarahj", followers=42000, engagement_rate=5.2,
            niche="Beauty", content_themes=["Barrier Repair", "Dewy Makeup"],
            recent_posts=["My 5-Step Morning Skincare Routine"],
            email="sarah@skincarelab.com"
        )
        outreach = self.personalizer.generate_outreach(inf)
        
        # Validate Email Pitch Word Count (Strictly 60 to 90 words)
        self.assertGreaterEqual(
            outreach.email_word_count, 60,
            f"Email pitch word count ({outreach.email_word_count}) is below minimum 60 words."
        )
        self.assertLessEqual(
            outreach.email_word_count, 90,
            f"Email pitch word count ({outreach.email_word_count}) exceeds maximum 90 words."
        )

        # Validate Instagram DM Word Count (Strictly 15 to 30 words)
        self.assertGreaterEqual(
            outreach.dm_word_count, 15,
            f"Instagram DM word count ({outreach.dm_word_count}) is below minimum 15 words."
        )
        self.assertLessEqual(
            outreach.dm_word_count, 30,
            f"Instagram DM word count ({outreach.dm_word_count}) exceeds maximum 30 words."
        )

        # Verify content personalization references
        self.assertIn("Sarah", outreach.email_pitch)
        self.assertTrue(any(w in outreach.email_pitch.lower() for w in ["beauty", "skincare", "routine", "barrier"]))

    def test_05_anti_duplicate_dispatch_safeguard(self):
        """Test Sending Layer: Prevent duplicate outreach to the same creator."""
        inf = InfluencerRecord(
            id="test_dup_01", name="Duplicate Test Creator", platform="YouTube",
            profile_url="https://youtube.com/@duptest", followers=35000, engagement_rate=4.2,
            niche="Tech", email="creator@duptest.io"
        )
        self.db.save_influencer(inf)
        outreach = self.personalizer.generate_outreach(inf)

        # First dispatch -> Should succeed
        log1 = self.dispatcher.dispatch_email(inf, outreach)
        self.assertIn(log1.status, ["Sent", "Simulated"])

        # Second dispatch attempt -> Must be detected and skipped
        log2 = self.dispatcher.dispatch_email(inf, outreach)
        self.assertEqual(log2.status, "Skipped")
        self.assertIn("Duplicate", log2.delivery_notes)

    def test_06_complete_end_to_end_pipeline(self):
        """Test running the full 7-stage pipeline orchestrator and exporting data."""
        test_dir = tempfile.mkdtemp()
        db_path = os.path.join(test_dir, "test_outreach.db")
        pipeline = OutreachPipeline(db_path=db_path)

        res = pipeline.run_full_pipeline()
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["summary"]["discovered_count"], 50)
        self.assertGreaterEqual(res["summary"]["messages_generated"], 40)

        # Check export files
        csv_dataset = os.path.join(test_dir, "influencers.csv")
        csv_tracker = os.path.join(test_dir, "tracker.csv")
        pipeline.export_influencer_dataset(csv_dataset)
        pipeline.export_outreach_tracker(csv_tracker)

        self.assertTrue(os.path.exists(csv_dataset))
        self.assertTrue(os.path.exists(csv_tracker))
        self.assertGreater(os.path.getsize(csv_dataset), 500)


if __name__ == "__main__":
    unittest.main()
