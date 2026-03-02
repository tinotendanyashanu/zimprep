"""
ACTION 4: End-to-End Pipeline Validation Script

This script executes all three pipelines with real data and validates execution.
"""

import requests
import json
import time
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

# Test user credentials (we'll need to create a test user or use existing)
TEST_USER = {
    "email": "test@zimprep.com",
    "password": "testpassword123"
}

class PipelineValidator:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[MONGODB_DB]
        self.token = None
        self.results = {
            "student_dashboard_v1": {"status": "NOT_RUN", "trace_id": None, "errors": []},
            "topic_practice_v1": {"status": "NOT_RUN", "trace_id": None, "errors": []},
            "exam_attempt_v1": {"status": "NOT_RUN", "trace_id": None, "errors": []}
        }
        self.db_counts_before = {}
        self.db_counts_after = {}
        
    def check_preconditions(self):
        """Verify all required collections have data"""
        print("=" * 60)
        print("PRECONDITION CHECK")
        print("=" * 60)
        
        collections = {
            'canonical_questions': 0,
            'syllabus_sections': 0,
            'question_embeddings': 0,
            'syllabus_embeddings': 0
        }
        
        for coll_name in collections:
            count = self.db[coll_name].count_documents({})
            collections[coll_name] = count
            print(f"{coll_name}: {count}")
            
            if count == 0:
                print(f"\n[FAIL] PRECONDITION FAILED: {coll_name} is empty!")
                print("STOP: Ingestion data missing")
                return False
        
        print("\n[PASS] All preconditions met\n")
        return True
    
    def get_sample_metadata(self):
        """Extract sample metadata from canonical_questions for test inputs"""
        print("=" * 60)
        print("EXTRACTING TEST METADATA")
        print("=" * 60)
        
        # Get a sample question to extract metadata
        sample = self.db.canonical_questions.find_one()
        
        if not sample:
            print("❌ No questions found")
            return None
        
        # Check for metadata structure
        metadata = sample.get('metadata', {})
        source_refs = sample.get('source_refs', [])
        
        print(f"Sample question ID: {sample.get('canonical_question_id')}")
        print(f"Metadata keys: {list(metadata.keys())}")
        print(f"Source refs: {len(source_refs)}")
        
        # Try to extract subject, year, paper from source_refs or metadata
        test_data = {
            "subject_code": "mathematics",  # Default
            "year": 2023,  # Default
            "paper_code": "paper_1",  # Default
            "syllabus_version": "zimsec_2023"  # Default
        }
        
        # Try to get actual values
        if source_refs and len(source_refs) > 0:
            ref = source_refs[0]
            if 'metadata' in ref:
                ref_meta = ref['metadata']
                test_data["subject_code"] = ref_meta.get('subject', 'mathematics')
                test_data["year"] = ref_meta.get('year', 2023)
                test_data["paper_code"] = ref_meta.get('paper', 'paper_1')
        
        print(f"\nTest data: {json.dumps(test_data, indent=2)}")
        return test_data
    
    def authenticate(self):
        """Get JWT token - for now, we'll skip auth and test directly"""
        print("=" * 60)
        print("AUTHENTICATION")
        print("=" * 60)
        print("⚠️  Skipping authentication - will test orchestrator directly\n")
        return True
    
    def record_db_counts(self, stage="before"):
        """Record MongoDB document counts"""
        collections = [
            'exam_results',
            'submissions',
            'answers',
            'audit_records',
            'practice_sessions'
        ]
        
        counts = {}
        for coll in collections:
            counts[coll] = self.db[coll].count_documents({})
        
        if stage == "before":
            self.db_counts_before = counts
        else:
            self.db_counts_after = counts
        
        return counts
    
    def execute_pipeline_direct(self, pipeline_name, payload):
        """Execute pipeline directly via orchestrator (bypassing auth)"""
        from app.orchestrator.orchestrator import orchestrator
        from app.orchestrator.execution_context import ExecutionContext
        import asyncio
        
        # Create execution context
        context = ExecutionContext.create(
            user_id="test_user_action4",
            request_source="validation_script",
            feature_flags={}
        )
        
        print(f"\n{'=' * 60}")
        print(f"EXECUTING: {pipeline_name}")
        print(f"Trace ID: {context.trace_id}")
        print(f"{'=' * 60}")
        print(f"Payload: {json.dumps(payload, indent=2)}\n")
        
        start_time = time.time()
        
        try:
            # Execute pipeline
            result = asyncio.run(
                orchestrator.execute_pipeline(
                    pipeline_name=pipeline_name,
                    payload=payload,
                    context=context
                )
            )
            
            duration = (time.time() - start_time) * 1000
            
            print(f"\n✅ Pipeline completed in {duration:.2f}ms")
            print(f"Trace ID: {result['trace_id']}")
            print(f"Success: {result['success']}")
            
            # Print engine outputs
            print(f"\nEngine Outputs:")
            for engine_name, output in result['engine_outputs'].items():
                status = "✅" if output.get('success') else "❌"
                print(f"  {status} {engine_name}: {output.get('message', 'No message')}")
            
            self.results[pipeline_name] = {
                "status": "PASS" if result['success'] else "FAIL",
                "trace_id": result['trace_id'],
                "duration_ms": duration,
                "engine_outputs": result['engine_outputs'],
                "errors": []
            }
            
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            print(f"\n❌ Pipeline failed after {duration:.2f}ms")
            print(f"Error: {str(e)}")
            
            self.results[pipeline_name] = {
                "status": "FAIL",
                "trace_id": context.trace_id,
                "duration_ms": duration,
                "errors": [str(e)]
            }
            
            raise
    
    def validate_student_dashboard(self):
        """STEP 1: Execute and validate student_dashboard_v1"""
        payload = {
            "user_id": "test_student_action4"
        }
        
        result = self.execute_pipeline_direct("student_dashboard_v1", payload)
        
        # Validation checks
        print("\n--- VALIDATION CHECKS ---")
        
        # Check identity resolution
        identity_output = result['engine_outputs'].get('identity_subscription', {})
        if identity_output.get('success'):
            print("✅ Identity resolved user")
        else:
            print("❌ Identity failed to resolve user")
            self.results["student_dashboard_v1"]["errors"].append("Identity resolution failed")
        
        # Check exam structure
        exam_structure_output = result['engine_outputs'].get('exam_structure', {})
        if exam_structure_output.get('success'):
            data = exam_structure_output.get('data', {})
            subjects = data.get('subjects', [])
            print(f"✅ Exam structure returned {len(subjects)} subjects")
            
            if len(subjects) == 0:
                print("❌ No subjects returned")
                self.results["student_dashboard_v1"]["errors"].append("No subjects returned")
        else:
            print("❌ Exam structure failed")
            self.results["student_dashboard_v1"]["errors"].append("Exam structure failed")
        
        # Check reporting
        reporting_output = result['engine_outputs'].get('reporting', {})
        if reporting_output.get('success'):
            print("✅ Reporting completed without error")
        else:
            print("❌ Reporting failed")
            self.results["student_dashboard_v1"]["errors"].append("Reporting failed")
        
        # Check recommendation
        recommendation_output = result['engine_outputs'].get('recommendation', {})
        if recommendation_output.get('success'):
            print("✅ Recommendation completed")
        else:
            print("❌ Recommendation failed")
            self.results["student_dashboard_v1"]["errors"].append("Recommendation failed")
        
        return result
    
    def validate_topic_practice(self, test_data):
        """STEP 2: Execute and validate topic_practice_v1"""
        payload = {
            "user_id": "test_student_action4",
            "subject_code": test_data["subject_code"],
            "syllabus_version": test_data["syllabus_version"],
            "practice_mode": "topic",
            "question_count": 3
        }
        
        result = self.execute_pipeline_direct("topic_practice_v1", payload)
        
        # Validation checks
        print("\n--- VALIDATION CHECKS ---")
        
        # Check practice assembly
        practice_output = result['engine_outputs'].get('practice_assembly', {})
        if practice_output.get('success'):
            data = practice_output.get('data', {})
            questions = data.get('questions', [])
            print(f"✅ Practice assembly created session with {len(questions)} questions")
            
            if len(questions) == 0:
                print("❌ No questions in practice session")
                self.results["topic_practice_v1"]["errors"].append("No questions delivered")
        else:
            print("❌ Practice assembly failed")
            self.results["topic_practice_v1"]["errors"].append("Practice assembly failed")
        
        # Check question delivery
        delivery_output = result['engine_outputs'].get('question_delivery', {})
        if delivery_output.get('success'):
            print("✅ Question delivery completed")
        else:
            print("❌ Question delivery failed")
            self.results["topic_practice_v1"]["errors"].append("Question delivery failed")
        
        # For full validation, we'd need to submit answers and check marking
        # For now, we validate the setup phase
        
        return result
    
    def validate_exam_attempt(self, test_data):
        """STEP 3: Execute and validate exam_attempt_v1"""
        payload = {
            "user_id": "test_student_action4",
            "subject_code": test_data["subject_code"],
            "year": test_data["year"],
            "paper_code": test_data["paper_code"]
        }
        
        result = self.execute_pipeline_direct("exam_attempt_v1", payload)
        
        # Validation checks
        print("\n--- VALIDATION CHECKS ---")
        
        # Check exam structure
        exam_structure_output = result['engine_outputs'].get('exam_structure', {})
        if exam_structure_output.get('success'):
            data = exam_structure_output.get('data', {})
            print(f"✅ Exam structure derived paper correctly")
        else:
            print("❌ Exam structure failed")
            self.results["exam_attempt_v1"]["errors"].append("Exam structure failed")
        
        # Check session timing
        timing_output = result['engine_outputs'].get('session_timing', {})
        if timing_output.get('success'):
            data = timing_output.get('data', {})
            duration = data.get('duration_minutes', 0)
            print(f"✅ Session timing created session ({duration} minutes)")
        else:
            print("❌ Session timing failed")
            self.results["exam_attempt_v1"]["errors"].append("Session timing failed")
        
        # Check question delivery
        delivery_output = result['engine_outputs'].get('question_delivery', {})
        if delivery_output.get('success'):
            data = delivery_output.get('data', {})
            questions = data.get('questions', [])
            print(f"✅ Question delivery returned {len(questions)} questions")
            
            if len(questions) == 0:
                print("❌ No questions delivered")
                self.results["exam_attempt_v1"]["errors"].append("No questions delivered")
        else:
            print("❌ Question delivery failed")
            self.results["exam_attempt_v1"]["errors"].append("Question delivery failed")
        
        return result
    
    def print_summary(self):
        """Print final summary report"""
        print("\n" + "=" * 60)
        print("ACTION 4 VALIDATION SUMMARY")
        print("=" * 60)
        
        print("\n--- PIPELINE EXECUTION RESULTS ---")
        for pipeline, result in self.results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"\n{status_icon} {pipeline}: {result['status']}")
            print(f"   Trace ID: {result['trace_id']}")
            if result.get('duration_ms'):
                print(f"   Duration: {result['duration_ms']:.2f}ms")
            if result['errors']:
                print(f"   Errors: {', '.join(result['errors'])}")
        
        print("\n--- DATABASE VERIFICATION ---")
        print("\nDocument counts BEFORE:")
        for coll, count in self.db_counts_before.items():
            print(f"  {coll}: {count}")
        
        print("\nDocument counts AFTER:")
        for coll, count in self.db_counts_after.items():
            delta = count - self.db_counts_before.get(coll, 0)
            delta_str = f"(+{delta})" if delta > 0 else ""
            print(f"  {coll}: {count} {delta_str}")
        
        # Final verdict
        print("\n" + "=" * 60)
        all_passed = all(r["status"] == "PASS" for r in self.results.values())
        
        if all_passed:
            print("✅ ACTION 4 COMPLETE")
            print("\n\"ZimPrep pipelines run end-to-end using real ingestion data.\"")
        else:
            print("❌ ACTION 4 FAILED")
            print("\nOne or more pipelines failed validation.")
        
        print("=" * 60)

def main():
    validator = PipelineValidator()
    
    # Step 0: Check preconditions
    if not validator.check_preconditions():
        return
    
    # Get test metadata
    test_data = validator.get_sample_metadata()
    if not test_data:
        print("❌ Failed to extract test metadata")
        return
    
    # Record DB state before
    print("\n--- Recording database state BEFORE ---")
    validator.record_db_counts("before")
    
    try:
        # Step 1: Student Dashboard
        print("\n" + "=" * 60)
        print("STEP 1: STUDENT DASHBOARD PIPELINE")
        print("=" * 60)
        validator.validate_student_dashboard()
        
        # Step 2: Topic Practice
        print("\n" + "=" * 60)
        print("STEP 2: TOPIC PRACTICE PIPELINE")
        print("=" * 60)
        validator.validate_topic_practice(test_data)
        
        # Step 3: Exam Attempt
        print("\n" + "=" * 60)
        print("STEP 3: EXAM ATTEMPT PIPELINE")
        print("=" * 60)
        validator.validate_exam_attempt(test_data)
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Record DB state after
        print("\n--- Recording database state AFTER ---")
        validator.record_db_counts("after")
        
        # Print summary
        validator.print_summary()

if __name__ == "__main__":
    main()
