import sys
import os

# Add backend to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.orchestrator.integrity import validate_stage_output, IntegrityError

def test_integrity():
    print("Testing data integrity logic...")
    
    # 1. Test Embedding Validation
    print("\n[Embedding]")
    try:
        validate_stage_output("embedding", {"embedding": [0.1] * 1536}, "test_trace")
        print("[PASS] Valid embedding accepted")
    except Exception as e:
        print(f"[FAIL] Valid embedding rejected: {e}")

    try:
        validate_stage_output("embedding", {}, "test_trace")
        print("[FAIL] Empty dict accepted")
    except IntegrityError:
        print("[PASS] Empty dict rejected")

    try:
        validate_stage_output("embedding", {"embedding": []}, "test_trace")
        print("[FAIL] Empty vector list accepted")
    except IntegrityError:
        print("[PASS] Empty vector list rejected")

    # 2. Test Retrieval Validation
    print("\n[Retrieval]")
    try:
        validate_stage_output("retrieval", {"evidence": ["doc1"]}, "test_trace")
        print("[PASS] Valid evidence accepted")
    except Exception as e:
        print(f"[FAIL] Valid evidence rejected: {e}")

    try:
        validate_stage_output("retrieval", {"evidence": []}, "test_trace")
        print("[FAIL] Empty evidence list accepted")
    except IntegrityError:
        print("[PASS] Empty evidence list rejected")
        
    try:
        validate_stage_output("retrieval", {}, "test_trace")
        print("[FAIL] Missing keys accepted")
    except IntegrityError:
        print("[PASS] Missing keys rejected")

    # 3. Test Reasoning Validation
    print("\n[Reasoning]")
    try:
        validate_stage_output("reasoning_marking", {"marks": [{"id": 1}], "score": 85}, "test_trace")
        print("[PASS] Valid marks accepted")
    except Exception as e:
        print(f"[FAIL] Valid marks rejected: {e}")

    try:
        validate_stage_output("reasoning_marking", {"score": -10}, "test_trace")
        print("[FAIL] Negative score accepted")
    except IntegrityError:
        print("[PASS] Negative score rejected")

    try:
        validate_stage_output("reasoning_marking", {}, "test_trace")
        print("[FAIL] Empty reasoning accepted")
    except IntegrityError:
        print("[PASS] Empty reasoning rejected")

    print("\nIntegrity Logic Tests Completed.")

if __name__ == "__main__":
    test_integrity()
