from app.orchestrator.execution_context import ExecutionContext
from app.orchestrator.engine_registry import engine_registry


class Orchestrator:
    """Central orchestrator for managing engine execution."""
    
    def __init__(self, registry):
        self.registry = registry

    def execute(self, engine_name: str, payload: dict, context: ExecutionContext):
        """Execute an engine with the given payload and context."""
        engine = self.registry.get(engine_name)
        if not engine:
            raise RuntimeError(f"Engine {engine_name} not registered")

        return engine.run(payload, context)


# Global orchestrator instance
orchestrator = Orchestrator(engine_registry)
