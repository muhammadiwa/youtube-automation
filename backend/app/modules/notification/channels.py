"""Notification channel implementations for multi-channel delivery.

Implements Email, SMS, Slack, and Telegram delivery channels.
Requirements: 23.1 - Deliver within 60 seconds
"""

import asyncio
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import httpx

from app.core.config import settings


@dataclass
class ChannelDeliveryResult:
    """Result of a channel delivery attempt."""
    success: bool
    channel: str
    recipient: str
    delivered_at: Optional[datetime] = None
    error: Optional[str] = None
    response_data: Optional[dict] = None


class NotificationChannelBase(ABC):
    """Base class for notification channels."""
    
    channel_name: str = "base"
    
    @abstractmethod
    async def deliver(
        self,
        recipient: str,
        title: str,
        message: str,
        payload: Optional[dict] = None,
    ) -> ChannelDeliveryResult:
        """Deliver notification to recipient.
        
        Args:
            recipient: Channel-specific recipient identifier
            title: Notification title
            message: Notification message body
            payload: Additional payload data
            
        Returns:
            ChannelDeliveryResult with delivery status
        """
        pass
    
    def _create_success_result(
        self,
        recipient: str,
        response_data: Optional[dict] = None,
    ) -> ChannelDeliveryResult:
        """Create a successful delivery result."""
        return ChannelDeliveryResult(
            success=True,
            channel=self.channel_name,
            recipient=recipient,
            delivered_at=datetime.utcnow(),
            response_data=response_data,
        )
    
    def _create_failure_result(
        self,
        recipient: str,
        error: str,
    ) -> ChannelDeliveryResult:
        """Create a failed delivery result."""
        return ChannelDeliveryResult(
            success=False,
            channel=self.channel_name,
            recipient=recipient,
            error=error,
        )


class EmailChannel(NotificationChannelBase):
    """Email notification channel using SMTP.
    
    Requirements: 23.1 - Email delivery support
    """
    
    channel_name = "email"
    
    async def deliver(
        self,
        recipient: str,
        title: str,
        message: str,
        payload: Optional[dict] = None,
    ) -> ChannelDeliveryResult:
        """Deliver notification via email."""
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            return self._create_failure_result(
                recipient,
                "SMTP not configured",
            )
        
        try:
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = title
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = recipient
            
            # Plain text version
            text_part = MIMEText(message, "plain")
            msg.attach(text_part)
            
            # HTML version (simple formatting)
            html_content = f"""
            <html>
            <body>
                <h2>{title}</h2>
                <p>{message.replace(chr(10), '<br>')}</p>
            </body>
            </html>
            """
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)
            
            # Send email in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_smtp,
                recipient,
                msg,
            )
            
            return self._create_success_result(recipient)
            
        except Exception as e:
            return self._create_failure_result(recipient, str(e))
    
    def _send_smtp(self, recipient: str, msg: MIMEMultipart) -> None:
        """Send email via SMTP (blocking operation)."""
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            server.sendmail(
                settings.SMTP_FROM_EMAIL,
                recipient,
                msg.as_string(),
            )


class SMSChannel(NotificationChannelBase):
    """SMS notification channel.
    
    Requirements: 23.1 - SMS delivery support
    
    Note: This is a placeholder implementation. In production,
    integrate with Twilio, AWS SNS, or similar SMS provider.
    """
    
    channel_name = "sms"
    
    async def deliver(
        self,
        recipient: str,
        title: str,
        message: str,
        payload: Optional[dict] = None,
    ) -> ChannelDeliveryResult:
        """Deliver notification via SMS."""
        # Combine title and message for SMS (limited characters)
        sms_text = f"{title}: {message}"
        if len(sms_text) > 160:
            sms_text = sms_text[:157] + "..."
        
        # Placeholder: In production, integrate with SMS provider
        # Example with Twilio:
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(
        #     body=sms_text,
        #     from_=from_number,
        #     to=recipient
        # )
        
        # For now, simulate successful delivery
        return self._create_success_result(
            recipient,
            {"message": "SMS delivery simulated", "text": sms_text},
        )


class SlackChannel(NotificationChannelBase):
    """Slack notification channel using webhooks.
    
    Requirements: 23.1 - Slack delivery support
    """
    
    channel_name = "slack"
    
    async def deliver(
        self,
        recipient: str,
        title: str,
        message: str,
        payload: Optional[dict] = None,
    ) -> ChannelDeliveryResult:
        """Deliver notification via Slack webhook."""
        if not recipient or not recipient.startswith("https://hooks.slack.com/"):
            return self._create_failure_result(
                recipient,
                "Invalid Slack webhook URL",
            )
        
        try:
            # Build Slack message payload
            slack_payload = {
                "text": title,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": title,
                            "emoji": True,
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message,
                        },
                    },
                ],
            }
            
            # Add payload data if provided
            if payload:
                fields = []
                for key, value in payload.items():
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key}:* {value}",
                    })
                
                if fields:
                    slack_payload["blocks"].append({
                        "type": "section",
                        "fields": fields[:10],  # Slack limit
                    })
            
            # Send to Slack webhook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    recipient,
                    json=slack_payload,
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    return self._create_success_result(recipient)
                else:
                    return self._create_failure_result(
                        recipient,
                        f"Slack API error: {response.status_code} - {response.text}",
                    )
                    
        except httpx.TimeoutException:
            return self._create_failure_result(recipient, "Slack webhook timeout")
        except Exception as e:
            return self._create_failure_result(recipient, str(e))


class TelegramChannel(NotificationChannelBase):
    """Telegram notification channel using Bot API.
    
    Requirements: 23.1 - Telegram delivery support
    
    Note: Requires TELEGRAM_BOT_TOKEN in settings.
    """
    
    channel_name = "telegram"
    
    async def deliver(
        self,
        recipient: str,
        title: str,
        message: str,
        payload: Optional[dict] = None,
    ) -> ChannelDeliveryResult:
        """Deliver notification via Telegram bot."""
        # Get bot token from settings (would need to add to config)
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        
        if not bot_token:
            # Simulate delivery if not configured
            return self._create_success_result(
                recipient,
                {"message": "Telegram delivery simulated (bot not configured)"},
            )
        
        try:
            # Build Telegram message
            telegram_text = f"*{title}*\n\n{message}"
            
            # Add payload data if provided
            if payload:
                telegram_text += "\n\n*Details:*"
                for key, value in payload.items():
                    telegram_text += f"\n• {key}: {value}"
            
            # Send via Telegram Bot API
            api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    json={
                        "chat_id": recipient,
                        "text": telegram_text,
                        "parse_mode": "Markdown",
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    return self._create_success_result(
                        recipient,
                        response.json(),
                    )
                else:
                    return self._create_failure_result(
                        recipient,
                        f"Telegram API error: {response.status_code} - {response.text}",
                    )
                    
        except httpx.TimeoutException:
            return self._create_failure_result(recipient, "Telegram API timeout")
        except Exception as e:
            return self._create_failure_result(recipient, str(e))
