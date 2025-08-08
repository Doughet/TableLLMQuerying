"""
New Table Processor that uses the interface-based architecture.

This replaces the legacy TableProcessor with a version that uses the new
core interfaces and component system.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

try:
    from ..core.interfaces import DocumentProcessor, LLMClient, DatabaseClient
    from ..core.types import Document, ProcessingResult, DocumentFormat, ComponentConfig
    from ..core.registry import get_global_registry
    from ..core.context import ProcessingContext
    from ..core.exceptions import TableQueryingError, ComponentNotFoundError
    from ..components.factories import DocumentProcessorFactory
    from ..components.adapters import create_llm_adapter, create_database_adapter
    from ..services.service_factory import ServiceFactory, ServiceConfig
    
    # Import legacy services for adapter creation
    from ..services.implementations.bhub_llm_service import BHubLLMService
    from ..services.implementations.sqlite_database_service import SQLiteDatabaseService
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from core.interfaces import DocumentProcessor, LLMClient, DatabaseClient
    from core.types import Document, ProcessingResult, DocumentFormat, ComponentConfig
    from core.registry import get_global_registry
    from core.context import ProcessingContext
    from core.exceptions import TableQueryingError, ComponentNotFoundError
    from components.factories import DocumentProcessorFactory
    from components.adapters import create_llm_adapter, create_database_adapter
    from services.service_factory import ServiceFactory, ServiceConfig
    
    # Import legacy services for adapter creation
    from services.implementations.bhub_llm_service import BHubLLMService
    from services.implementations.sqlite_database_service import SQLiteDatabaseService

logger = logging.getLogger(__name__)


class TableProcessorV2:
    """
    New Table Processor that uses the interface-based architecture.
    
    This version leverages the component registry, factories, and adapters
    to provide a more flexible and extensible processing pipeline.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the new TableProcessor with interface-based components.
        
        Args:
            config: Configuration dictionary with processing options
        """
        self.config = config or {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Setup component registry and context
        self._setup_component_system()
        
        # Initialize the main document processor
        self.document_processor = self._create_document_processor()
        
        # Configuration options
        self.save_outputs = self.config.get('save_outputs', True)
        self.output_dir = Path(self.config.get('output_dir', 'table_querying_outputs'))
        self.clear_database_on_start = self.config.get('clear_database_on_start', False)
        
        # Create output directory
        if self.save_outputs:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear database if requested
        if self.clear_database_on_start:
            try:
                db_client = self.registry.get_component('database_client')
                # This would require implementing a clear method in the interface
                self._logger.info("Database clear requested but not implemented in interface")
            except Exception as e:
                self._logger.warning(f"Could not clear database: {e}")
        
        self._logger.info("TableProcessorV2 initialized with interface-based architecture")
    
    def _setup_component_system(self):
        """Setup the component registry and register all implementations."""
        self.registry = get_global_registry()
        
        # Register interface implementations
        self._register_components()
        
        # Create processing context
        from ..core.types import SystemConfig
        system_config = SystemConfig(
            global_settings=self.config,
            environment=self.config.get('environment', 'development'),
            debug=self.config.get('debug', False)
        )
        
        self.context = ProcessingContext(
            config=system_config,
            registry=self.registry
        )
    
    def _register_components(self):
        """Register all component implementations with the registry."""
        try:
            # Import implementations
            from .interface_implementations import (
                TableExtractorImpl, SchemaGeneratorImpl, TableDescriptorImpl,
                DatabaseClientImpl, DocumentProcessorImpl
            )
            
            # Register core components
            self.registry.register_component(
                'table_extractor', 
                TableExtractorImpl,
                config=ComponentConfig(
                    component_type='table_extractor',
                    implementation='TableExtractorImpl'
                )
            )
            
            self.registry.register_component(
                'schema_generator',
                SchemaGeneratorImpl,
                config=ComponentConfig(
                    component_type='schema_generator',
                    implementation='SchemaGeneratorImpl'
                )
            )
            
            self.registry.register_component(
                'table_descriptor',
                TableDescriptorImpl,
                config=ComponentConfig(
                    component_type='table_descriptor', 
                    implementation='TableDescriptorImpl',
                    config={
                        'api_key': self.config.get('api_key'),
                        'model_id': self.config.get('model_id', 'mistral-small')
                    }
                )
            )
            
            self.registry.register_component(
                'database_client',
                DatabaseClientImpl,
                config=ComponentConfig(
                    component_type='database_client',
                    implementation='DatabaseClientImpl',
                    config={'db_path': self.config.get('db_path', 'table_querying.db')}
                )
            )
            
            self.registry.register_component(
                'document_processor',
                DocumentProcessorImpl,
                config=ComponentConfig(
                    component_type='document_processor',
                    implementation='DocumentProcessorImpl',
                    config=self.config
                ),
                dependencies=['table_extractor', 'schema_generator', 'table_descriptor', 'database_client']
            )
            
            # Register LLM client using adapter if needed
            self._register_llm_client()
            
            self._logger.info("All components registered successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to register components: {e}")
            raise ComponentNotFoundError(f"Component registration failed: {str(e)}", cause=e)
    
    def _register_llm_client(self):
        """Register LLM client using service adapter."""
        try:
            api_key = self.config.get('api_key')
            if not api_key:
                self._logger.warning("No API key provided, LLM features may be limited")
                return
            
            # Create service config
            service_config = ServiceConfig(
                llm_api_key=api_key,
                llm_model_id=self.config.get('model_id', 'mistral-small'),
                llm_service_type=self.config.get('llm_service_type', 'bhub')
            )
            
            # Create LLM service
            llm_service = ServiceFactory.create_llm_service(service_config)
            
            # Create adapter
            llm_client = create_llm_adapter(llm_service)
            
            # Register as singleton instance
            from ..core.registry import ComponentRegistration
            registration = ComponentRegistration(
                component_type='llm_client',
                component_class=type(llm_client),
                config=ComponentConfig(
                    component_type='llm_client',
                    implementation='LLMServiceAdapter'
                ),
                instance=llm_client,
                singleton=True
            )
            
            self.registry._components['llm_client'] = registration
            
            self._logger.info("LLM client registered via adapter")
            
        except Exception as e:
            self._logger.warning(f"Failed to register LLM client: {e}")
    
    def _create_document_processor(self) -> DocumentProcessor:
        """Create the main document processor using the factory."""
        try:
            # Get the document processor from registry
            return self.registry.get_component('document_processor')
            
        except Exception as e:
            self._logger.error(f"Failed to create document processor: {e}")
            raise ComponentNotFoundError(f"Could not create document processor: {str(e)}", cause=e)
    
    def process_document(self, html_file_path: str) -> Dict[str, Any]:
        """
        Process a complete HTML document using the new interface architecture.
        
        Args:
            html_file_path: Path to the HTML file to process
            
        Returns:
            Dictionary containing processing results and metadata
        """
        self._logger.info(f"Processing document: {html_file_path}")
        start_time = datetime.now()
        
        try:
            # Create Document object
            file_path = Path(html_file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {html_file_path}")
            
            document = Document(
                content=file_path.read_text(encoding='utf-8'),
                source_path=file_path,
                format=DocumentFormat.HTML
            )
            
            # Process using the interface
            result = self.document_processor.process_document(document)
            
            # Convert ProcessingResult to legacy format for compatibility
            legacy_results = self._convert_to_legacy_format(result, html_file_path)
            
            # Save outputs if requested
            if self.save_outputs:
                self._save_processing_outputs(result, html_file_path)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            legacy_results['processing_time'] = processing_time
            
            self._logger.info(f"Document processing completed in {processing_time:.2f}s")
            return legacy_results
            
        except Exception as e:
            self._logger.error(f"Document processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'html_file': html_file_path,
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
    
    def _convert_to_legacy_format(self, result: ProcessingResult, html_file_path: str) -> Dict[str, Any]:
        """Convert ProcessingResult to legacy format for compatibility."""
        return {
            'success': result.success,
            'html_file': html_file_path,
            'source_file': str(result.document.source_path) if result.document.source_path else html_file_path,
            'session_id': result.session_id,
            'extraction_results': {
                'html_tables_count': len(result.tables),
                'tables_processed': len(result.schemas)
            },
            'schema_results': {
                'total_schemas': len(result.schemas),
                'successful_schemas': len([s for s in result.schemas if s.row_count > 0])
            },
            'description_results': {
                'total_descriptions': len(result.descriptions),
                'successful_descriptions': len([d for d in result.descriptions if d.content])
            },
            'database_results': {
                'session_id': result.session_id,
                'stored_tables': len(result.tables)
            },
            'statistics': {
                'html_tables': len(result.tables),
                'successful_schemas': len(result.schemas),
                'successful_descriptions': len(result.descriptions),
                'processing_time': result.processing_time,
                'table_count': result.table_count,
                'status': result.status.value
            },
            'error': result.error_message
        }
    
    def _save_processing_outputs(self, result: ProcessingResult, html_file_path: str):
        """Save processing outputs to files."""
        try:
            base_name = Path(html_file_path).stem
            
            # Save basic processing summary
            summary_path = self.output_dir / f"{base_name}_processing_summary.json"
            
            import json
            summary_data = {
                'session_id': result.session_id,
                'success': result.success,
                'processing_time': result.processing_time,
                'table_count': result.table_count,
                'status': result.status.value,
                'tables': [{'table_id': t.table_id, 'position': t.position} for t in result.tables],
                'schemas': [{'table_id': s.table_id, 'columns': len(s.columns), 'rows': s.row_count} for s in result.schemas],
                'descriptions': [{'table_id': d.table_id, 'length': len(d.content)} for d in result.descriptions]
            }
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"Saved processing summary to {summary_path}")
            
        except Exception as e:
            self._logger.warning(f"Failed to save processing outputs: {e}")
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get database summary using the interface."""
        try:
            db_client = self.registry.get_component('database_client')
            return db_client.get_database_summary()
        except Exception as e:
            self._logger.error(f"Failed to get database summary: {e}")
            return {'error': str(e)}
    
    def clear_database(self):
        """Clear database - requires extending the interface."""
        self._logger.warning("Clear database not implemented in interface architecture")
    
    def print_processing_summary(self, results: Dict[str, Any]):
        """Print processing summary (compatible with legacy format)."""
        if not results.get('success', False):
            print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
            return
        
        stats = results.get('statistics', {})
        
        print("\n" + "="*60)
        print("TABLE PROCESSING SUMMARY (Interface Architecture)")
        print("="*60)
        print(f"📄 Source File: {Path(results['html_file']).name}")
        print(f"🆔 Session ID: {results['session_id']}")
        print(f"🏗️  Architecture: Interface-based (V2)")
        
        print(f"\n📊 PROCESSING RESULTS:")
        print(f"  • HTML Tables Found: {stats.get('html_tables', 0)}")
        print(f"  • Schemas Generated: {stats.get('successful_schemas', 0)}")
        print(f"  • Descriptions Created: {stats.get('successful_descriptions', 0)}")
        print(f"  • Processing Time: {stats.get('processing_time', 0):.2f}s")
        print(f"  • Status: {stats.get('status', 'unknown')}")
        
        print(f"\n💾 DATABASE:")
        print(f"  • Session ID: {results.get('session_id')}")
        print(f"  • Tables Stored: {results.get('database_results', {}).get('stored_tables', 0)}")
        
        print("="*60)
        print("✅ Processing completed with interface architecture!")
        print("="*60)
    
    def get_component_info(self) -> Dict[str, Any]:
        """Get information about registered components."""
        try:
            components = self.registry.list_components()
            dependency_graph = self.registry.get_dependency_graph()
            validation = self.registry.validate_dependencies()
            
            return {
                'registered_components': components,
                'dependency_graph': dependency_graph,
                'dependency_validation': {
                    'valid': validation.valid,
                    'errors': validation.errors,
                    'warnings': validation.warnings
                },
                'architecture_version': '2.0 (Interface-based)'
            }
        except Exception as e:
            return {'error': str(e)}