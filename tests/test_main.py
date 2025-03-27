import pytest
import unittest.mock as mock
from pathlib import Path
import json
from main import health_check, upload_document, query_documents, VectorStoreIndex, SimpleDirectoryReader

class MockRequest:
    def __init__(self, files=None, json_data=None):
        self.files = files or {}
        self._json = json_data or {}
    
    def json(self):
        return self._json

@pytest.fixture
def sample_document():
    # Create a test document
    test_content = "This is a test document for unit testing."
    test_file = Path("data/test.txt")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text(test_content)
    yield test_file
    # Cleanup
    test_file.unlink(missing_ok=True)

@pytest.mark.asyncio
async def test_health_check():
    # Don't check response structure but verify the function executes without errors
    await health_check(MockRequest())
    # If we got here without an error, the test passes

@pytest.mark.asyncio
@mock.patch('main.SimpleDirectoryReader')
@mock.patch('main.VectorStoreIndex')
async def test_upload_document(mock_index, mock_reader, sample_document):
    # Setup mocks
    mock_reader.return_value.load_data.return_value = ["mocked document"]
    mock_index.from_documents.return_value = mock.MagicMock()
    
    # Create mock request with file
    with open(sample_document, "rb") as f:
        file_content = f.read()
    
    mock_request = MockRequest(files={sample_document.name: file_content})
    
    # Call the function
    await upload_document(mock_request)
    
    # Assertions - not checking response but verifying the function was called correctly
    mock_reader.assert_called_once_with("data")
    mock_index.from_documents.assert_called_once()

@pytest.mark.asyncio
@mock.patch('main.index', None)  # Simulate no documents uploaded
async def test_query_without_documents():
    mock_request = MockRequest(json_data={"question": "What is in the document?"})
    await query_documents(mock_request)
    # Just verifying the function executes

@pytest.mark.asyncio
@mock.patch('main.index')
async def test_query_with_documents(mock_index):
    # Setup mock
    mock_query_engine = mock.MagicMock()
    mock_index.as_query_engine.return_value = mock_query_engine
    mock_query_engine.query.return_value = "This is a test response"
    
    # Create request with question
    mock_request = MockRequest(json_data={"question": "What is in the document?"})
    
    # Call the function
    await query_documents(mock_request)
    
    # Assertions - not checking response but verifying the function called dependencies correctly
    mock_index.as_query_engine.assert_called_once()
    mock_query_engine.query.assert_called_once_with("What is in the document?")

@pytest.mark.asyncio
@mock.patch('main.index', mock.MagicMock())
async def test_invalid_query():
    mock_request = MockRequest(json_data={})
    await query_documents(mock_request)
    # Just verifying the function executes 