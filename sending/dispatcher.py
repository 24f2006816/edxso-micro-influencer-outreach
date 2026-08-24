"""
Sending Layer and Outreach Dispatcher.
Manages automated email delivery (SMTP / Simulated mode), Instagram DM manual workflow,
anti-duplicate outreach safeguards, and audit tracking.
"""

import os
import uuid
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from models import InfluencerRecord, PersonalizedOutreach, OutreachLog
from database import Database


class OutreachDispatcher:
    """
    Executes and tracks outreach campaigns across Email (SMTP / Simulated) and Instagram DMs.
    Guarantees idempotency (anti-duplicate dispatch) and logs every operation.
    """

    def __init__(self, db: Database, mode: str = "SIMULATED"):
        self.db = db
        self.mode = mode.upper()  # 'SIMULATED' or 'SMTP'
        
        # SMTP Configuration (if using real live email)
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_email = os.getenv("SENDER_EMAIL", "partnerships@auraflow.io")

    def dispatch_email(
        self, influencer: InfluencerRecord, outreach: PersonalizedOutreach
    ) -> OutreachLog:
        """
        Dispatches or simulates dispatching a personalized email pitch.
        Enforces email validity and idempotency checks.
        """
        log_id = f"out_{uuid.uuid4().hex[:10]}"
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # 1. Validation: Check if email is valid
        if not influencer.email or influencer.email.lower() == "not found":
            log = OutreachLog(
                id=log_id,
                influencer_id=influencer.id,
                influencer_name=influencer.name,
                email="Not Found",
                platform=influencer.platform,
                message_generated_type="Email Pitch",
                email_pitch=outreach.email_pitch,
                instagram_dm=outreach.instagram_dm,
                sent_date=now_str,
                status="Skipped",
                channel="Email Dispatcher",
                delivery_notes="Skipped: Influencer profile does not contain a verified public contact email."
            )
            self.db.log_outreach(log)
            influencer.status = "Skipped"
            self.db.save_influencer(influencer)
            return log

        # 2. Idempotency Check: Prevent duplicate outreach
        if self.db.is_already_contacted(influencer.id, influencer.email):
            log = OutreachLog(
                id=log_id,
                influencer_id=influencer.id,
                influencer_name=influencer.name,
                email=influencer.email,
                platform=influencer.platform,
                message_generated_type="Email Pitch",
                email_pitch=outreach.email_pitch,
                instagram_dm=outreach.instagram_dm,
                sent_date=now_str,
                status="Skipped",
                channel="Email Dispatcher",
                delivery_notes=f"Skipped (Duplicate): Influencer or email '{influencer.email}' was already contacted in this campaign."
            )
            self.db.log_outreach(log)
            return log

        # 3. Execution: Live SMTP or High-Fidelity Simulation
        if self.mode == "SMTP" and self.smtp_user and self.smtp_password:
            status, note = self._send_live_smtp(influencer.email, outreach.email_pitch, influencer.name)
            channel_used = "SMTP Live"
        else:
            status, note = self._send_simulated_email(influencer.email, outreach.email_pitch)
            channel_used = "Simulated Dispatcher"

        log = OutreachLog(
            id=log_id,
            influencer_id=influencer.id,
            influencer_name=influencer.name,
            email=influencer.email,
            platform=influencer.platform,
            message_generated_type="Email Pitch + IG DM",
            email_pitch=outreach.email_pitch,
            instagram_dm=outreach.instagram_dm,
            sent_date=now_str,
            status=status,
            channel=channel_used,
            delivery_notes=note
        )

        self.db.log_outreach(log)
        influencer.status = "Sent" if status in ["Sent", "Simulated"] else "Failed"
        self.db.save_influencer(influencer)
        return log

    def dispatch_instagram_dm_workflow(
        self, influencer: InfluencerRecord, outreach: PersonalizedOutreach
    ) -> OutreachLog:
        """
        Compliant Instagram DM workflow (Manual/Simulated Dispatch).
        Respects Meta API platform policies while generating structured copy-ready payloads.
        """
        log_id = f"dm_{uuid.uuid4().hex[:10]}"
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        log = OutreachLog(
            id=log_id,
            influencer_id=influencer.id,
            influencer_name=influencer.name,
            email=influencer.email,
            platform="Instagram",
            message_generated_type="Instagram DM",
            email_pitch=outreach.email_pitch,
            instagram_dm=outreach.instagram_dm,
            sent_date=now_str,
            status="Simulated",
            channel="Instagram DM (Simulated Workflow)",
            delivery_notes=f"Generated 1-click clipboard payload for handle {influencer.profile_url} ({outreach.dm_word_count} words)."
        )

        self.db.log_outreach(log)
        return log

    def batch_dispatch(
        self, items: List[Tuple[InfluencerRecord, PersonalizedOutreach]]
    ) -> List[OutreachLog]:
        logs = []
        for inf, outreach in items:
            log = self.dispatch_email(inf, outreach)
            logs.append(log)
        return logs

    def _send_simulated_email(self, recipient: str, body: str) -> Tuple[str, str]:
        time.sleep(0.01)
        note = f"Simulated delivery successful to {recipient}. 250 OK: Message queued for recipient relay."
        return "Simulated", note

    def _send_live_smtp(self, recipient: str, body: str, name: str) -> Tuple[str, str]:
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = recipient
            msg["Subject"] = f"Collaboration Inquiry - {name} x AuraFlow"
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            return "Sent", f"Live SMTP message delivered to {recipient}."
        except Exception as e:
            return "Failed", f"SMTP Delivery error: {str(e)}"
