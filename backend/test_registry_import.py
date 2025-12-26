import traceback
import sys

try:
    print("Importing engine registry...")
    from app.orchestrator.engine_registry import engine_registry
    print(f"SUCCESS: {len(engine_registry._engines)} engines registered")
    print("Engines:", sorted(engine_registry._engines.keys()))
except Exception as e:
    print("FAILED TO IMPORT ENGINE REGISTRY")
    print("="* 80)
    traceback.print_exc()
    print("="* 80)
    sys.exit(1)
