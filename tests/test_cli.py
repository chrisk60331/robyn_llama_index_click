import pytest
from unittest import mock
from pathlib import Path
from click.testing import CliRunner
import cli

@pytest.fixture
def runner():
    """CLI test runner"""
    return CliRunner()


@pytest.fixture
def mock_httpx():
    """Mock httpx for testing upload and query"""
    with mock.patch('httpx.post') as mock_post:
        # Setup mock response
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing upload"""
    file_content = "Test document content"
    temp_file = tmp_path / "test_doc.txt"
    temp_file.write_text(file_content)
    return str(temp_file)


def test_cli_help(runner):
    """Test the CLI help output"""
    result = runner.invoke(cli.cli, ['--help'])
    assert result.exit_code == 0
    assert "Robyn + LlamaIndex Analysis POC CLI" in result.output
    assert "serve" in result.output
    assert "upload" in result.output
    assert "query" in result.output
    assert "setup" in result.output


def test_serve_normal_mode(runner):
    """Test the serve command in normal mode"""
    mock_app = mock.MagicMock()
    
    # Mock the import of app from main
    with mock.patch.dict('sys.modules', {'main': mock.MagicMock(app=mock_app)}):
        result = runner.invoke(cli.cli, ['serve'])
        assert result.exit_code == 0
        mock_app.start.assert_called_once_with(port=8000, host='127.0.0.1')


def test_serve_dev_mode(runner):
    """Test the serve command in dev mode"""
    import sys
    with mock.patch('subprocess.run') as mock_run:
        result = runner.invoke(cli.cli, ['serve', '--dev'])
        assert result.exit_code == 0
        mock_run.assert_called_once_with([
            sys.executable,
            "-m", "robyn",
            "main.py",
            "--dev",
            "--port", "8000",
            "--host", "127.0.0.1"
        ])


def test_upload_command(runner, mock_httpx, temp_file):
    """Test the upload command"""
    result = runner.invoke(cli.cli, ['upload', temp_file])
    assert result.exit_code == 0
    
    # Check that httpx.post was called with the right URL and files
    mock_httpx.assert_called_once()
    args, kwargs = mock_httpx.call_args
    assert args[0] == 'http://localhost:8000/upload'
    assert 'files' in kwargs
    
    # Verify response output
    assert "status" in result.output
    assert "success" in result.output


def test_query_command(runner, mock_httpx):
    """Test the query command"""
    test_question = "What is in the document?"
    result = runner.invoke(cli.cli, ['query', test_question])
    assert result.exit_code == 0
    
    # Check that httpx.post was called with the right URL and json
    mock_httpx.assert_called_once_with(
        'http://localhost:8000/query',
        json={'question': test_question}
    )
    
    # Verify response output
    assert "status" in result.output
    assert "success" in result.output


def test_setup_command(runner):
    """Test the setup command"""
    with mock.patch('pathlib.Path.mkdir') as mock_mkdir:
        with mock.patch('pathlib.Path.exists') as mock_exists:
            with mock.patch('pathlib.Path.write_text') as mock_write_text:
                mock_exists.return_value = False
                
                result = runner.invoke(cli.cli, ['setup'])
                
                assert result.exit_code == 0
                mock_mkdir.assert_called_once_with(exist_ok=True)
                mock_write_text.assert_called_once_with('OPENAI_API_KEY=your_api_key_here\n')
                assert "Created .env file" in result.output
                assert "Setup complete!" in result.output


def test_setup_command_env_exists(runner):
    """Test the setup command when .env already exists"""
    with mock.patch('pathlib.Path.mkdir') as mock_mkdir:
        with mock.patch('pathlib.Path.exists') as mock_exists:
            with mock.patch('pathlib.Path.write_text') as mock_write_text:
                mock_exists.return_value = True
                
                result = runner.invoke(cli.cli, ['setup'])
                
                assert result.exit_code == 0
                mock_mkdir.assert_called_once_with(exist_ok=True)
                mock_write_text.assert_not_called()
                assert "Setup complete!" in result.output 