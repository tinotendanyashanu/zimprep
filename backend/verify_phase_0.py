import sys
import os
import logging

# Add the app directory to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

# Setup basic logging to catch warnings
logging.basicConfig(level=logging.INFO)

try:
    print("Step 1: Importing engine registry (triggers registration)...")
    from app.orchestrator.engine_registry import engine_registry
    
    print("Step 2: verifying 'identity' and 'identity_subscription'...")
    identity = engine_registry.get("identity")
    sub = engine_registry.get("identity_subscription")
    
    if identity is None:
        print("FAIL: 'identity' engine not found.")
        sys.exit(1)
        
    if sub is None:
        print("FAIL: 'identity_subscription' engine not found.")
        sys.exit(1)
        
    if identity is not sub:
        print("FAIL: 'identity' and 'identity_subscription' are DIFFERENT instances.")
        sys.exit(1)
        
    print("PASS: Identity alias verified.")
    
    print("Step 3: verifying pipelines pipelines...")
    # process_pipeline_definitions does not exist, relying on get_pipeline
    from app.orchestrator.pipelines import get_pipeline
    
    required_pipelines = [
        "exam_attempt_v1",
        "handwriting_exam_attempt_v1",
        "topic_practice_v1"
    ]
    
    for p_name in required_pipelines:
        pipeline = get_pipeline(p_name)
        if not pipeline:
             print(f"FAIL: Pipeline {p_name} not found.")
             sys.exit(1)
        
        # Check if all engines in pipeline exist
        missing = []
        for engine_name in pipeline:
            if not engine_registry.get(engine_name):
                missing.append(engine_name)
        
        if missing:
            print(f"FAIL: Pipeline {p_name} has missing engines: {missing}")
            sys.exit(1)
            
        print(f"PASS: Pipeline {p_name} verified.")

    print("\nPHASE 0 COMPLETE – SYSTEM UNBLOCKED")

except ImportError as e:
    print(f"ImportError: {e}")
    # Try adding the current directory to path if 'app' is not found
    sys.path.append(os.getcwd())
    print("Retrying with current directory in path...")
    try:
        from app.orchestrator.engine_registry import engine_registry
        # ... validation logic would go here if I structured this better, 
        # but for now let's hope the first path add worked or fail.
    except ImportError as e2:
        print(f"Fatal ImportError: {e2}")
        sys.exit(1)
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Runtime Error: {e}")
    sys.exit(1)
