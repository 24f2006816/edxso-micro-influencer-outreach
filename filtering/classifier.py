"""
Filtering and Classification Engine.
Evaluates discovered influencers against multi-dimensional qualification criteria
and records granular pass/fail rationales.
"""

from typing import List, Dict, Any, Tuple
from models import InfluencerRecord, FilterCriteria, FilterResult


class InfluencerClassifier:
    """
    Evaluates influencers against micro-influencer boundaries, niche alignments,
    engagement metrics, and brand safety benchmarks.
    """

    NICHE_ALIASES = {
        "tech": "Technology",
        "technology": "Technology",
        "beauty": "Beauty",
        "skincare": "Beauty",
        "fashion": "Fashion",
        "style": "Fashion",
        "fitness": "Fitness",
        "wellness": "Fitness",
        "fintech": "Fintech",
        "finance": "Fintech",
        "crypto": "Crypto",
        "web3": "Crypto",
        "parenting": "Parenting",
        "family": "Parenting",
        "gaming": "Gaming",
        "esports": "Gaming",
        "lifestyle": "Lifestyle"
    }

    def __init__(self, default_criteria: FilterCriteria = None):
        self.default_criteria = default_criteria or FilterCriteria()

    def normalize_niche(self, niche: str) -> str:
        return self.NICHE_ALIASES.get(niche.lower().strip(), niche.strip())

    def evaluate(self, influencer: InfluencerRecord, criteria: FilterCriteria = None) -> FilterResult:
        crit = criteria or self.default_criteria
        reasons: List[str] = []
        breakdown: Dict[str, bool] = {}
        all_passed = True

        # 1. Follower Count Check (Micro-influencer definition: 5k - 100k)
        if influencer.followers < crit.min_followers:
            all_passed = False
            breakdown["follower_count"] = False
            reasons.append(
                f"Disqualified: Follower count ({influencer.followers:,}) is below the micro-influencer minimum ({crit.min_followers:,})."
            )
        elif influencer.followers > crit.max_followers:
            all_passed = False
            breakdown["follower_count"] = False
            reasons.append(
                f"Disqualified: Follower count ({influencer.followers:,}) exceeds the micro-influencer maximum ({crit.max_followers:,})."
            )
        else:
            breakdown["follower_count"] = True

        # 2. Engagement Rate Check
        if influencer.engagement_rate < crit.min_engagement_rate:
            all_passed = False
            breakdown["engagement_rate"] = False
            reasons.append(
                f"Disqualified: Engagement rate ({influencer.engagement_rate:.1f}%) is below minimum requirement ({crit.min_engagement_rate:.1f}%)."
            )
        else:
            breakdown["engagement_rate"] = True

        # 3. Niche / Category Alignment Check
        norm_inf_niche = self.normalize_niche(influencer.niche).lower()
        allowed_niches_norm = [self.normalize_niche(n).lower() for n in crit.allowed_niches]
        
        if crit.allowed_niches and norm_inf_niche not in allowed_niches_norm:
            all_passed = False
            breakdown["niche_match"] = False
            reasons.append(
                f"Disqualified: Niche '{influencer.niche}' does not match target campaign niches ({', '.join(crit.allowed_niches)})."
            )
        else:
            breakdown["niche_match"] = True

        # 4. Platform Alignment Check
        allowed_platforms_lower = [p.lower() for p in crit.allowed_platforms]
        if crit.allowed_platforms and influencer.platform.lower() not in allowed_platforms_lower:
            all_passed = False
            breakdown["platform_match"] = False
            reasons.append(
                f"Disqualified: Platform '{influencer.platform}' is not in allowed platforms ({', '.join(crit.allowed_platforms)})."
            )
        else:
            breakdown["platform_match"] = True

        # 5. Brand Safety & Quality Benchmark
        if influencer.brand_fit_score < crit.min_brand_fit_score:
            all_passed = False
            breakdown["brand_fit"] = False
            reasons.append(
                f"Disqualified: Brand fit score ({influencer.brand_fit_score}/10) is below minimum threshold ({crit.min_brand_fit_score}/10)."
            )
        else:
            breakdown["brand_fit"] = True

        # 6. Optional Contact Email Requirement
        if crit.require_contact_email and (influencer.email == "Not Found" or not influencer.email):
            all_passed = False
            breakdown["email_available"] = False
            reasons.append("Disqualified: No verified contact email available.")
        else:
            breakdown["email_available"] = True

        # If passed all criteria, add positive qualification reason
        if all_passed:
            reasons.append(
                f"Qualified: Matches target niche '{influencer.niche}', verified {influencer.followers:,} followers (5k-100k tier), "
                f"strong {influencer.engagement_rate:.1f}% engagement rate on {influencer.platform}, brand score {influencer.brand_fit_score}/10."
            )

        # Update influencer record fields
        influencer.filter_passed = all_passed
        influencer.filter_reasons = reasons
        influencer.status = "Qualified" if all_passed else "Disqualified"

        return FilterResult(passed=all_passed, reasons=reasons, breakdown=breakdown)

    def classify_all(
        self, influencers: List[InfluencerRecord], criteria: FilterCriteria = None
    ) -> Tuple[List[InfluencerRecord], List[InfluencerRecord], Dict[str, Any]]:
        """
        Classifies a list of influencers, returning (qualified, disqualified, audit_report).
        """
        qualified: List[InfluencerRecord] = []
        disqualified: List[InfluencerRecord] = []
        
        for inf in influencers:
            res = self.evaluate(inf, criteria)
            if res.passed:
                qualified.append(inf)
            else:
                disqualified.append(inf)

        audit_report = {
            "total_evaluated": len(influencers),
            "passed_count": len(qualified),
            "failed_count": len(disqualified),
            "pass_rate_percent": round((len(qualified) / len(influencers) * 100), 2) if influencers else 0.0,
            "reasons_summary": self._aggregate_failure_reasons(disqualified)
        }

        return qualified, disqualified, audit_report

    def _aggregate_failure_reasons(self, disqualified: List[InfluencerRecord]) -> Dict[str, int]:
        summary: Dict[str, int] = {
            "follower_out_of_bounds": 0,
            "low_engagement": 0,
            "niche_mismatch": 0,
            "platform_mismatch": 0,
            "low_brand_fit": 0,
            "missing_email": 0
        }
        for inf in disqualified:
            for r in inf.filter_reasons:
                if "Follower count" in r:
                    summary["follower_out_of_bounds"] += 1
                if "Engagement rate" in r:
                    summary["low_engagement"] += 1
                if "Niche" in r:
                    summary["niche_mismatch"] += 1
                if "Platform" in r:
                    summary["platform_mismatch"] += 1
                if "Brand fit" in r:
                    summary["low_brand_fit"] += 1
                if "contact email" in r:
                    summary["missing_email"] += 1
        return summary
