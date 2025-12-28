"""Quick verification script for Phase Six engines."""
import sys
sys.path.insert(0, '.')

from app.orchestrator.engine_registry import engine_registry

engines = sorted(engine_registry._engines.keys())
print(f"✓ Total engines registered: {len(engines)}")
print(f"\n✓ Phase Six engines:")
print(f"  - partial_offline_buffering: {'partial_offline_buffering' in engines}")
print(f"  - device_connectivity: {'device_connectivity' in engines}")
print(f"\n✓ All registered engines:")
for i, engine in enumerate(engines, 1):
    print(f"  {i}. {engine}")
