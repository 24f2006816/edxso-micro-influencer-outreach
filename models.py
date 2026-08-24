"""
Data models and schema definitions for the Automated Micro-Influencer Outreach System.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json


@dataclass
class InfluencerRecord:
    id: str
    name: str
    platform: str  # Instagram, YouTube, TikTok, etc.
    profile_url: str
    followers: int
    engagement_rate: float  # e.g., 4.2 for 4.2%
    niche: str  # Fitness, Beauty, Fashion, Tech, Fintech, Crypto, Parenting, Gaming, Lifestyle
    content_themes: List[str] = field(default_factory=list)
    email: str = "Not Found"  # Mandatory field: valid email or explicit 'Not Found'
    
    # Optional Profile Enrichment Fields
    secondary_platform: Optional[str] = None
    secondary_url: Optional[str] = None
    website: Optional[str] = None
    audience_age: Optional[str] = None  # e.g., '18-24 (45%), 25-34 (40%)'
    audience_gender: Optional[str] = None  # e.g., '68% Female, 32% Male'
    audience_geography: Optional[str] = None  # e.g., 'United States (55%), UK (20%)'
    content_tone: Optional[str] = "Authentic & Informative"  # e.g. Educational, Casual, Aesthetic
    recent_posts: List[str] = field(default_factory=list)  # Titles/summaries of recent content
    brand_fit_score: float = 8.5  # Scale 1-10
    
    # Processing Statuses
    status: str = "Discovered"  # Discovered, Qualified, Disqualified, Enriched, Personalized, Sent, Skipped
    filter_passed: Optional[bool] = None
    filter_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InfluencerRecord":
        d = dict(data)
        if isinstance(d.get("content_themes"), str):
            try:
                d["content_themes"] = json.loads(d["content_themes"])
            except Exception:
                d["content_themes"] = [t.strip() for t in d["content_themes"].split(",") if t.strip()]
        if isinstance(d.get("recent_posts"), str):
            try:
                d["recent_posts"] = json.loads(d["recent_posts"])
            except Exception:
                d["recent_posts"] = [p.strip() for p in d["recent_posts"].split(";") if p.strip()]
        if isinstance(d.get("filter_reasons"), str):
            try:
                d["filter_reasons"] = json.loads(d["filter_reasons"])
            except Exception:
                d["filter_reasons"] = [d["filter_reasons"]] if d["filter_reasons"] else []
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class FilterCriteria:
    min_followers: int = 5000
    max_followers: int = 100000
    min_engagement_rate: float = 2.0
    allowed_niches: List[str] = field(default_factory=lambda: [
        "Fitness", "Beauty", "Fashion", "Tech", "Technology", "Fintech", "Crypto", "Parenting", "Gaming", "Lifestyle"
    ])
    allowed_platforms: List[str] = field(default_factory=lambda: ["Instagram", "YouTube", "TikTok", "Twitch"])
    min_brand_fit_score: float = 6.0
    require_contact_email: bool = False


@dataclass
class FilterResult:
    passed: bool
    reasons: List[str]
    breakdown: Dict[str, bool] = field(default_factory=dict)


@dataclass
class PersonalizedOutreach:
    influencer_id: str
    influencer_name: str
    email_pitch: str
    email_word_count: int
    collaboration_angle: str  # Sponsorship, Affiliate, UGC, Ambassador, Product Placement, Barter
    instagram_dm: str
    dm_word_count: int
    model_used: str
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OutreachLog:
    id: str
    influencer_id: str
    influencer_name: str
    email: str
    platform: str
    message_generated_type: str  # Email Pitch / Instagram DM / Both
    email_pitch: str
    instagram_dm: str
    sent_date: str
    status: str  # Sent, Simulated, Failed, Skipped
    channel: str  # SMTP, Gmail API, Instagram DM (Manual Dispatch), Simulated
    delivery_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
