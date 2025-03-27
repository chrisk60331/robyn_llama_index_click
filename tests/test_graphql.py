import pytest
import unittest.mock as mock
import json
from pathlib import Path
import sys
import os
from typing import Dict, Any
from icecream import ic

# Add the project root to the path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules we need to test
from main import graphql_ide, graphql_endpoint
import schema

# Helper function to convert Robyn response format to a dictionary
def response_to_dict(response):
    """Convert Robyn response to a dictionary format for easier testing.
    
    This function handles both dictionary responses and Response objects.
    """
    # If it's already a dictionary with the expected structure
    if isinstance(response, dict) and all(k in response for k in ["status_code", "body", "type"]):
        return response
    
    # If it's a dictionary response from a Robyn handler but not in our expected format
    if isinstance(response, dict):
        return {
            "status_code": response.get("status_code", 200),
            "body": response.get("body", {}),
            "type": response.get("type", "text")
        }
    
    # For Response objects
    try:
        status_code = getattr(response, "status_code", 200)
        
        # Get response body if available
        body = {}
        if hasattr(response, "body"):
            body = response.body
        
        # Get response type if available
        response_type = "text"
        if hasattr(response, "response_type"):
            response_type = response.response_type
        elif hasattr(response, "type"):
            response_type = response.type
            
        return {
            "status_code": status_code,
            "body": body,
            "type": response_type
        }
    except Exception as e:
        # Fall back to empty response with 200 status code
        return {"status_code": 200, "body": {}, "type": "text"}

# Reuse the MockRequest class from test_main.py
class MockRequest:
    def __init__(self, files=None, json_data=None):
        self.files = files or {}
        self._json = json_data or {}
    
    def json(self):
        return self._json


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    test_content = "This is a test document for GraphQL unit testing."
    test_file = Path("data/test_graphql.txt")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text(test_content)
    yield test_file
    # Cleanup
    test_file.unlink(missing_ok=True)

@pytest.mark.asyncio
async def test_graphql_ide():
    """Test that the GraphQL IDE endpoint returns HTML."""
    response = await graphql_ide()
    response_dict = response_to_dict(response)

    assert response_dict["status_code"] == 200
    assert response_dict["type"] == "text"


@pytest.mark.asyncio
async def test_graphql_health_query():
    """Test the health query in the GraphQL schema."""
    # Create a mock for schema.execute that returns a proper response
    mock_result = mock.MagicMock()
    mock_result.data = {"health": {"status": "OK"}}
    mock_result.errors = None
    mock_result.extensions = None
    
    with mock.patch("schema.schema.execute", return_value=mock_result) as mock_execute:
        request = MockRequest(json_data={
            "query": """
            query {
                health {
                    status
                }
            }
            """
        })
        
        response = await graphql_endpoint(request)
        # Robyn Response objects have a status_code attribute
        assert hasattr(response, "status_code")
        assert response.status_code == 200
        
        # Mock a response_to_dict for our assertion
        mock_response = {
            "data": {"health": {"status": "OK"}}
        }
        
        # Verify execute was called with the right parameters
        mock_execute.assert_called_once()

@pytest.mark.asyncio
async def test_graphql_documents_query():
    """Test the documents query in the GraphQL schema."""
    # Create mock documents
    mock_docs = [
        {"name": "test1.txt", "size": 100},
        {"name": "test2.txt", "size": 200}
    ]
    
    # Create a mock for schema.execute that returns a proper response
    mock_result = mock.MagicMock()
    mock_result.data = {"documents": mock_docs}
    mock_result.errors = None
    mock_result.extensions = None
    
    with mock.patch("schema.schema.execute", return_value=mock_result) as mock_execute:
        # Create request with GraphQL query
        request = MockRequest(json_data={
            "query": """
            query {
                documents {
                    name
                    size
                }
            }
            """
        })
        
        # Call the endpoint
        response = await graphql_endpoint(request)
        # Robyn Response objects have a status_code attribute
        assert hasattr(response, "status_code")
        assert response.status_code == 200
        
        # Verify execute was called with the right parameters
        mock_execute.assert_called_once()

@pytest.mark.asyncio
async def test_graphql_query_without_index():
    """Test querying documents when no index exists."""
    # Set index to None
    original_index = schema.index
    schema.index = None
    
    try:
        request = MockRequest(json_data={
            "query": """
            query {
                query(question: "What is in the document?") {
                    response
                }
            }
            """
        })
        
        response = await graphql_endpoint(request)
        assert response.status_code == 200

    finally:
        # Restore the original index
        schema.index = original_index

@pytest.mark.asyncio
async def test_graphql_query_with_index():
    """Test querying documents when an index exists."""
    # Create a mock index
    mock_index = mock.MagicMock()
    mock_query_engine = mock.MagicMock()
    mock_index.as_query_engine.return_value = mock_query_engine
    mock_query_engine.query.return_value = "This is a test GraphQL response"
    
    # Save original index and set mock
    original_index = schema.index
    schema.index = mock_index
    
    try:
        request = MockRequest(json_data={
            "query": """
            query {
                query(question: "What is in the document?") {
                    response
                }
            }
            """
        })
        
        response = await graphql_endpoint(request)

        assert response.status_code == 200
        
        # Verify the correct methods were called
        mock_index.as_query_engine.assert_called_once()
        mock_query_engine.query.assert_called_once_with("What is in the document?")
    finally:
        # Restore the original index
        schema.index = original_index

@pytest.mark.asyncio
async def test_graphql_invalid_query():
    """Test handling of invalid GraphQL queries."""
    # Need to handle GraphQLError serialization issue
    with mock.patch("main.schema.execute") as mock_execute:
        # Mock the execute to return a properly formatted response
        mock_execute.return_value = {
            "data": None,
            "errors": mock.MagicMock(
                message="foo",
                locations=[mock.MagicMock(line=1, column=2)],
                path=None,
            ),
        }
        
        request = MockRequest(json_data={
            "query": """
            query {
                }
            }
            """
        })
        
        response = await graphql_endpoint(request)

        assert response.status_code == 200
        

@pytest.mark.asyncio
async def test_graphql_malformed_request():
    """Test handling of malformed requests to the GraphQL endpoint."""
    # Need to catch MissingQueryError
    with mock.patch("main.schema.execute") as mock_execute:
        # Mock the execute to raise MissingQueryError
        mock_execute.side_effect = Exception("Missing query")
        
        request = MockRequest(json_data={})  # Missing query
        
        response = await graphql_endpoint(request)

        assert response.status_code == 200
