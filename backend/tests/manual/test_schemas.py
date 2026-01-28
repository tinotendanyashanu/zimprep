# Test just importing the contract
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("Testing contract import...")

try:
    print("1. Importing EngineResponse...")
    from app.contracts.engine_response import EngineResponse
    print("OK")
    
    print("2. Importing EngineTrace...")
    from app.contracts.trace import EngineTrace
    print("OK")
    
    print("3. Importing identity schemas...")
    from app.engines.identity_subscription.schemas.input import IdentitySubscriptionInput
    print("OK")
    
    print("4. Importing identity output...")
    from app.engines.identity_subscription.schemas.output import IdentitySubscriptionOutput
    print("OK")
    
    print("All imports successful!")
    
except Exception as e:
    print(f"Error at import: {e}")
    import traceback
    traceback.print_exc()
