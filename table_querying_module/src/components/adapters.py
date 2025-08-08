"""
Adapter components for bridging legacy services with new interfaces.

This module provides adapter classes that wrap existing service implementations
to conform to the new core interfaces.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core.interfaces import LLMClient, DatabaseClient
from ..core.types import Schema, Description, Query, QueryResult, ValidationResult
from ..core.exceptions import LLMError, DatabaseError, ValidationError
from ..services.llm_service import LLMService, LLMResponse
from ..services.database_service import DatabaseService, TableMetadata, QueryResult as ServiceQueryResult

logger = logging.getLogger(__name__)


class LLMServiceAdapter(LLMClient):
    """
    Adapter that wraps legacy LLMService to implement the LLMClient interface.
    
    This allows existing LLM service implementations to work with the new
    architecture without modification.
    """
    
    def __init__(self, llm_service: LLMService, **kwargs):
        """
        Initialize adapter with an LLM service instance.
        
        Args:
            llm_service: Legacy LLMService instance to wrap
            **kwargs: Additional configuration
        """
        self.llm_service = llm_service
        self.config = kwargs
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text completion using the wrapped service."""
        try:
            response = self.llm_service.generate_completion(prompt, **kwargs)
            
            if response.success:
                return response.content
            else:
                raise LLMError(
                    f"Text generation failed: {response.error}",
                    error_code="TEXT_GENERATION_FAILED"
                )
                
        except Exception as e:
            self._logger.error(f"Text generation error: {e}")
            raise LLMError(f"Text generation failed: {str(e)}", cause=e)
    
    def generate_description(self, schema: Schema, context: Optional[str] = None) -> Description:
        """Generate table description using the wrapped service."""
        try:
            # Convert schema to format expected by legacy service
            schema_dict = schema.to_dict()
            
            response = self.llm_service.generate_table_description(schema_dict, context or "")
            
            if response.success:
                return Description(
                    table_id=schema.table_id,
                    content=response.content,
                    generated_by=self.llm_service.__class__.__name__,
                    generated_at=datetime.now(),
                    confidence=1.0,
                    metadata=response.metadata or {}
                )
            else:
                raise LLMError(
                    f"Description generation failed: {response.error}",
                    error_code="DESCRIPTION_GENERATION_FAILED"
                )
                
        except Exception as e:
            self._logger.error(f"Description generation error: {e}")
            raise LLMError(f"Description generation failed: {str(e)}", cause=e)
    
    def generate_sql(self, natural_query: str, database_schema: Dict[str, Any]) -> str:
        """Generate SQL query using the wrapped service."""
        try:
            response = self.llm_service.generate_sql_query(natural_query, database_schema)
            
            if response.success:
                return response.content
            else:
                raise LLMError(
                    f"SQL generation failed: {response.error}",
                    error_code="SQL_GENERATION_FAILED"
                )
                
        except Exception as e:
            self._logger.error(f"SQL generation error: {e}")
            raise LLMError(f"SQL generation failed: {str(e)}", cause=e)
    
    def analyze_query(self, query: str, available_tables: List[Schema]) -> Dict[str, Any]:
        """Analyze query feasibility using the wrapped service."""
        try:
            # Convert schemas to format expected by legacy service
            tables_dicts = [schema.to_dict() for schema in available_tables]
            
            response = self.llm_service.analyze_query_feasibility(query, tables_dicts)
            
            if response.success:
                # Parse JSON response if needed
                import json
                try:
                    analysis = json.loads(response.content)
                    return analysis
                except json.JSONDecodeError:
                    # Fallback to simple analysis
                    return {
                        "is_fulfillable": True,
                        "confidence": 0.5,
                        "reasoning": response.content
                    }
            else:
                raise LLMError(
                    f"Query analysis failed: {response.error}",
                    error_code="QUERY_ANALYSIS_FAILED"
                )
                
        except Exception as e:
            self._logger.error(f"Query analysis error: {e}")
            raise LLMError(f"Query analysis failed: {str(e)}", cause=e)
    
    def is_available(self) -> bool:
        """Check if the wrapped service is available."""
        try:
            return self.llm_service.is_available()
        except Exception:
            return False


class DatabaseServiceAdapter(DatabaseClient):
    """
    Adapter that wraps legacy DatabaseService to implement the DatabaseClient interface.
    
    This allows existing database service implementations to work with the new
    architecture without modification.
    """
    
    def __init__(self, database_service: DatabaseService, **kwargs):
        """
        Initialize adapter with a database service instance.
        
        Args:
            database_service: Legacy DatabaseService instance to wrap
            **kwargs: Additional configuration
        """
        self.database_service = database_service
        self.config = kwargs
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def store_processing_result(self, result: Any) -> bool:
        """Store processing result using the wrapped service."""
        try:
            # Convert ProcessingResult to format expected by legacy service
            session_id = result.session_id or "default"
            success_count = 0
            
            for table, schema, description in zip(result.tables, result.schemas, result.descriptions):
                table_data = {
                    "table_id": table.table_id,
                    "source_file": result.document.filename,
                    "rows": schema.row_count,
                    "columns": schema.column_count,
                    "column_names": schema.columns,
                    "column_types": {k: v.value for k, v in schema.column_types.items()},
                    "description": description.content,
                    "row_data": schema.sample_data
                }
                
                if self.database_service.store_table(table_data, session_id):
                    success_count += 1
            
            return success_count == len(result.tables)
            
        except Exception as e:
            self._logger.error(f"Error storing processing result: {e}")
            raise DatabaseError(f"Failed to store processing result: {str(e)}", cause=e)
    
    def get_table_by_id(self, table_id: str) -> Optional[Schema]:
        """Get table schema by ID using the wrapped service."""
        try:
            metadata = self.database_service.get_table_metadata(table_id)
            if not metadata:
                return None
            
            # Convert TableMetadata to Schema
            from ..core.types import DataType
            column_types = {}
            for col_name in metadata.column_names:
                type_str = metadata.column_types.get(col_name, "string")
                try:
                    column_types[col_name] = DataType(type_str)
                except ValueError:
                    column_types[col_name] = DataType.UNKNOWN
            
            return Schema(
                table_id=metadata.table_id,
                columns=metadata.column_names,
                column_types=column_types,
                row_count=metadata.rows,
                metadata={
                    "source_file": metadata.source_file,
                    "created_at": metadata.created_at
                }
            )
            
        except Exception as e:
            self._logger.error(f"Error getting table {table_id}: {e}")
            raise DatabaseError(f"Failed to get table {table_id}: {str(e)}", cause=e)
    
    def search_tables(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Schema]:
        """Search tables using the wrapped service."""
        try:
            # Use legacy search functionality
            search_fields = filters.get("search_fields", ["description", "source_file"]) if filters else None
            metadata_list = self.database_service.search_tables(query, search_fields)
            
            schemas = []
            for metadata in metadata_list:
                schema = self._convert_metadata_to_schema(metadata)
                if schema:
                    schemas.append(schema)
            
            return schemas
            
        except Exception as e:
            self._logger.error(f"Error searching tables: {e}")
            raise DatabaseError(f"Failed to search tables: {str(e)}", cause=e)
    
    def execute_query(self, query: Query) -> QueryResult:
        """Execute query using the wrapped service."""
        try:
            start_time = datetime.now()
            
            # Extract SQL from query (assuming it's already SQL or needs conversion)
            sql_query = query.content
            parameters = query.filters
            
            service_result = self.database_service.execute_query(sql_query, parameters)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return QueryResult(
                success=service_result.success,
                data=service_result.data,
                query=query,
                execution_time=execution_time,
                error_message=service_result.error,
                metadata=service_result.metadata or {}
            )
            
        except Exception as e:
            self._logger.error(f"Error executing query: {e}")
            return QueryResult(
                success=False,
                data=[],
                query=query,
                error_message=str(e)
            )
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get database summary using the wrapped service."""
        try:
            return self.database_service.get_database_summary()
        except Exception as e:
            self._logger.error(f"Error getting database summary: {e}")
            raise DatabaseError(f"Failed to get database summary: {str(e)}", cause=e)
    
    def health_check(self) -> bool:
        """Check database health using the wrapped service."""
        try:
            return self.database_service.is_available()
        except Exception:
            return False
    
    def _convert_metadata_to_schema(self, metadata: TableMetadata) -> Optional[Schema]:
        """Convert legacy TableMetadata to new Schema format."""
        try:
            from ..core.types import DataType
            
            column_types = {}
            for col_name in metadata.column_names:
                type_str = metadata.column_types.get(col_name, "string")
                try:
                    column_types[col_name] = DataType(type_str)
                except ValueError:
                    column_types[col_name] = DataType.UNKNOWN
            
            return Schema(
                table_id=metadata.table_id,
                columns=metadata.column_names,
                column_types=column_types,
                row_count=metadata.rows,
                metadata={
                    "source_file": metadata.source_file,
                    "created_at": metadata.created_at,
                    "description": metadata.description
                }
            )
        except Exception as e:
            self._logger.warning(f"Failed to convert metadata to schema: {e}")
            return None


class MultiProviderLLMClient(LLMClient):
    """LLM client that supports multiple providers with fallback."""
    
    def __init__(self, clients: List[LLMClient], fallback_strategy: str = "round_robin", **kwargs):
        """
        Initialize multi-provider client.
        
        Args:
            clients: List of LLM clients to use
            fallback_strategy: Strategy for fallback ("round_robin", "priority", "random")
        """
        self.clients = clients
        self.fallback_strategy = fallback_strategy
        self.current_client_index = 0
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if not clients:
            raise ConfigurationError("At least one LLM client must be provided")
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using available providers with fallback."""
        for client in self._get_client_order():
            try:
                if client.is_available():
                    return client.generate_text(prompt, **kwargs)
            except Exception as e:
                self._logger.warning(f"Client {client.__class__.__name__} failed: {e}")
                continue
        
        raise LLMError("All LLM providers failed", error_code="ALL_PROVIDERS_FAILED")
    
    def generate_description(self, schema: Schema, context: Optional[str] = None) -> Description:
        """Generate description using available providers with fallback."""
        for client in self._get_client_order():
            try:
                if client.is_available():
                    return client.generate_description(schema, context)
            except Exception as e:
                self._logger.warning(f"Client {client.__class__.__name__} failed: {e}")
                continue
        
        raise LLMError("All LLM providers failed", error_code="ALL_PROVIDERS_FAILED")
    
    def generate_sql(self, natural_query: str, database_schema: Dict[str, Any]) -> str:
        """Generate SQL using available providers with fallback."""
        for client in self._get_client_order():
            try:
                if client.is_available():
                    return client.generate_sql(natural_query, database_schema)
            except Exception as e:
                self._logger.warning(f"Client {client.__class__.__name__} failed: {e}")
                continue
        
        raise LLMError("All LLM providers failed", error_code="ALL_PROVIDERS_FAILED")
    
    def analyze_query(self, query: str, available_tables: List[Schema]) -> Dict[str, Any]:
        """Analyze query using available providers with fallback."""
        for client in self._get_client_order():
            try:
                if client.is_available():
                    return client.analyze_query(query, available_tables)
            except Exception as e:
                self._logger.warning(f"Client {client.__class__.__name__} failed: {e}")
                continue
        
        raise LLMError("All LLM providers failed", error_code="ALL_PROVIDERS_FAILED")
    
    def is_available(self) -> bool:
        """Check if any provider is available."""
        return any(client.is_available() for client in self.clients)
    
    def _get_client_order(self) -> List[LLMClient]:
        """Get clients in order based on fallback strategy."""
        if self.fallback_strategy == "round_robin":
            # Rotate through clients
            ordered_clients = self.clients[self.current_client_index:] + self.clients[:self.current_client_index]
            self.current_client_index = (self.current_client_index + 1) % len(self.clients)
            return ordered_clients
        elif self.fallback_strategy == "priority":
            # Use clients in order of registration (priority)
            return self.clients
        elif self.fallback_strategy == "random":
            # Randomize client order
            import random
            return random.sample(self.clients, len(self.clients))
        else:
            return self.clients


# Adapter factory functions
def create_llm_adapter(llm_service: LLMService, **kwargs) -> LLMClient:
    """Create an LLM client adapter from a legacy LLM service."""
    return LLMServiceAdapter(llm_service, **kwargs)


def create_database_adapter(database_service: DatabaseService, **kwargs) -> DatabaseClient:
    """Create a database client adapter from a legacy database service."""
    return DatabaseServiceAdapter(database_service, **kwargs)


def create_multi_llm_client(clients: List[LLMClient], **kwargs) -> LLMClient:
    """Create a multi-provider LLM client."""
    return MultiProviderLLMClient(clients, **kwargs)