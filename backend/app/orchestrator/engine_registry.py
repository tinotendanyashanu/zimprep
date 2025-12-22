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


# Register all engines
# NOTE: Engines are registered here to avoid circular imports
def _register_engines():
    """Register all engines in the system."""
    # Import and register appeal reconstruction engine
    from app.engines.appeal_reconstruction.engine import AppealReconstructionEngine
    engine_registry.register("appeal_reconstruction", AppealReconstructionEngine())


# Call registration on import
_register_engines()

