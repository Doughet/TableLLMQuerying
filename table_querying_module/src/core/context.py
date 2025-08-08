"""
Processing context and dependency injection container.

This module provides a centralized context for managing processing state,
configuration, and component dependencies throughout the system.
"""

import logging
from typing import Dict, Any, Optional, Type, TypeVar, Generic, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import threading
from contextlib import contextmanager

from .types import SystemConfig, ComponentConfig, Document, ProcessingResult
from .registry import ComponentRegistry, get_global_registry
from .exceptions import ConfigurationError, ComponentNotFoundError

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ProcessingSession:
    """Represents a processing session with its context."""
    session_id: str
    started_at: datetime = field(default_factory=datetime.now)
    document: Optional[Document] = None
    config: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get session duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if session is completed."""
        return self.completed_at is not None


class ProcessingContext:
    """
    Central context for managing processing state and dependencies.
    
    This class provides a dependency injection container and manages
    the processing context throughout the system lifecycle.
    """
    
    def __init__(
        self,
        config: Optional[SystemConfig] = None,
        registry: Optional[ComponentRegistry] = None
    ):
        self.config = config or SystemConfig()
        self.registry = registry or get_global_registry()
        self._components: Dict[str, Any] = {}
        self._sessions: Dict[str, ProcessingSession] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize components based on configuration
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize components based on configuration."""
        for component_type, component_config in self.config.components.items():
            if component_config.enabled:
                try:
                    self._ensure_component(component_type)
                    self._logger.debug(f"Initialized component: {component_type}")
                except Exception as e:
                    self._logger.error(f"Failed to initialize component {component_type}: {e}")
    
    def get_component(self, component_type: str, **kwargs) -> T:
        """
        Get a component instance with dependency injection.
        
        Args:
            component_type: Type of component to retrieve
            **kwargs: Additional arguments for component creation
            
        Returns:
            Component instance
        """
        return self._ensure_component(component_type, **kwargs)
    
    def _ensure_component(self, component_type: str, **kwargs) -> Any:
        """Ensure a component is available and return it."""
        with self._lock:
            # Check if component is already cached
            cache_key = f"{component_type}:{hash(frozenset(kwargs.items()))}"
            if cache_key in self._components:
                return self._components[cache_key]
            
            # Get component from registry
            try:
                component = self.registry.get_component(component_type, **kwargs)
                self._components[cache_key] = component
                return component
            except ComponentNotFoundError:
                # Try to auto-configure if configuration exists
                component_config = self.config.get_component_config(component_type)
                if component_config:
                    return self._auto_configure_component(component_type, component_config, **kwargs)
                raise
    
    def _auto_configure_component(
        self,
        component_type: str,
        component_config: ComponentConfig,
        **kwargs
    ) -> Any:
        """Auto-configure a component based on configuration."""
        # This would load the component class dynamically based on configuration
        # For now, raise an error indicating missing registration
        raise ComponentNotFoundError(
            f"Component '{component_type}' not registered and auto-configuration not implemented",
            error_code="COMPONENT_AUTO_CONFIG_FAILED",
            details={"component_type": component_type, "config": component_config.to_dict()}
        )
    
    def register_component(
        self,
        component_type: str,
        component_class: Type,
        config: Optional[ComponentConfig] = None,
        **kwargs
    ) -> None:
        """Register a component with the context's registry."""
        self.registry.register_component(component_type, component_class, config, **kwargs)
        
        # Update system configuration
        if config:
            self.config.add_component_config(component_type, config)
    
    def configure_component(self, component_type: str, config_updates: Dict[str, Any]) -> None:
        """Update component configuration."""
        self.registry.configure_component(component_type, config_updates)
        
        # Clear cached instances to force recreation
        keys_to_remove = [key for key in self._components.keys() if key.startswith(f"{component_type}:")]
        for key in keys_to_remove:
            del self._components[key]
    
    def create_session(
        self,
        session_id: str,
        document: Optional[Document] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> ProcessingSession:
        """Create a new processing session."""
        session = ProcessingSession(
            session_id=session_id,
            document=document,
            config=config or {}
        )
        
        self._sessions[session_id] = session
        self._logger.info(f"Created processing session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ProcessingSession]:
        """Get a processing session by ID."""
        return self._sessions.get(session_id)
    
    def complete_session(self, session_id: str) -> None:
        """Mark a processing session as completed."""
        session = self._sessions.get(session_id)
        if session and not session.is_completed:
            session.completed_at = datetime.now()
            self._logger.info(f"Completed processing session: {session_id}")
    
    def list_sessions(self, active_only: bool = False) -> Dict[str, ProcessingSession]:
        """List processing sessions."""
        if active_only:
            return {sid: session for sid, session in self._sessions.items() if not session.is_completed}
        return dict(self._sessions)
    
    def cleanup_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        sessions_to_remove = []
        
        for session_id, session in self._sessions.items():
            if session.started_at.timestamp() < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self._sessions[session_id]
        
        self._logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
        return len(sessions_to_remove)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get_global_setting(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config.global_settings[key] = value
    
    def validate_configuration(self) -> bool:
        """Validate the current configuration."""
        try:
            # Validate component dependencies
            validation_result = self.registry.validate_dependencies()
            if not validation_result.valid:
                self._logger.error(f"Configuration validation failed: {validation_result.get_error_summary()}")
                return False
            
            return True
        except Exception as e:
            self._logger.error(f"Configuration validation error: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get context metrics and statistics."""
        active_sessions = len([s for s in self._sessions.values() if not s.is_completed])
        completed_sessions = len([s for s in self._sessions.values() if s.is_completed])
        
        return {
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
            'total_sessions': len(self._sessions),
            'registered_components': len(self.registry.list_components()),
            'cached_components': len(self._components),
            'configuration': {
                'environment': self.config.environment,
                'debug': self.config.debug,
                'component_count': len(self.config.components)
            }
        }
    
    def reset(self) -> None:
        """Reset the context, clearing all cached components and sessions."""
        with self._lock:
            self._components.clear()
            self._sessions.clear()
            self.registry.clear_singletons()
            self._logger.info("Context reset completed")
    
    @contextmanager
    def processing_session(
        self,
        session_id: str,
        document: Optional[Document] = None,
        auto_complete: bool = True
    ):
        """Context manager for processing sessions."""
        session = self.create_session(session_id, document)
        try:
            yield session
        finally:
            if auto_complete:
                self.complete_session(session_id)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()


class ContextualComponent:
    """Base class for components that need access to processing context."""
    
    def __init__(self, context: ProcessingContext, **kwargs):
        self.context = context
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_component(self, component_type: str, **kwargs) -> Any:
        """Get another component through the context."""
        return self.context.get_component(component_type, **kwargs)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value from context."""
        return self.context.get_config(key, default)
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        self._logger.info(message, extra=kwargs)
    
    def log_error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with context."""
        self._logger.error(message, exc_info=error, extra=kwargs)


# Context factory and utilities
def create_default_context() -> ProcessingContext:
    """Create a default processing context with standard configuration."""
    config = SystemConfig(
        environment="development",
        debug=True,
        global_settings={
            'max_processing_time': 300,
            'default_batch_size': 10,
            'enable_metrics': True,
            'log_level': 'INFO'
        }
    )
    
    return ProcessingContext(config=config)


def create_production_context(config_path: Optional[Path] = None) -> ProcessingContext:
    """Create a production-ready processing context."""
    # Load configuration from file if provided
    if config_path and config_path.exists():
        # Implementation would load from file
        pass
    
    config = SystemConfig(
        environment="production",
        debug=False,
        global_settings={
            'max_processing_time': 600,
            'default_batch_size': 50,
            'enable_metrics': True,
            'log_level': 'WARNING'
        }
    )
    
    return ProcessingContext(config=config)


# Global context management
_global_context: Optional[ProcessingContext] = None
_context_lock = threading.Lock()


def get_global_context() -> ProcessingContext:
    """Get the global processing context."""
    global _global_context
    
    if _global_context is None:
        with _context_lock:
            if _global_context is None:
                _global_context = create_default_context()
    
    return _global_context


def set_global_context(context: ProcessingContext) -> None:
    """Set the global processing context."""
    global _global_context
    with _context_lock:
        _global_context = context


@contextmanager
def temporary_context(context: ProcessingContext):
    """Temporarily use a different global context."""
    original_context = _global_context
    set_global_context(context)
    try:
        yield context
    finally:
        if original_context:
            set_global_context(original_context)