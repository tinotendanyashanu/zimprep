# Test just importing one engine
import sys
from pathlib import Path
import traceback

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    print("Importing identity_subscription engine...")
    from app.engines.identity_subscription.engine import IdentitySubscriptionEngine
    print("Import successful!")
    
    print("\nCreating engine instance...")
    engine = IdentitySubscriptionEngine()
    print("Engine instance created!")
    
except Exception as e:
    print(f"\nError: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
