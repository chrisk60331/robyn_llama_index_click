from typing import List, Optional
import strawberry
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from pathlib import Path

# Define GraphQL types
@strawberry.type
class Document:
    name: str
    size: int

@strawberry.type
class QueryResponse:
    response: str

@strawberry.type
class HealthStatus:
    status: str

# Global reference to the index
# This will be populated by the main application
index = None

# Define the Query type
@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> HealthStatus:
        """Check if the service is up and running"""
        return HealthStatus(status="OK")
    
    @strawberry.field
    def documents(self) -> List[Document]:
        """List all uploaded documents"""
        documents = []
        data_dir = Path("data")
        
        if data_dir.exists():
            for file_path in data_dir.iterdir():
                if file_path.is_file():
                    documents.append(
                        Document(
                            name=file_path.name, 
                            size=file_path.stat().st_size
                        )
                    )
        
        return documents
    
    @strawberry.field
    def query(self, question: str) -> Optional[QueryResponse]:
        """Query the documents using LlamaIndex"""
        if index is None:
            return None
        
        query_engine = index.as_query_engine()
        response = query_engine.query(question)
        
        return QueryResponse(response=str(response))

# Create the schema
schema = strawberry.Schema(query=Query) 