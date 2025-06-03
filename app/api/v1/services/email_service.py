import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from datetime import datetime, timedelta
import random
import string

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.sender_email = settings.EMAIL_FROM
        self.use_tls = settings.SMTP_TLS

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email using SMTP
        """
        if not text_content:
            # Create a simple text version from HTML if not provided
            text_content = ""
            # Simple HTML to text conversion
            # This is a very basic conversion and might need improvement
            import re
            text_content = re.sub(r'<[^>]*>', ' ', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = to_email

        # Add HTML/plain-text parts to MIMEMultipart message
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.sendmail(
                    self.sender_email, to_email, message.as_string()
                )
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_otp_email(self, email: str, otp: str) -> bool:
        """
        Send OTP to user's email
        """
        subject = "Your Password Reset OTP"
        html_content = f"""
        <div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;\">
            <h2>Password Reset Request</h2>
            <p>You have requested to reset your password. Please use the following OTP to proceed:</p>
            <div style=\"background-color: #f5f5f5; padding: 15px; margin: 20px 0; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 2px;\">
                {otp}
            </div>
            <p>This OTP is valid for 15 minutes.</p>
            <p>If you didn't request this, please ignore this email or contact support if you have any concerns.</p>
            <hr>
            <p style=\"font-size: 12px; color: #666;\">
                This is an automated message, please do not reply directly to this email.
            </p>
        </div>
        """
        
        return await self.send_email(email, subject, html_content)

    async def send_password_reset_confirmation(self, email: str) -> bool:
        """
        Send password reset confirmation email
        """
        subject = "Password Reset Successful"
        html_content = """
        <div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;\">
            <h2>Password Reset Successful</h2>
            <p>Your password has been successfully reset.</p>
            <p>If you didn't make this change or believe an unauthorized person has accessed your account, please contact our support team immediately.</p>
            <hr>
            <p style=\"font-size: 12px; color: #666;\">
                This is an automated message, please do not reply directly to this email.
            </p>
        </div>
        """
        return await self.send_email(email, subject, html_content)

# Create a singleton instance
email_service = EmailService()

# Convenience functions for direct usage
async def send_otp_email(email: str, otp: str) -> bool:
    return await email_service.send_otp_email(email, otp)

async def send_password_reset_confirmation(email: str) -> bool:
    return await email_service.send_password_reset_confirmation(email)
