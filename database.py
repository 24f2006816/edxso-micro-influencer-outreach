"""
Database layer for managing influencers, filtration audits, generated messages, and outreach tracking.
Uses SQLite with robust anti-duplicate safeguards and clean connection management.
"""

import sqlite3
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

from models import InfluencerRecord, PersonalizedOutreach, OutreachLog


class Database:
    def __init__(self, db_path: str = "data/outreach_system.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Influencer profiles & status
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS influencers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    profile_url TEXT NOT NULL,
                    followers INTEGER NOT NULL,
                    engagement_rate REAL NOT NULL,
                    niche TEXT NOT NULL,
                    content_themes TEXT,
                    email TEXT NOT NULL,
                    secondary_platform TEXT,
                    secondary_url TEXT,
                    website TEXT,
                    audience_age TEXT,
                    audience_gender TEXT,
                    audience_geography TEXT,
                    content_tone TEXT,
                    recent_posts TEXT,
                    brand_fit_score REAL,
                    status TEXT NOT NULL,
                    filter_passed INTEGER,
                    filter_reasons TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Personalized AI Outreach Messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outreach_messages (
                    influencer_id TEXT PRIMARY KEY,
                    influencer_name TEXT NOT NULL,
                    email_pitch TEXT NOT NULL,
                    email_word_count INTEGER NOT NULL,
                    collaboration_angle TEXT NOT NULL,
                    instagram_dm TEXT NOT NULL,
                    dm_word_count INTEGER NOT NULL,
                    model_used TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    FOREIGN KEY (influencer_id) REFERENCES influencers(id)
                )
            """)

            # Outreach Dispatch Audit Logs (Tracking Layer)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outreach_logs (
                    id TEXT PRIMARY KEY,
                    influencer_id TEXT NOT NULL,
                    influencer_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    message_generated_type TEXT NOT NULL,
                    email_pitch TEXT,
                    instagram_dm TEXT,
                    sent_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    delivery_notes TEXT,
                    FOREIGN KEY (influencer_id) REFERENCES influencers(id)
                )
            """)

            conn.commit()

    def save_influencer(self, inf: InfluencerRecord):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO influencers (
                    id, name, platform, profile_url, followers, engagement_rate, niche,
                    content_themes, email, secondary_platform, secondary_url, website,
                    audience_age, audience_gender, audience_geography, content_tone,
                    recent_posts, brand_fit_score, status, filter_passed, filter_reasons, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    platform=excluded.platform,
                    profile_url=excluded.profile_url,
                    followers=excluded.followers,
                    engagement_rate=excluded.engagement_rate,
                    niche=excluded.niche,
                    content_themes=excluded.content_themes,
                    email=excluded.email,
                    secondary_platform=excluded.secondary_platform,
                    secondary_url=excluded.secondary_url,
                    website=excluded.website,
                    audience_age=excluded.audience_age,
                    audience_gender=excluded.audience_gender,
                    audience_geography=excluded.audience_geography,
                    content_tone=excluded.content_tone,
                    recent_posts=excluded.recent_posts,
                    brand_fit_score=excluded.brand_fit_score,
                    status=excluded.status,
                    filter_passed=excluded.filter_passed,
                    filter_reasons=excluded.filter_reasons,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                inf.id, inf.name, inf.platform, inf.profile_url, inf.followers,
                inf.engagement_rate, inf.niche, json.dumps(inf.content_themes), inf.email,
                inf.secondary_platform, inf.secondary_url, inf.website,
                inf.audience_age, inf.audience_gender, inf.audience_geography, inf.content_tone,
                json.dumps(inf.recent_posts), inf.brand_fit_score, inf.status,
                1 if inf.filter_passed else (0 if inf.filter_passed is not None else None),
                json.dumps(inf.filter_reasons)
            ))
            conn.commit()
        finally:
            conn.close()

    def save_influencers(self, influencers: List[InfluencerRecord]):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            for inf in influencers:
                cursor.execute("""
                    INSERT INTO influencers (
                        id, name, platform, profile_url, followers, engagement_rate, niche,
                        content_themes, email, secondary_platform, secondary_url, website,
                        audience_age, audience_gender, audience_geography, content_tone,
                        recent_posts, brand_fit_score, status, filter_passed, filter_reasons, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name,
                        platform=excluded.platform,
                        profile_url=excluded.profile_url,
                        followers=excluded.followers,
                        engagement_rate=excluded.engagement_rate,
                        niche=excluded.niche,
                        content_themes=excluded.content_themes,
                        email=excluded.email,
                        secondary_platform=excluded.secondary_platform,
                        secondary_url=excluded.secondary_url,
                        website=excluded.website,
                        audience_age=excluded.audience_age,
                        audience_gender=excluded.audience_gender,
                        audience_geography=excluded.audience_geography,
                        content_tone=excluded.content_tone,
                        recent_posts=excluded.recent_posts,
                        brand_fit_score=excluded.brand_fit_score,
                        status=excluded.status,
                        filter_passed=excluded.filter_passed,
                        filter_reasons=excluded.filter_reasons,
                        updated_at=CURRENT_TIMESTAMP
                """, (
                    inf.id, inf.name, inf.platform, inf.profile_url, inf.followers,
                    inf.engagement_rate, inf.niche, json.dumps(inf.content_themes), inf.email,
                    inf.secondary_platform, inf.secondary_url, inf.website,
                    inf.audience_age, inf.audience_gender, inf.audience_geography, inf.content_tone,
                    json.dumps(inf.recent_posts), inf.brand_fit_score, inf.status,
                    1 if inf.filter_passed else (0 if inf.filter_passed is not None else None),
                    json.dumps(inf.filter_reasons)
                ))
            conn.commit()
        finally:
            conn.close()

    def get_influencer(self, influencer_id: str) -> Optional[InfluencerRecord]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM influencers WHERE id = ?", (influencer_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_influencer(row)
        finally:
            conn.close()

    def get_all_influencers(self, status: Optional[str] = None, niche: Optional[str] = None) -> List[InfluencerRecord]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM influencers WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            if niche:
                query += " AND niche = ?"
                params.append(niche)
            query += " ORDER BY followers DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_influencer(r) for r in rows]
        finally:
            conn.close()

    def _row_to_influencer(self, row: sqlite3.Row) -> InfluencerRecord:
        d = dict(row)
        d["filter_passed"] = bool(d["filter_passed"]) if d["filter_passed"] is not None else None
        return InfluencerRecord.from_dict(d)

    def save_outreach_message(self, msg: PersonalizedOutreach):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO outreach_messages (
                    influencer_id, influencer_name, email_pitch, email_word_count,
                    collaboration_angle, instagram_dm, dm_word_count, model_used, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(influencer_id) DO UPDATE SET
                    email_pitch=excluded.email_pitch,
                    email_word_count=excluded.email_word_count,
                    collaboration_angle=excluded.collaboration_angle,
                    instagram_dm=excluded.instagram_dm,
                    dm_word_count=excluded.dm_word_count,
                    model_used=excluded.model_used,
                    generated_at=excluded.generated_at
            """, (
                msg.influencer_id, msg.influencer_name, msg.email_pitch,
                msg.email_word_count, msg.collaboration_angle, msg.instagram_dm,
                msg.dm_word_count, msg.model_used, msg.generated_at
            ))
            conn.commit()
        finally:
            conn.close()

    def get_outreach_message(self, influencer_id: str) -> Optional[PersonalizedOutreach]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM outreach_messages WHERE influencer_id = ?", (influencer_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return PersonalizedOutreach(**dict(row))
        finally:
            conn.close()

    def log_outreach(self, log: OutreachLog):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO outreach_logs (
                    id, influencer_id, influencer_name, email, platform,
                    message_generated_type, email_pitch, instagram_dm,
                    sent_date, status, channel, delivery_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.id, log.influencer_id, log.influencer_name, log.email, log.platform,
                log.message_generated_type, log.email_pitch, log.instagram_dm,
                log.sent_date, log.status, log.channel, log.delivery_notes
            ))
            conn.commit()
        finally:
            conn.close()

    def is_already_contacted(self, influencer_id: str, email: str = "") -> bool:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if email and email.lower() != "not found":
                cursor.execute("""
                    SELECT COUNT(*) as count FROM outreach_logs 
                    WHERE (influencer_id = ? OR email = ?) AND status IN ('Sent', 'Simulated')
                """, (influencer_id, email))
            else:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM outreach_logs 
                    WHERE influencer_id = ? AND status IN ('Sent', 'Simulated')
                """, (influencer_id,))
            row = cursor.fetchone()
            return row["count"] > 0
        finally:
            conn.close()

    def get_outreach_logs(self) -> List[OutreachLog]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM outreach_logs ORDER BY sent_date DESC")
            rows = cursor.fetchall()
            return [OutreachLog(**dict(r)) for r in rows]
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM influencers")
            total = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as qualified FROM influencers WHERE filter_passed = 1")
            qualified = cursor.fetchone()["qualified"]

            cursor.execute("SELECT COUNT(*) as disqualified FROM influencers WHERE filter_passed = 0")
            disqualified = cursor.fetchone()["disqualified"]

            cursor.execute("SELECT COUNT(*) as with_email FROM influencers WHERE email != 'Not Found' AND email != ''")
            with_email = cursor.fetchone()["with_email"]

            cursor.execute("SELECT COUNT(*) as personalized FROM outreach_messages")
            personalized = cursor.fetchone()["personalized"]

            cursor.execute("SELECT COUNT(*) as sent FROM outreach_logs WHERE status IN ('Sent', 'Simulated')")
            sent = cursor.fetchone()["sent"]

            cursor.execute("SELECT niche, COUNT(*) as count FROM influencers GROUP BY niche")
            niche_counts = {r["niche"]: r["count"] for r in cursor.fetchall()}

            cursor.execute("SELECT platform, COUNT(*) as count FROM influencers GROUP BY platform")
            platform_counts = {r["platform"]: r["count"] for r in cursor.fetchall()}

            return {
                "total_discovered": total,
                "qualified": qualified,
                "disqualified": disqualified,
                "with_email": with_email,
                "messages_generated": personalized,
                "outreach_sent": sent,
                "niche_breakdown": niche_counts,
                "platform_breakdown": platform_counts,
            }
        finally:
            conn.close()
