"""Seed exam schedules to MongoDB for testing upcoming exams feature.

Run with: python backend/scripts/seed_exam_schedules.py
"""

import asyncio
from datetime import datetime, timedelta
from pymongo import MongoClient

from app.config.settings import settings

# Sample exam schedules for testing
SAMPLE_SCHEDULES = [
    {
        "schedule_id": "sched_2025_bio_p2_may",
        "exam_id": "zimsec_5090_biology_paper_2",
        "subject_code": "5090",
        "syllabus_version": "2023-2027",
        "paper_code": "paper_2",
        "subject_name": "Biology",
        "paper_name": "Paper 2 (Theory)",
        "scheduled_date": datetime.utcnow() + timedelta(days=30),  # 30 days from now
        "duration_minutes": 150,
        "status": "scheduled",
        "cohort_id": "cohort_2025_a",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "schedule_id": "sched_2025_math_p1_may",
        "exam_id": "zimsec_4008_mathematics_paper_1",
        "subject_code": "4008",
        "syllabus_version": "2023-2027",
        "paper_code": "paper_1",
        "subject_name": "Mathematics",
        "paper_name": "Paper 1 (Non-Calculator)",
        "scheduled_date": datetime.utcnow() + timedelta(days=35),  # 35 days from now
        "duration_minutes": 120,
        "status": "scheduled",
        "cohort_id": "cohort_2025_a",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "schedule_id": "sched_2025_chem_p3_may",
        "exam_id": "zimsec_5070_chemistry_paper_3",
        "subject_code": "5070",
        "syllabus_version": "2023-2027",
        "paper_code": "paper_3",
        "subject_name": "Chemistry",
        "paper_name": "Paper 3 (Practical)",
        "scheduled_date": datetime.utcnow() + timedelta(days=50),  # 50 days from now
        "duration_minutes": 90,
        "status": "scheduled",
        "school_id": "school_harare_01",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "schedule_id": "sched_2025_phys_p1_june",
        "exam_id": "zimsec_5054_physics_paper_1",
        "subject_code": "5054",
        "syllabus_version": "2023-2027",
        "paper_code": "paper_1",
        "subject_name": "Physics",
        "paper_name": "Paper 1 (Multiple Choice)",
        "scheduled_date": datetime.utcnow() + timedelta(days=70),  # 70 days from now
        "duration_minutes": 60,
        "status": "scheduled",
        "cohort_id": "cohort_2025_b",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "schedule_id": "sched_2025_eng_p2_june",
        "exam_id": "zimsec_1123_english_paper_2",
        "subject_code": "1123",
        "syllabus_version": "2023-2027",
        "paper_code": "paper_2",
        "subject_name": "English Language",
        "paper_name": "Paper 2 (Comprehension)",
        "scheduled_date": datetime.utcnow() + timedelta(days=85),  # 85 days from now
        "duration_minutes": 120,
        "status": "scheduled",
        "candidate_ids": ["student_001", "student_002", "student_003"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "schedule_id": "sched_2025_geo_p1_june",
        "exam_id": "zimsec_2217_geography_paper_1",
        "subject_code": "2217",
        "syllabus_version": "2023-2027",
        "paper_code": "paper_1",
        "subject_name": "Geography",
        "paper_name": "Paper 1 (Physical Geography)",
        "scheduled_date": datetime.utcnow() + timedelta(days=100),  # 100 days from now
        "duration_minutes": 135,
        "status": "scheduled",
        "cohort_id": "cohort_2025_a",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    # Past exam (should be excluded from upcoming)
    {
        "schedule_id": "sched_2024_bio_p1_past",
        "exam_id": "zimsec_5090_biology_paper_1",
        "subject_code": "5090",
        "syllabus_version": "2023-2027",
        "paper_code": "paper_1",
        "subject_name": "Biology",
        "paper_name": "Paper 1 (Multiple Choice)",
        "scheduled_date": datetime.utcnow() - timedelta(days=10),  # 10 days ago
        "duration_minutes": 60,
        "status": "completed",
        "cohort_id": "cohort_2024_a",
        "created_at": datetime.utcnow() - timedelta(days=20),
        "updated_at": datetime.utcnow() - timedelta(days=9),
    },
    # Cancelled exam (should be excluded)
    {
        "schedule_id": "sched_2025_hist_p2_cancelled",
        "exam_id": "zimsec_2147_history_paper_2",
        "subject_code": "2147",
        "syllabus_version": "2023-2027",
        "paper_code": "paper_2",
        "subject_name": "History",
        "paper_name": "Paper 2 (Depth Studies)",
        "scheduled_date": datetime.utcnow() + timedelta(days=60),
        "duration_minutes": 120,
        "status": "cancelled",
        "cohort_id": "cohort_2025_a",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
]


def seed_exam_schedules():
    """Seed exam schedules into MongoDB."""
    print("🔧 Connecting to MongoDB...")
    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    collection = db["exam_schedules"]
    
    print(f"📊 Current exam schedules count: {collection.count_documents({})}")
    
    # Clear existing sample data (optional - comment out to preserve)
    print("🗑️  Clearing existing exam schedules...")
    collection.delete_many({})
    
    # Insert sample schedules
    print(f"📝 Inserting {len(SAMPLE_SCHEDULES)} sample exam schedules...")
    result = collection.insert_many(SAMPLE_SCHEDULES)
    
    print(f"✅ Successfully inserted {len(result.inserted_ids)} exam schedules!")
    
    # Show summary
    print("\n📋 Summary:")
    scheduled_count = collection.count_documents({"status": "scheduled"})
    past_count = collection.count_documents({"status": "completed"})
    cancelled_count = collection.count_documents({"status": "cancelled"})
    
    print(f"  - Scheduled (upcoming): {scheduled_count}")
    print(f"  - Completed (past): {past_count}")
    print(f"  - Cancelled: {cancelled_count}")
    
    # Show upcoming exams
    print("\n📅 Upcoming exams (next 5):")
    upcoming = collection.find(
        {"scheduled_date": {"$gt": datetime.utcnow()}, "status": "scheduled"}
    ).sort("scheduled_date", 1).limit(5)
    
    for exam in upcoming:
        date_str = exam["scheduled_date"].strftime("%Y-%m-%d %H:%M UTC")
        print(f"  - {exam['subject_name']} {exam['paper_name']} on {date_str}")
    
    print("\n✨ Seeding complete!")
    client.close()


if __name__ == "__main__":
    seed_exam_schedules()
