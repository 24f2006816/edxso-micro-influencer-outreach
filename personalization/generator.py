"""
AI-Powered Message Personalization Engine.
Generates dynamically tailored outreach pitches:
1. Email Collaboration Pitch (Strictly 60–90 words)
2. Instagram DM (Strictly 15–30 words)
Supports live Gemini/OpenAI API REST calls and an intelligent built-in semantic generator.
"""

import os
import re
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Tuple, Optional

from models import InfluencerRecord, PersonalizedOutreach


class AIPersonalizationEngine:
    """
    Generates personalized outreach messages for qualified micro-influencers.
    """

    COLLABORATION_ANGLES = [
        "Sponsorship",
        "UGC content creation",
        "Brand ambassador program",
        "Paid product placement",
        "Affiliate campaign",
        "Barter collaboration"
    ]

    def __init__(self, model_name: str = "auto", company_name: str = "AuraFlow Collective"):
        self.company_name = company_name
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.model_name = model_name

    def generate_outreach(self, influencer: InfluencerRecord, angle: Optional[str] = None) -> PersonalizedOutreach:
        """
        Generates both Email Pitch (60-90 words) and Instagram DM (15-30 words) for an influencer.
        """
        chosen_angle = angle or self._select_collaboration_angle(influencer)
        
        # Try external LLM API if key is available, otherwise use high-fidelity semantic generator
        if self.gemini_key:
            try:
                email_text, dm_text, model_label = self._generate_with_gemini(influencer, chosen_angle)
            except Exception:
                email_text, dm_text, model_label = self._generate_semantic_fallback(influencer, chosen_angle)
        elif self.openai_key:
            try:
                email_text, dm_text, model_label = self._generate_with_openai(influencer, chosen_angle)
            except Exception:
                email_text, dm_text, model_label = self._generate_semantic_fallback(influencer, chosen_angle)
        else:
            email_text, dm_text, model_label = self._generate_semantic_fallback(influencer, chosen_angle)

        # Enforce and sanitize word count boundaries
        email_clean, email_wc = self._enforce_word_count(email_text, min_w=60, max_w=90, is_email=True, influencer=influencer, angle=chosen_angle)
        dm_clean, dm_wc = self._enforce_word_count(dm_text, min_w=15, max_w=30, is_email=False, influencer=influencer, angle=chosen_angle)

        outreach = PersonalizedOutreach(
            influencer_id=influencer.id,
            influencer_name=influencer.name,
            email_pitch=email_clean,
            email_word_count=email_wc,
            collaboration_angle=chosen_angle,
            instagram_dm=dm_clean,
            dm_word_count=dm_wc,
            model_used=model_label
        )

        influencer.status = "Personalized"
        return outreach

    def generate_batch(self, influencers: List[InfluencerRecord]) -> List[PersonalizedOutreach]:
        return [self.generate_outreach(inf) for inf in influencers]

    def _select_collaboration_angle(self, influencer: InfluencerRecord) -> str:
        """
        Dynamically matches the best collaboration angle based on niche, platform, and follower count.
        """
        if influencer.followers > 60000:
            return "Sponsorship"
        elif influencer.followers > 35000:
            if influencer.niche in ["Beauty", "Fashion", "Lifestyle"]:
                return "Brand ambassador program"
            return "Paid product placement"
        elif influencer.followers > 15000:
            if influencer.niche in ["Beauty", "Fitness", "Gaming"]:
                return "UGC content creation"
            return "Affiliate campaign"
        else:
            return "Barter collaboration" if influencer.niche in ["Beauty", "Fashion"] else "UGC content creation"

    def _generate_semantic_fallback(self, inf: InfluencerRecord, angle: str) -> Tuple[str, str, str]:
        """
        High-fidelity context-aware semantic message generator.
        Generates hyper-personalized messages tailored to niche, recent content titles, and audience.
        """
        first_name = inf.name.split()[0]
        recent_topic = inf.recent_posts[0] if inf.recent_posts else f"recent {inf.niche.lower()} breakdowns"
        primary_theme = inf.content_themes[0] if inf.content_themes else inf.niche
        sec_theme = inf.content_themes[1] if len(inf.content_themes) > 1 else "daily workflows"

        # Construct Email Pitch (Target 70-80 words, bound 60-90)
        email_templates = [
            f"Hi {first_name},\n\n"
            f"I came across your content on {inf.platform} and loved your recent piece on '{recent_topic}'. "
            f"Your approach to {primary_theme.lower()} resonates deeply with our mission at {self.company_name}.\n\n"
            f"We are launching a new campaign and would love to partner with you on a paid {angle.lower()}. "
            f"We provide competitive compensation, creative freedom, and tailored product access for your audience.\n\n"
            f"Would you be open to reviewing the brief this week?\n\n"
            f"Best,\nOutreach Team",

            f"Hello {first_name},\n\n"
            f"Your recent breakdown of '{recent_topic}' really stood out to us. "
            f"We admire how effectively you educate your community around {primary_theme.lower()} and {sec_theme.lower()}.\n\n"
            f"At {self.company_name}, we are selecting key creators in the {inf.niche.lower()} space for an exclusive {angle.lower()}. "
            f"We offer full editorial autonomy, competitive deliverables pay, and exclusive perks for your {inf.platform} followers.\n\n"
            f"Could we share the campaign details and budget over a quick email?\n\n"
            f"Warm regards,\n{self.company_name} Team",

            f"Hi {first_name},\n\n"
            f"Loved your recent post covering '{recent_topic}'. "
            f"The high engagement and genuine feedback from your {inf.niche.lower()} audience show the authentic community you have cultivated on {inf.platform}.\n\n"
            f"We would love to sponsor you for an upcoming {angle.lower()} with {self.company_name}. "
            f"We offer dedicated creator compensation, free custom kits, and full creative control.\n\n"
            f"Let me know if you would like to explore this collaboration!\n\n"
            f"Best regards,\nPartnerships Team"
        ]

        # Pick template deterministically based on hash of influencer id
        idx = hash(inf.id) % len(email_templates)
        email_pitch = email_templates[idx]

        # Construct Instagram DM (Target 20-25 words, bound 15-30)
        dm_templates = [
            f"Hi {first_name}! Loved your recent post on '{recent_topic}'. Your {inf.niche.lower()} community looks like a perfect match for our upcoming {angle.lower()}. Open to collabs?",
            f"Hey {first_name}, really enjoyed your insights on '{recent_topic}'. We would love to collaborate on a paid {angle.lower()} for your {inf.niche.lower()} audience. Interested?",
            f"Hi {first_name}, big fan of your {primary_theme.lower()} content! Loved '{recent_topic}'. Would love to send a paid {angle.lower()} proposal your way if open!"
        ]
        dm_pitch = dm_templates[idx]

        return email_pitch, dm_pitch, "Semantic-Contextual-Generator-v2"

    def _generate_with_gemini(self, inf: InfluencerRecord, angle: str) -> Tuple[str, str, str]:
        prompt = f"""
You are an expert influencer marketing manager. Generate two personalized outreach messages for this micro-influencer:
Influencer: {inf.name} ({inf.platform}, {inf.followers:,} followers, {inf.engagement_rate}% engagement, Niche: {inf.niche})
Recent Content: {'; '.join(inf.recent_posts[:2])}
Content Themes: {', '.join(inf.content_themes[:3])}
Target Angle: {angle}
Company: {self.company_name}

OUTPUT EXACT JSON:
{{
  "email_pitch": "...", // STRICTLY 60 to 90 words. Mention recent post, niche, angle, value prop, call to action.
  "instagram_dm": "..." // STRICTLY 15 to 30 words. Casual, direct, references content.
}}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            # Extract JSON block
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                payload = json.loads(match.group(0))
                return payload["email_pitch"], payload["instagram_dm"], "Gemini-1.5-Flash"
        raise ValueError("Failed parsing Gemini response")

    def _generate_with_openai(self, inf: InfluencerRecord, angle: str) -> Tuple[str, str, str]:
        prompt = f"""
You are an expert influencer marketing manager. Generate two personalized outreach messages:
Influencer: {inf.name} ({inf.platform}, {inf.followers:,} followers, {inf.engagement_rate}% engagement, Niche: {inf.niche})
Recent Content: {'; '.join(inf.recent_posts[:2])}
Content Themes: {', '.join(inf.content_themes[:3])}
Target Angle: {angle}
Company: {self.company_name}

OUTPUT JSON ONLY:
{{
  "email_pitch": "...", // STRICTLY 60 to 90 words
  "instagram_dm": "..." // STRICTLY 15 to 30 words
}}
"""
        url = "https://api.openai.com/v1/chat/completions"
        data = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_key}"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            content = res_json["choices"][0]["message"]["content"]
            payload = json.loads(content)
            return payload["email_pitch"], payload["instagram_dm"], "GPT-4o-Mini"

    def _enforce_word_count(
        self, text: str, min_w: int, max_w: int, is_email: bool, influencer: InfluencerRecord, angle: str
    ) -> Tuple[str, int]:
        """
        Sanitizes and enforces strict word count bounds.
        """
        words = text.split()
        count = len(words)

        if min_w <= count <= max_w:
            return text, count

        # If too long, trim cleanly to max_w - 2 and add polite signoff
        if count > max_w:
            trimmed = " ".join(words[: max_w - 4])
            if is_email:
                text = f"{trimmed}...\n\nBest,\nPartnerships Team"
            else:
                text = f"{trimmed} Open to collabs?"
            words = text.split()
            count = len(words)

        # If too short, augment with contextual value proposition
        if count < min_w:
            if is_email:
                first_name = influencer.name.split()[0]
                recent_post = influencer.recent_posts[0] if influencer.recent_posts else "recent posts"
                text = (
                    f"Hi {first_name},\n\n"
                    f"I came across your profile on {influencer.platform} and really enjoyed your content on '{recent_post}'. "
                    f"Your genuine perspective on {influencer.niche.lower()} connects well with our audience.\n\n"
                    f"At {self.company_name}, we are launching a new initiative and would love to partner with you for a paid {angle.lower()}. "
                    f"We offer competitive compensation, full creative autonomy, and dedicated product support for your community.\n\n"
                    f"Would you be open to exploring campaign details and discussing deliverables this week?\n\n"
                    f"Best regards,\nPartnerships Team"
                )
            else:
                first_name = influencer.name.split()[0]
                recent_post = influencer.recent_posts[0] if influencer.recent_posts else "content"
                text = f"Hi {first_name}, loved your recent post on '{recent_post}'. Your {influencer.niche.lower()} audience looks like a great fit for our upcoming {angle.lower()} campaign. Interested in collaborating?"
            words = text.split()
            count = len(words)

        return text, count
