"""Notification Service for Exam Reminders.

Handles creation, sending, and tracking of exam-related notifications.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config.settings import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing exam notifications."""
    
    # Reminder intervals in timedelta
    REMINDER_INTERVALS = {
        "7_days": timedelta(days=7),
        "3_days": timedelta(days=3),
        "1_day": timedelta(days=1),
        "1_hour": timedelta(hours=1),
    }
    
    # Default reminder intervals for new candidates
    DEFAULT_INTERVALS = ["7_days", "1_day", "1_hour"]
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize notification service.
        
        Args:
            mongo_client: Optional MongoDB client (for testing)
        """
        if mongo_client is None:
            self.client = MongoClient(settings.MONGODB_URI)
        else:
            self.client = mongo_client
        
        self.db = self.client[settings.MONGODB_DB]
        self.notifications = self.db["notifications"]
        self.exam_schedules = self.db["exam_schedules"]
    
    async def create_exam_reminders(self) -> Dict[str, Any]:
        """Background job: Create reminder notifications for upcoming exams.
        
        Checks all scheduled exams and creates reminders at configured intervals.
        
        Returns:
            Dictionary with creation statistics
        """
        try:
            created_count = 0
            skipped_count = 0
            now = datetime.utcnow()
            
            # Check each reminder interval
            for interval_name, interval_delta in self.REMINDER_INTERVALS.items():
                # Find exams that need reminders at this interval
                target_time = now + interval_delta
                
                # Find exams scheduled around this time (±30 minutes window)
                window_start = target_time - timedelta(minutes=30)
                window_end = target_time + timedelta(minutes=30)
                
                exams = self.exam_schedules.find({
                    "scheduled_date": {
                        "$gte": window_start,
                        "$lte": window_end
                    },
                    "status": "scheduled"
                })
                
                for exam in exams:
                    # Get affected candidates
                    candidates = self._get_exam_candidates(exam)
                    
                    for candidate_id in candidates:
                        # Check if reminder already exists
                        existing = self.notifications.find_one({
                            "candidate_id": candidate_id,
                            "schedule_id": exam["schedule_id"],
                            "reminder_interval": interval_name,
                            "notification_type": "exam_reminder"
                        })
                        
                        if existing:
                            skipped_count += 1
                            continue
                        
                        # Create reminder notification
                        notification = {
                            "notification_id": f"notif_{uuid4().hex[:12]}",
                            "candidate_id": candidate_id,
                            "notification_type": "exam_reminder",
                            "exam_id": exam["exam_id"],
                            "schedule_id": exam["schedule_id"],
                            "scheduled_date": exam["scheduled_date"],
                            "reminder_interval": interval_name,
                            "status": "pending",
                            "delivery_method": "email",  # Can be configured per user
                            "metadata": {
                                "subject": exam["subject_name"],
                                "paper": exam["paper_name"],
                                "duration_minutes": exam["duration_minutes"]
                            },
                            "created_at": now,
                            "updated_at": now,
                        }
                        
                        self.notifications.insert_one(notification)
                        created_count += 1
            
            logger.info(
                f"Exam reminder creation complete: {created_count} created, {skipped_count} skipped",
                extra={
                    "created": created_count,
                    "skipped": skipped_count
                }
            )
            
            return {
                "success": True,
                "created": created_count,
                "skipped": skipped_count,
                "timestamp": now.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error creating exam reminders: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_exam_candidates(self, exam: Dict[str, Any]) -> List[str]:
        """Get list of candidates for an exam.
        
        Args:
            exam: Exam schedule document
            
        Returns:
            List of candidate IDs
        """
        candidates = []
        
        # Direct candidate assignment
        if "candidate_ids" in exam and exam["candidate_ids"]:
            candidates.extend(exam["candidate_ids"])
        
        # Cohort assignment (would need to query candidates collection)
        if "cohort_id" in exam:
            # TODO: Query candidates collection for cohort members
            # For now, return empty list for cohort-based
            pass
        
        # School assignment
        if "school_id" in exam:
            # TODO: Query candidates collection for school members
            pass
        
        return list(set(candidates))  # Remove duplicates
    
    async def send_pending_notifications(self, limit: int = 100) -> Dict[str, Any]:
        """Send pending notifications.
        
        Args:
            limit: Maximum notifications to send in one batch
            
        Returns:
            Dictionary with send statistics
        """
        try:
            # Find pending notifications
            pending = self.notifications.find({
                "status": "pending"
            }).limit(limit)
            
            sent_count = 0
            failed_count = 0
            
            for notification in pending:
                success = await self._send_notification(notification)
                
                if success:
                    self.notifications.update_one(
                        {"notification_id": notification["notification_id"]},
                        {
                            "$set": {
                                "status": "sent",
                                "sent_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    sent_count += 1
                else:
                    self.notifications.update_one(
                        {"notification_id": notification["notification_id"]},
                        {
                            "$set": {
                                "status": "failed",
                                "failed_reason": "Delivery service error",
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    failed_count += 1
            
            logger.info(
                f"Notification sending complete: {sent_count} sent, {failed_count} failed",
                extra={"sent": sent_count, "failed": failed_count}
            )
            
            return {
                "success": True,
                "sent": sent_count,
                "failed": failed_count
            }
        
        except Exception as e:
            logger.error(f"Error sending notifications: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_notification(self, notification: Dict[str, Any]) -> bool:
        """Send a single notification.
        
        Args:
            notification: Notification document
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            delivery_method = notification.get("delivery_method", "email")
            
            if delivery_method == "email":
                return await self._send_email_notification(notification)
            elif delivery_method == "sms":
                return await self._send_sms_notification(notification)
            elif delivery_method == "push":
                return await self._send_push_notification(notification)
            elif delivery_method == "in_app":
                # In-app notifications are stored in DB, just mark as sent
                return True
            else:
                logger.warning(f"Unknown delivery method: {delivery_method}")
                return False
        
        except Exception as e:
            logger.error(
                f"Error sending notification {notification['notification_id']}: {e}",
                exc_info=True
            )
            return False
    
    async def _send_email_notification(self, notification: Dict[str, Any]) -> bool:
        """Send email notification.
        
        Args:
            notification: Notification document
            
        Returns:
            True if sent successfully
        """
        # TODO: Integrate with email service (SendGrid, AWS SES, etc.)
        logger.info(
            f"EMAIL NOTIFICATION: {notification['notification_type']} for {notification['candidate_id']}",
            extra={
                "notification_id": notification["notification_id"],
                "type": notification["notification_type"],
                "candidate_id": notification["candidate_id"]
            }
        )
        
        # Simulate successful send
        return True
    
    async def _send_sms_notification(self, notification: Dict[str, Any]) -> bool:
        """Send SMS notification.
        
        Args:
            notification: Notification document
            
        Returns:
            True if sent successfully
        """
        # TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
        logger.info(f"SMS NOTIFICATION: {notification['notification_type']}")
        return True
    
    async def _send_push_notification(self, notification: Dict[str, Any]) -> bool:
        """Send push notification.
        
        Args:
            notification: Notification document
            
        Returns:
            True if sent successfully
        """
        # TODO: Integrate with push service (Firebase, OneSignal, etc.)
        logger.info(f"PUSH NOTIFICATION: {notification['notification_type']}")
        return True
    
    async def create_reschedule_notification(
        self,
        candidate_ids: List[str],
        exam_id: str,
        old_date: datetime,
        new_date: datetime,
        metadata: Dict[str, Any]
    ) -> int:
        """Create notifications for exam reschedule.
        
        Args:
            candidate_ids: List of affected candidates
            exam_id: Exam identifier
            old_date: Original scheduled date
            new_date: New scheduled date
            metadata: Additional exam information
            
        Returns:
            Number of notifications created
        """
        count = 0
        now = datetime.utcnow()
        
        for candidate_id in candidate_ids:
            notification = {
                "notification_id": f"notif_{uuid4().hex[:12]}",
                "candidate_id": candidate_id,
                "notification_type": "exam_rescheduled",
                "exam_id": exam_id,
                "status": "pending",
                "delivery_method": "email",
                "metadata": {
                    **metadata,
                    "old_date": old_date.isoformat(),
                    "new_date": new_date.isoformat()
                },
                "created_at": now,
                "updated_at": now,
            }
            
            self.notifications.insert_one(notification)
            count += 1
        
        logger.info(f"Created {count} reschedule notifications")
        return count
    
    async def get_candidate_notifications(
        self,
        candidate_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get notifications for a candidate.
        
        Args:
            candidate_id: Candidate ID
            limit: Maximum notifications to return
            unread_only: Only return unread notifications
            
        Returns:
            List of notification documents
        """
        query = {"candidate_id": candidate_id}
        
        if unread_only:
            query["status"] = "sent"  # Sent but not read
        
        notifications = list(
            self.notifications.find(query)
            .sort("created_at", -1)
            .limit(limit)
        )
        
        # Convert ObjectId to string
        for notif in notifications:
            if "_id" in notif:
                notif["_id"] = str(notif["_id"])
        
        return notifications
