# Simple minimal test
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("Starting minimal test...")

try:
    print("1. Importing ExecutionContext...")
    from app.orchestrator.execution_context import ExecutionContext
    
    print("2. Creating context...")
    ctx = ExecutionContext.create(user_id="test", request_source="web")
    
    print("3. Importing engines...")
    from app.engines.identity_subscription.engine import IdentitySubscriptionEngine
    
    print("4. Creating engine instance...")
    engine = IdentitySubscriptionEngine()
    
    print("5. Calling engine.run()...")
    payload = {"user_id": "test", "requested_action": "view_subject"}
    result = engine.run(payload, ctx)
    
    print(f"6. Result: success={result.success}")
    print("Test completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
