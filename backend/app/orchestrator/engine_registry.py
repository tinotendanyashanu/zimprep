class EngineRegistry:
    """Registry for managing and accessing engines."""
    
    def __init__(self):
        self._engines = {}

    def register(self, name: str, engine):
        """Register an engine by name."""
        self._engines[name] = engine

    def get(self, name: str):
        """Get an engine by name."""
        return self._engines.get(name)


# Global registry instance
engine_registry = EngineRegistry()
