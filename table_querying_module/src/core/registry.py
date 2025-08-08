"""
Component registry for managing pluggable components.

This module provides a central registry for all system components,
enabling dynamic component discovery and dependency injection.
"""

import logging
import inspect
from typing import Dict, List, Any, Type, Optional, Callable, TypeVar
from pathlib import Path
import importlib.util
import sys
from dataclasses import dataclass, field
from threading import Lock

from .interfaces import *
from .types import ComponentConfig, ValidationResult
from .exceptions import (
    ComponentNotFoundError, ComponentInitializationError, 
    ValidationError, ConfigurationError
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ComponentRegistration:
    """Registration information for a component."""
    component_type: str
    component_class: Type
    config: ComponentConfig
    instance: Optional[Any] = None
    singleton: bool = True
    factory: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    
    def create_instance(self, registry: 'ComponentRegistry', **kwargs) -> Any:
        """Create an instance of the component."""
        if self.singleton and self.instance is not None:
            return self.instance
        
        try:
            # Resolve dependencies
            resolved_deps = {}
            for dep_type in self.dependencies:
                resolved_deps[dep_type] = registry.get_component(dep_type)
            
            # Merge with provided kwargs
            init_kwargs = {**resolved_deps, **self.config.config, **kwargs}
            
            if self.factory:
                instance = self.factory(**init_kwargs)
            else:
                instance = self.component_class(**init_kwargs)
            
            if self.singleton:
                self.instance = instance
            
            return instance
            
        except Exception as e:
            raise ComponentInitializationError(
                f"Failed to create instance of {self.component_type}",
                error_code="COMPONENT_INIT_FAILED",
                details={"component_class": str(self.component_class), "error": str(e)},
                cause=e
            )


class ComponentRegistry:
    """Central registry for system components."""
    
    def __init__(self):
        self._components: Dict[str, ComponentRegistration] = {}
        self._aliases: Dict[str, str] = {}
        self._lock = Lock()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Register built-in component types
        self._register_built_in_types()
    
    def _register_built_in_types(self):
        """Register built-in component type mappings."""
        self._component_interfaces = {
            'document_processor': DocumentProcessor,
            'table_extractor': TableExtractor,
            'schema_generator': SchemaGenerator,
            'table_descriptor': TableDescriptor,
            'database_client': DatabaseClient,
            'llm_client': LLMClient,
            'query_processor': QueryProcessor,
            'chat_interface': ChatInterface,
            'component_manager': ComponentManager,
            'plugin_manager': PluginManager,
            'configuration_manager': ConfigurationManager,
            'metrics_collector': MetricsCollector,
            'logger': Logger,
        }
    
    def register_component(
        self,
        component_type: str,
        component_class: Type,
        config: Optional[ComponentConfig] = None,
        singleton: bool = True,
        factory: Optional[Callable] = None,
        dependencies: Optional[List[str]] = None,
        alias: Optional[str] = None,
        skip_validation: bool = False
    ) -> None:
        """
        Register a component implementation.
        
        Args:
            component_type: Type of component (e.g., 'llm_client', 'database_client')
            component_class: Class implementing the component interface
            config: Component configuration
            singleton: Whether to create singleton instances
            factory: Optional factory function for creating instances
            dependencies: List of component types this component depends on
            alias: Optional alias for the component type
        """
        with self._lock:
            # Validate component implements required interface (unless skipped for testing)
            if not skip_validation:
                validation = self.validate_component(component_type, component_class)
                if not validation.valid:
                    raise ValidationError(
                        f"Component {component_class} does not implement required interface",
                        error_code="INVALID_COMPONENT",
                        details={"errors": validation.errors}
                    )
            
            # Create default config if not provided
            if config is None:
                config = ComponentConfig(
                    component_type=component_type,
                    implementation=component_class.__name__
                )
            
            registration = ComponentRegistration(
                component_type=component_type,
                component_class=component_class,
                config=config,
                singleton=singleton,
                factory=factory,
                dependencies=dependencies or []
            )
            
            self._components[component_type] = registration
            
            # Register alias if provided
            if alias:
                self._aliases[alias] = component_type
            
            self._logger.info(f"Registered component: {component_type} -> {component_class.__name__}")
    
    def get_component(self, component_type: str, **kwargs) -> Any:
        """
        Get a component instance by type.
        
        Args:
            component_type: Type of component to retrieve
            **kwargs: Additional arguments for component creation
            
        Returns:
            Component instance
        """
        # Resolve alias if needed
        resolved_type = self._aliases.get(component_type, component_type)
        
        if resolved_type not in self._components:
            raise ComponentNotFoundError(
                f"Component type '{component_type}' not registered",
                error_code="COMPONENT_NOT_FOUND",
                details={"available_types": list(self._components.keys())}
            )
        
        registration = self._components[resolved_type]
        return registration.create_instance(self, **kwargs)
    
    def has_component(self, component_type: str) -> bool:
        """Check if a component type is registered."""
        resolved_type = self._aliases.get(component_type, component_type)
        return resolved_type in self._components
    
    def list_components(self) -> Dict[str, List[str]]:
        """List all registered components organized by interface type."""
        components_by_interface = {}
        
        for component_type, registration in self._components.items():
            interface_name = self._get_interface_name(component_type)
            if interface_name not in components_by_interface:
                components_by_interface[interface_name] = []
            
            components_by_interface[interface_name].append({
                'type': component_type,
                'class': registration.component_class.__name__,
                'implementation': registration.config.implementation,
                'singleton': registration.singleton
            })
        
        return components_by_interface
    
    def validate_component(self, component_type: str, component_class: Type) -> ValidationResult:
        """
        Validate that a component class implements the required interface.
        
        Args:
            component_type: Type of component
            component_class: Class to validate
            
        Returns:
            Validation result
        """
        result = ValidationResult(valid=True)
        
        # Get expected interface
        expected_interface = self._component_interfaces.get(component_type)
        if not expected_interface:
            result.add_error(f"Unknown component type: {component_type}")
            return result
        
        # Check if class implements interface
        if not issubclass(component_class, expected_interface):
            result.add_error(f"Class {component_class} does not implement {expected_interface}")
            return result
        
        # Check if all abstract methods are implemented
        abstract_methods = self._get_abstract_methods(expected_interface)
        class_methods = set(dir(component_class))
        
        missing_methods = abstract_methods - class_methods
        if missing_methods:
            result.add_error(f"Missing required methods: {', '.join(missing_methods)}")
        
        return result
    
    def configure_component(self, component_type: str, config_updates: Dict[str, Any]) -> None:
        """Update configuration for a registered component."""
        if component_type not in self._components:
            raise ComponentNotFoundError(f"Component type '{component_type}' not registered")
        
        registration = self._components[component_type]
        registration.config.config.update(config_updates)
        
        # Clear singleton instance to force recreation with new config
        if registration.singleton:
            registration.instance = None
    
    def unregister_component(self, component_type: str) -> None:
        """Unregister a component."""
        with self._lock:
            if component_type in self._components:
                del self._components[component_type]
                self._logger.info(f"Unregistered component: {component_type}")
            
            # Remove any aliases pointing to this component
            aliases_to_remove = [alias for alias, target in self._aliases.items() if target == component_type]
            for alias in aliases_to_remove:
                del self._aliases[alias]
    
    def clear_singletons(self) -> None:
        """Clear all singleton instances, forcing recreation on next access."""
        with self._lock:
            for registration in self._components.values():
                if registration.singleton:
                    registration.instance = None
    
    def get_component_config(self, component_type: str) -> ComponentConfig:
        """Get configuration for a component."""
        if component_type not in self._components:
            raise ComponentNotFoundError(f"Component type '{component_type}' not registered")
        
        return self._components[component_type].config
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get the dependency graph of all registered components."""
        return {
            component_type: registration.dependencies
            for component_type, registration in self._components.items()
        }
    
    def validate_dependencies(self) -> ValidationResult:
        """Validate that all component dependencies can be resolved."""
        result = ValidationResult(valid=True)
        
        for component_type, registration in self._components.items():
            for dep_type in registration.dependencies:
                if not self.has_component(dep_type):
                    result.add_error(
                        f"Component '{component_type}' depends on unregistered component '{dep_type}'"
                    )
        
        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies()
        if circular_deps:
            result.add_error(f"Circular dependencies detected: {circular_deps}")
        
        return result
    
    def _get_interface_name(self, component_type: str) -> str:
        """Get the interface name for a component type."""
        interface = self._component_interfaces.get(component_type)
        return interface.__name__ if interface else "Unknown"
    
    def _get_abstract_methods(self, interface_class: Type) -> set:
        """Get set of abstract method names from an interface class."""
        abstract_methods = set()
        for name, method in inspect.getmembers(interface_class, predicate=inspect.isfunction):
            if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
                abstract_methods.add(name)
        return abstract_methods
    
    def _detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the component graph."""
        def visit(component_type: str, path: List[str], visited: set, cycles: List[List[str]]):
            if component_type in path:
                # Found a cycle
                cycle_start = path.index(component_type)
                cycles.append(path[cycle_start:] + [component_type])
                return
            
            if component_type in visited:
                return
            
            visited.add(component_type)
            registration = self._components.get(component_type)
            
            if registration:
                for dep in registration.dependencies:
                    visit(dep, path + [component_type], visited, cycles)
        
        cycles = []
        visited = set()
        
        for component_type in self._components:
            if component_type not in visited:
                visit(component_type, [], visited, cycles)
        
        return cycles


class PluginLoader:
    """Utility class for loading plugins from external files."""
    
    def __init__(self, registry: ComponentRegistry):
        self.registry = registry
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def load_plugin(self, plugin_path: Path) -> Dict[str, Any]:
        """
        Load a plugin from a Python file.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            Plugin metadata
        """
        if not plugin_path.exists():
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")
        
        # Load the module
        spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
        if spec is None or spec.loader is None:
            raise ValidationError(f"Cannot load plugin from {plugin_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[plugin_path.stem] = module
        spec.loader.exec_module(module)
        
        # Look for plugin registration function
        if hasattr(module, 'register_plugin'):
            plugin_info = module.register_plugin(self.registry)
            self._logger.info(f"Loaded plugin: {plugin_path.name}")
            return plugin_info
        else:
            raise ValidationError(f"Plugin {plugin_path} does not have register_plugin function")
    
    def discover_plugins(self, search_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        Discover and load plugins from search paths.
        
        Args:
            search_paths: List of directories to search for plugins
            
        Returns:
            List of loaded plugin metadata
        """
        loaded_plugins = []
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            # Look for Python files
            for plugin_file in search_path.glob("*_plugin.py"):
                try:
                    plugin_info = self.load_plugin(plugin_file)
                    loaded_plugins.append(plugin_info)
                except Exception as e:
                    self._logger.warning(f"Failed to load plugin {plugin_file}: {e}")
        
        return loaded_plugins


# Global registry instance
_global_registry: Optional[ComponentRegistry] = None
_registry_lock = Lock()


def get_global_registry() -> ComponentRegistry:
    """Get the global component registry instance."""
    global _global_registry
    
    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = ComponentRegistry()
    
    return _global_registry


def register_component(component_type: str, component_class: Type, **kwargs) -> None:
    """Register a component with the global registry."""
    registry = get_global_registry()
    registry.register_component(component_type, component_class, **kwargs)


def get_component(component_type: str, **kwargs) -> Any:
    """Get a component from the global registry."""
    registry = get_global_registry()
    return registry.get_component(component_type, **kwargs)