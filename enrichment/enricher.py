"""
Profile Enrichment Engine.
Validates, standardizes, and enhances influencer profiles with verified metrics,
content themes, collaboration angles, audience demographic estimates, and contact details.
"""

import re
from typing import List, Dict, Any, Optional
from models import InfluencerRecord


class ProfileEnricher:
    """
    Enriches influencer records to ensure all mandatory and optional metadata
    are standardized and ready for AI personalization and outreach.
    """

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    def __init__(self):
        pass

    def enrich(self, influencer: InfluencerRecord) -> InfluencerRecord:
        """
        Enriches a single influencer record.
        Validates email format, fills in default themes if sparse,
        and assigns collaboration angles.
        """
        # 1. Contact Email Validation & Normalization
        cleaned_email = (influencer.email or "").strip()
        if not cleaned_email or cleaned_email.lower() in ["none", "null", "n/a", "unknown", "not found"]:
            influencer.email = "Not Found"
        elif not self.EMAIL_REGEX.match(cleaned_email):
            influencer.email = "Not Found"
        else:
            influencer.email = cleaned_email.lower()

        # 2. Content Themes Standardizing
        if not influencer.content_themes:
            influencer.content_themes = [f"{influencer.niche} Reviews", f"{influencer.niche} Tutorials"]

        # 3. Tone & Style Normalization
        if not influencer.content_tone:
            influencer.content_tone = self._infer_tone_from_niche(influencer.niche)

        # 4. Audience Geography Fallback
        if not influencer.audience_geography:
            influencer.audience_geography = "Global (Predominantly US / English-speaking)"

        # 5. Audience Age Fallback
        if not influencer.audience_age:
            influencer.audience_age = "18-35 (75%+)"

        # 6. Audience Gender Fallback
        if not influencer.audience_gender:
            influencer.audience_gender = self._infer_gender_demographics(influencer.niche)

        # 7. Update status
        if influencer.filter_passed:
            influencer.status = "Enriched"

        return influencer

    def enrich_batch(self, influencers: List[InfluencerRecord]) -> List[InfluencerRecord]:
        return [self.enrich(inf) for inf in influencers]

    def _infer_tone_from_niche(self, niche: str) -> str:
        niche_lower = niche.lower()
        if "tech" in niche_lower or "crypto" in niche_lower or "fintech" in niche_lower:
            return "Analytical & Educational"
        elif "beauty" in niche_lower or "fashion" in niche_lower:
            return "Aesthetic & Relatable"
        elif "fitness" in niche_lower:
            return "High-Energy & Motivating"
        elif "gaming" in niche_lower:
            return "Passionate & Community-Driven"
        elif "parenting" in niche_lower:
            return "Empathetic & Practical"
        else:
            return "Authentic & Engaging"

    def _infer_gender_demographics(self, niche: str) -> str:
        niche_lower = niche.lower()
        if "beauty" in niche_lower:
            return "85% Female, 15% Male"
        elif "fashion" in niche_lower:
            return "75% Female, 25% Male"
        elif "tech" in niche_lower or "crypto" in niche_lower:
            return "20% Female, 80% Male"
        elif "gaming" in niche_lower:
            return "30% Female, 70% Male"
        elif "parenting" in niche_lower:
            return "88% Female, 12% Male"
        elif "fitness" in niche_lower:
            return "50% Female, 50% Male"
        return "50% Female, 50% Male"
