"""Notification integration service for all modules.

Provides centralized notification sending for all application events.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notification.service import NotificationService
from app.modules.notification.schemas import (
    NotificationSendRequest,
    NotificationPriority,
)

logger = logging.getLogger(__name__)


class NotificationIntegrationService:
    """Centralized service for sending notifications across all modules."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_service = NotificationService(session)
    
    # ==================== Stream Notifications ====================
    
    async def notify_stream_started(
        self,
        user_id: uuid.UUID,
        stream_title: str,
        channel_name: str,
        stream_id: str,
        youtube_url: Optional[str] = None,
    ) -> None:
        """Notify when a live stream starts."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="stream.started",
                    title="Stream Started",
                    message=f"Your live stream '{stream_title}' on {channel_name} is now live!",
                    priority=NotificationPriority.NORMAL,
                    payload={
                        "stream_id": stream_id,
                        "stream_title": stream_title,
                        "channel_name": channel_name,
                        "youtube_url": youtube_url,
                        "action_url": f"/dashboard/streams/{stream_id}",
                    },
                )
            )
            logger.info(f"Stream started notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send stream started notification: {e}")
    
    async def notify_stream_ended(
        self,
        user_id: uuid.UUID,
        stream_title: str,
        channel_name: str,
        stream_id: str,
        duration_minutes: int,
        peak_viewers: Optional[int] = None,
    ) -> None:
        """Notify when a live stream ends."""
        try:
            message = f"Your live stream '{stream_title}' on {channel_name} has ended after {duration_minutes} minutes."
            if peak_viewers:
                message += f" Peak viewers: {peak_viewers:,}"
            
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="stream.ended",
                    title="Stream Ended",
                    message=message,
                    priority=NotificationPriority.LOW,
                    payload={
                        "stream_id": stream_id,
                        "stream_title": stream_title,
                        "channel_name": channel_name,
                        "duration_minutes": duration_minutes,
                        "peak_viewers": peak_viewers,
                        "action_url": f"/dashboard/streams/{stream_id}",
                    },
                )
            )
            logger.info(f"Stream ended notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send stream ended notification: {e}")
    
    async def notify_stream_error(
        self,
        user_id: uuid.UUID,
        stream_title: str,
        channel_name: str,
        stream_id: str,
        error_message: str,
    ) -> None:
        """Notify when a stream encounters an error."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="stream.health_degraded",
                    title="Stream Error",
                    message=f"Your stream '{stream_title}' on {channel_name} encountered an error: {error_message}",
                    priority=NotificationPriority.HIGH,
                    payload={
                        "stream_id": stream_id,
                        "stream_title": stream_title,
                        "channel_name": channel_name,
                        "error_message": error_message,
                        "action_url": f"/dashboard/streams/{stream_id}",
                    },
                )
            )
            logger.info(f"Stream error notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send stream error notification: {e}")
    
    async def notify_stream_disconnected(
        self,
        user_id: uuid.UUID,
        stream_title: str,
        channel_name: str,
        stream_id: str,
    ) -> None:
        """Notify when a stream disconnects."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="stream.disconnected",
                    title="Stream Disconnected",
                    message=f"Your stream '{stream_title}' on {channel_name} has disconnected. Attempting to reconnect...",
                    priority=NotificationPriority.HIGH,
                    payload={
                        "stream_id": stream_id,
                        "stream_title": stream_title,
                        "channel_name": channel_name,
                        "action_url": f"/dashboard/streams/{stream_id}",
                    },
                )
            )
            logger.info(f"Stream disconnected notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send stream disconnected notification: {e}")
    
    async def notify_stream_reconnected(
        self,
        user_id: uuid.UUID,
        stream_title: str,
        channel_name: str,
        stream_id: str,
    ) -> None:
        """Notify when a stream reconnects successfully."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="stream.reconnected",
                    title="Stream Reconnected",
                    message=f"Your stream '{stream_title}' on {channel_name} has reconnected successfully.",
                    priority=NotificationPriority.NORMAL,
                    payload={
                        "stream_id": stream_id,
                        "stream_title": stream_title,
                        "channel_name": channel_name,
                        "action_url": f"/dashboard/streams/{stream_id}",
                    },
                )
            )
            logger.info(f"Stream reconnected notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send stream reconnected notification: {e}")
    
    # ==================== Video Notifications ====================
    
    async def notify_video_uploaded(
        self,
        user_id: uuid.UUID,
        video_title: str,
        channel_name: str,
        video_id: str,
        youtube_video_id: Optional[str] = None,
    ) -> None:
        """Notify when a video upload completes."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="video.uploaded",
                    title="Video Uploaded",
                    message=f"Your video '{video_title}' has been uploaded to {channel_name} successfully!",
                    priority=NotificationPriority.NORMAL,
                    payload={
                        "video_id": video_id,
                        "video_title": video_title,
                        "channel_name": channel_name,
                        "youtube_video_id": youtube_video_id,
                        "action_url": f"/dashboard/videos/{video_id}",
                    },
                )
            )
            logger.info(f"Video uploaded notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send video uploaded notification: {e}")
    
    async def notify_video_published(
        self,
        user_id: uuid.UUID,
        video_title: str,
        channel_name: str,
        video_id: str,
        youtube_url: Optional[str] = None,
    ) -> None:
        """Notify when a video is published."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="video.published",
                    title="Video Published",
                    message=f"Your video '{video_title}' is now live on {channel_name}!",
                    priority=NotificationPriority.NORMAL,
                    payload={
                        "video_id": video_id,
                        "video_title": video_title,
                        "channel_name": channel_name,
                        "youtube_url": youtube_url,
                        "action_url": f"/dashboard/videos/{video_id}",
                    },
                )
            )
            logger.info(f"Video published notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send video published notification: {e}")
    
    async def notify_video_processing_failed(
        self,
        user_id: uuid.UUID,
        video_title: str,
        video_id: str,
        error_message: str,
    ) -> None:
        """Notify when video processing fails."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="video.processing_failed",
                    title="Video Processing Failed",
                    message=f"Failed to process video '{video_title}': {error_message}",
                    priority=NotificationPriority.HIGH,
                    payload={
                        "video_id": video_id,
                        "video_title": video_title,
                        "error_message": error_message,
                        "action_url": f"/dashboard/videos/{video_id}",
                    },
                )
            )
            logger.info(f"Video processing failed notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send video processing failed notification: {e}")
    
    # ==================== Account Notifications ====================
    
    async def notify_token_expiring(
        self,
        user_id: uuid.UUID,
        channel_name: str,
        account_id: str,
        expires_in_hours: int,
    ) -> None:
        """Notify when OAuth token is about to expire."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="account.token_expiring",
                    title="Token Expiring Soon",
                    message=f"Your YouTube connection for '{channel_name}' will expire in {expires_in_hours} hours. Please re-authenticate to avoid service interruption.",
                    priority=NotificationPriority.HIGH,
                    payload={
                        "account_id": account_id,
                        "channel_name": channel_name,
                        "expires_in_hours": expires_in_hours,
                        "action_url": "/dashboard/accounts",
                    },
                )
            )
            logger.info(f"Token expiring notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send token expiring notification: {e}")
    
    async def notify_token_expired(
        self,
        user_id: uuid.UUID,
        channel_name: str,
        account_id: str,
    ) -> None:
        """Notify when OAuth token has expired."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="account.token_expired",
                    title="Token Expired",
                    message=f"Your YouTube connection for '{channel_name}' has expired. Please re-authenticate to continue using the service.",
                    priority=NotificationPriority.CRITICAL,
                    payload={
                        "account_id": account_id,
                        "channel_name": channel_name,
                        "action_url": "/dashboard/accounts",
                    },
                )
            )
            logger.info(f"Token expired notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send token expired notification: {e}")
    
    async def notify_quota_warning(
        self,
        user_id: uuid.UUID,
        channel_name: str,
        account_id: str,
        quota_used_percent: int,
        quota_remaining: int,
    ) -> None:
        """Notify when API quota is running low."""
        try:
            priority = NotificationPriority.CRITICAL if quota_used_percent >= 90 else NotificationPriority.HIGH
            
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="account.quota_warning",
                    title="API Quota Warning",
                    message=f"Your YouTube API quota for '{channel_name}' is {quota_used_percent}% used. {quota_remaining:,} units remaining.",
                    priority=priority,
                    payload={
                        "account_id": account_id,
                        "channel_name": channel_name,
                        "quota_used_percent": quota_used_percent,
                        "quota_remaining": quota_remaining,
                        "action_url": "/dashboard/accounts",
                    },
                )
            )
            logger.info(f"Quota warning notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send quota warning notification: {e}")
    
    # ==================== Strike Notifications ====================
    
    async def notify_strike_detected(
        self,
        user_id: uuid.UUID,
        channel_name: str,
        strike_type: str,
        severity: str,
        reason: str,
        affected_video_title: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Notify when a strike is detected on the channel."""
        try:
            message = f"A {severity} {strike_type} strike has been detected on '{channel_name}'. Reason: {reason}"
            if affected_video_title:
                message += f" Affected video: {affected_video_title}"
            if expires_at:
                message += f" Expires: {expires_at.strftime('%B %d, %Y')}"
            
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="strike.detected",
                    title="Strike Detected",
                    message=message,
                    priority=NotificationPriority.CRITICAL,
                    payload={
                        "channel_name": channel_name,
                        "strike_type": strike_type,
                        "severity": severity,
                        "reason": reason,
                        "affected_video_title": affected_video_title,
                        "expires_at": expires_at.isoformat() if expires_at else None,
                        "action_url": "/dashboard/strikes",
                    },
                )
            )
            logger.info(f"Strike detected notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send strike detected notification: {e}")
    
    async def notify_strike_resolved(
        self,
        user_id: uuid.UUID,
        channel_name: str,
        strike_type: str,
        reason: str,
    ) -> None:
        """Notify when a strike is resolved."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="strike.resolved",
                    title="Strike Resolved",
                    message=f"The {strike_type} strike on '{channel_name}' has been resolved. Original reason: {reason}",
                    priority=NotificationPriority.NORMAL,
                    payload={
                        "channel_name": channel_name,
                        "strike_type": strike_type,
                        "reason": reason,
                        "action_url": "/dashboard/strikes",
                    },
                )
            )
            logger.info(f"Strike resolved notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send strike resolved notification: {e}")
    
    # ==================== Job Notifications ====================
    
    async def notify_job_failed(
        self,
        user_id: uuid.UUID,
        job_type: str,
        job_id: str,
        error_message: str,
    ) -> None:
        """Notify when a background job fails."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="job.failed",
                    title="Job Failed",
                    message=f"A {job_type} job has failed: {error_message}",
                    priority=NotificationPriority.HIGH,
                    payload={
                        "job_id": job_id,
                        "job_type": job_type,
                        "error_message": error_message,
                        "action_url": "/dashboard/jobs",
                    },
                )
            )
            logger.info(f"Job failed notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send job failed notification: {e}")
    
    # ==================== System Notifications ====================
    
    async def notify_system_error(
        self,
        user_id: uuid.UUID,
        error_type: str,
        error_message: str,
        component: Optional[str] = None,
    ) -> None:
        """Notify about system errors."""
        try:
            message = f"System error: {error_message}"
            if component:
                message = f"System error in {component}: {error_message}"
            
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="system.error",
                    title="System Error",
                    message=message,
                    priority=NotificationPriority.CRITICAL,
                    payload={
                        "error_type": error_type,
                        "error_message": error_message,
                        "component": component,
                    },
                )
            )
            logger.info(f"System error notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send system error notification: {e}")
    
    async def notify_security_alert(
        self,
        user_id: uuid.UUID,
        alert_type: str,
        description: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Notify about security alerts."""
        try:
            message = f"Security alert: {description}"
            if ip_address:
                message += f" (IP: {ip_address})"
            
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="security.alert",
                    title="Security Alert",
                    message=message,
                    priority=NotificationPriority.CRITICAL,
                    payload={
                        "alert_type": alert_type,
                        "description": description,
                        "ip_address": ip_address,
                        "action_url": "/dashboard/security",
                    },
                )
            )
            logger.info(f"Security alert notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send security alert notification: {e}")
    
    # ==================== Comment Notifications ====================
    
    async def notify_comment_received(
        self,
        user_id: uuid.UUID,
        video_title: str,
        comment_author: str,
        comment_preview: str,
        video_id: str,
        requires_moderation: bool = False,
    ) -> None:
        """Notify when a new comment is received."""
        try:
            title = "Comment Needs Review" if requires_moderation else "New Comment"
            message = f"New comment on '{video_title}' from {comment_author}: {comment_preview[:100]}..."
            
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="comment.received" if not requires_moderation else "comment.moderation_required",
                    title=title,
                    message=message,
                    priority=NotificationPriority.HIGH if requires_moderation else NotificationPriority.LOW,
                    payload={
                        "video_id": video_id,
                        "video_title": video_title,
                        "comment_author": comment_author,
                        "requires_moderation": requires_moderation,
                        "action_url": f"/dashboard/videos/{video_id}/comments",
                    },
                )
            )
            logger.info(f"Comment notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send comment notification: {e}")
    
    # ==================== Competitor Notifications ====================
    
    async def notify_competitor_update(
        self,
        user_id: uuid.UUID,
        competitor_name: str,
        update_type: str,
        details: str,
    ) -> None:
        """Notify about competitor activity."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="competitor.update",
                    title="Competitor Update",
                    message=f"{competitor_name}: {update_type} - {details}",
                    priority=NotificationPriority.LOW,
                    payload={
                        "competitor_name": competitor_name,
                        "update_type": update_type,
                        "details": details,
                        "action_url": "/dashboard/competitors",
                    },
                )
            )
            logger.info(f"Competitor update notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send competitor update notification: {e}")
    
    # ==================== Milestone Notifications ====================
    
    async def notify_subscriber_milestone(
        self,
        user_id: uuid.UUID,
        channel_name: str,
        milestone: int,
        current_count: int,
    ) -> None:
        """Notify when a subscriber milestone is reached."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="channel.subscriber_milestone",
                    title="Subscriber Milestone!",
                    message=f"Congratulations! '{channel_name}' has reached {milestone:,} subscribers! Current count: {current_count:,}",
                    priority=NotificationPriority.NORMAL,
                    payload={
                        "channel_name": channel_name,
                        "milestone": milestone,
                        "current_count": current_count,
                        "action_url": "/dashboard/analytics",
                    },
                )
            )
            logger.info(f"Subscriber milestone notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send subscriber milestone notification: {e}")
    
    # ==================== Backup Notifications ====================
    
    async def notify_backup_completed(
        self,
        user_id: uuid.UUID,
        backup_type: str,
        backup_size: str,
        backup_id: str,
    ) -> None:
        """Notify when a backup completes."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="backup.completed",
                    title="Backup Completed",
                    message=f"Your {backup_type} backup has completed successfully. Size: {backup_size}",
                    priority=NotificationPriority.LOW,
                    payload={
                        "backup_id": backup_id,
                        "backup_type": backup_type,
                        "backup_size": backup_size,
                        "action_url": "/dashboard/backups",
                    },
                )
            )
            logger.info(f"Backup completed notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send backup completed notification: {e}")
    
    async def notify_backup_failed(
        self,
        user_id: uuid.UUID,
        backup_type: str,
        error_message: str,
    ) -> None:
        """Notify when a backup fails."""
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="backup.failed",
                    title="Backup Failed",
                    message=f"Your {backup_type} backup has failed: {error_message}",
                    priority=NotificationPriority.HIGH,
                    payload={
                        "backup_type": backup_type,
                        "error_message": error_message,
                        "action_url": "/dashboard/backups",
                    },
                )
            )
            logger.info(f"Backup failed notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send backup failed notification: {e}")
