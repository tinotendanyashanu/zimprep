"""Background job for exam reminder notifications.

Run this job every hour to check for upcoming exams and send reminders.

Usage:
    python -m app.jobs.exam_reminder_job
    
Or schedule with cron/APScheduler:
    0 * * * * python -m app.jobs.exam_reminder_job
"""

import asyncio
import logging
from datetime import datetime

from app.services.notification_service import NotificationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_exam_reminder_job():
    """Main job function to create and send exam reminders."""
    logger.info("Starting exam reminder job")
    start_time = datetime.utcnow()
    
    try:
        service = NotificationService()
        
        # Step 1: Create reminder notifications for upcoming exams
        logger.info("Creating exam reminders...")
        create_result = await service.create_exam_reminders()
        logger.info(f"Reminders created: {create_result}")
        
        # Step 2: Send pending notifications
        logger.info("Sending pending notifications...")
        send_result = await service.send_pending_notifications(limit=200)
        logger.info(f"Notifications sent: {send_result}")
        
        # Calculate execution time
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            f"Exam reminder job completed in {elapsed:.2f}s",
            extra={
                "created": create_result.get("created", 0),
                "sent": send_result.get("sent", 0),
                "failed": send_result.get("failed", 0),
                "duration_seconds": elapsed
            }
        )
        
        return {
            "success": True,
            "created": create_result.get("created", 0),
            "sent": send_result.get("sent", 0),
            "failed": send_result.get("failed", 0),
            "duration_seconds": elapsed
        }
    
    except Exception as e:
        logger.error(f"Exam reminder job failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Run the job
    result = asyncio.run(run_exam_reminder_job())
    
    if result["success"]:
        print(f"✅ Job completed successfully")
        print(f"   Created: {result['created']} reminders")
        print(f"   Sent: {result['sent']} notifications")
        if result['failed'] > 0:
            print(f"   Failed: {result['failed']} notifications")
    else:
        print(f"❌ Job failed: {result['error']}")
        exit(1)
