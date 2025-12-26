"""Verification script for Phase 3 infrastructure setup.

Checks that all MongoDB collections are properly configured and populated.

Run with: python -m scripts.verify_phase3_setup
"""

import asyncio
from motor import motor_asyncio
import os
from datetime import datetime, timedelta


async def verify_setup():
    """Verify all Phase 3 infrastructure is set up correctly."""
    
    print("🔍 ZimPrep Phase 3 Infrastructure Verification")
    print("=" * 80)
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client.zimprep
    
    print(f"\n✅ Connected to MongoDB: {mongo_uri}\n")
    
    results = {
        "collections": {"pass": 0, "fail": 0},
        "indexes": {"pass": 0, "fail": 0},
        "data": {"pass": 0, "fail": 0}
    }
    
    # Test 1: Check collections exist
    print("📦 Testing Collections...")
    print("-" * 80)
    
    required_collections = [
        "questions",
        "ai_cache_persistent",
        "ai_cost_tracking"
    ]
    
    existing_collections = await db.list_collection_names()
    
    for collection_name in required_collections:
        if collection_name in existing_collections:
            print(f"   ✅ {collection_name} exists")
            results["collections"]["pass"] += 1
        else:
            print(f"   ❌ {collection_name} MISSING")
            results["collections"]["fail"] += 1
    
    # Test 2: Check indexes
    print(f"\n🔑 Testing Indexes...")
    print("-" * 80)
    
    # Check questions indexes
    questions_indexes = await db.questions.index_information()
    expected_question_indexes = ["question_id_1", "topic_id_1_difficulty_1", "subject_1_syllabus_version_1"]
    
    for index_name in expected_question_indexes:
        if index_name in questions_indexes:
            print(f"   ✅ questions.{index_name}")
            results["indexes"]["pass"] += 1
        else:
            print(f"   ❌ questions.{index_name} MISSING")
            results["indexes"]["fail"] += 1
    
    # Check cache indexes
    cache_indexes = await db.ai_cache_persistent.index_information()
    if "cache_key_1" in cache_indexes:
        print(f"   ✅ ai_cache_persistent.cache_key_1")
        results["indexes"]["pass"] += 1
    else:
        print(f"   ❌ ai_cache_persistent.cache_key_1 MISSING")
        results["indexes"]["fail"] += 1
    
    # Check cost tracking indexes
    cost_indexes = await db.ai_cost_tracking.index_information()
    if "user_id_1_timestamp_-1" in cost_indexes or "user_id_1" in cost_indexes:
        print(f"   ✅ ai_cost_tracking user indexes")
        results["indexes"]["pass"] += 1
    else:
        print(f"   ❌ ai_cost_tracking user indexes MISSING")
        results["indexes"]["fail"] += 1
    
    # Test 3: Check data population
    print(f"\n📊 Testing Data Population...")
    print("-" * 80)
    
    # Count questions
    question_count = await db.questions.count_documents({})
    if question_count >= 1000:
        print(f"   ✅ Questions: {question_count} (target: 1000+)")
        results["data"]["pass"] += 1
    elif question_count > 0:
        print(f"   ⚠️  Questions: {question_count} (target: 1000+) - PARTIAL")
        results["data"]["fail"] += 1
    else:
        print(f"   ❌ Questions: 0 (target: 1000+) - EMPTY")
        results["data"]["fail"] += 1
    
    # Check subject distribution
    if question_count > 0:
        math_count = await db.questions.count_documents({"subject": "Mathematics"})
        science_count = await db.questions.count_documents({"subject": "Science"})
        english_count = await db.questions.count_documents({"subject": "English"})
        
        print(f"      - Mathematics: {math_count}")
        print(f"      - Science: {science_count}")
        print(f"      - English: {english_count}")
    
    # Check difficulty distribution
    if question_count > 0:
        easy_count = await db.questions.count_documents({"difficulty": "easy"})
        medium_count = await db.questions.count_documents({"difficulty": "medium"})
        hard_count = await db.questions.count_documents({"difficulty": "hard"})
        
        easy_pct = (easy_count / question_count) * 100
        medium_pct = (medium_count / question_count) * 100
        hard_pct = (hard_count / question_count) * 100
        
        print(f"      - Easy: {easy_count} ({easy_pct:.1f}%) - target: 40%")
        print(f"      - Medium: {medium_count} ({medium_pct:.1f}%) - target: 40%")
        print(f"      - Hard: {hard_count} ({hard_pct:.1f}%) - target: 20%")
        
        # Check if distribution is close to target
        if 35 <= easy_pct <= 45 and 35 <= medium_pct <= 45 and 15 <= hard_pct <= 25:
            print(f"   ✅ Difficulty distribution is balanced")
            results["data"]["pass"] += 1
        else:
            print(f"   ⚠️  Difficulty distribution is off-target")
            results["data"]["fail"] += 1
    
    # Test 4: Sample queries
    print(f"\n🔍 Testing Sample Queries...")
    print("-" * 80)
    
    # Query for specific topic
    if question_count > 0:
        sample_question = await db.questions.find_one({"subject": "Mathematics"})
        if sample_question:
            print(f"   ✅ Sample query successful")
            print(f"      Question: {sample_question['question_text'][:60]}...")
            results["data"]["pass"] += 1
        else:
            print(f"   ❌ Sample query failed")
            results["data"]["fail"] += 1
    
    # Print summary
    print(f"\n" + "=" * 80)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 80)
    
    total_pass = sum(r["pass"] for r in results.values())
    total_fail = sum(r["fail"] for r in results.values())
    total_tests = total_pass + total_fail
    
    print(f"\n   Collections: {results['collections']['pass']}/{results['collections']['pass'] + results['collections']['fail']} passed")
    print(f"   Indexes: {results['indexes']['pass']}/{results['indexes']['pass'] + results['indexes']['fail']} passed")
    print(f"   Data: {results['data']['pass']}/{results['data']['pass'] + results['data']['fail']} passed")
    print(f"\n   TOTAL: {total_pass}/{total_tests} tests passed")
    
    if total_fail == 0:
        print(f"\n✅ ALL TESTS PASSED! Phase 3 infrastructure is ready!")
    elif total_pass > total_tests / 2:
        print(f"\n⚠️  PARTIAL SUCCESS: {total_fail} test(s) failed. Review output above.")
    else:
        print(f"\n❌ SETUP INCOMPLETE: {total_fail} test(s) failed. Run setup scripts.")
    
    client.close()
    
    return total_fail == 0


if __name__ == "__main__":
    success = asyncio.run(verify_setup())
    exit(0 if success else 1)
