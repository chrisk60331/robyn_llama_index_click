# Robyn + LlamaIndex Analysis POC

This is a proof of concept application that combines Robyn (a fast Python web framework) with LlamaIndex for document analysis and question answering.

## Setup

1. Install uv (recommended package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. Create a `.env` file with your OpenAI API key:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

4. Run the setup command:
```bash
python -m cli setup
```

## Running the Application

Start the server:
```bash
python -m cli serve
```

The server will start on `http://localhost:8000` by default.

## CLI Usage

The application provides a CLI interface for easy interaction:

```bash
# Start the server
python -m cli serve [--port PORT] [--host HOST]

# Upload a document
python -m cli upload path/to/your/document.pdf

# Query the documents
python -m cli query "What are the main points in the document?"

# Setup the environment
python -m cli setup
```

## API Endpoints

- `POST /upload`: Upload a document for analysis
- `POST /query`: Ask questions about the uploaded documents
- `GET /health`: Health check endpoint

## Development

### Running Tests

```bash
pytest
```

### Project Structure

```
.
├── cli.py              # CLI interface
├── main.py            # Main application
├── pyproject.toml     # Project configuration and dependencies
├── tests/             # Test directory
│   └── test_main.py   # Application tests
└── data/              # Directory for uploaded documents
```

## Example Usage

1. Upload a document:
```bash
python -m cli upload path/to/your/document.pdf
```

2. Query the documents:
```bash
python -m cli query "What are the main points in the document?"
``` 