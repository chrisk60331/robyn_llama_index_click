# Robyn + LlamaIndex Analysis POC

This is a proof of concept application that combines Robyn (a fast Python web framework) with LlamaIndex for document analysis and question answering. It also features a GraphQL API for querying documents.

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
uv run cli.py setup
```

## Running the Application

Start the server:
```bash
uv run cli.py serve
```

The server will start on `http://localhost:8000` by default.

## CLI Usage

The application provides a CLI interface for easy interaction:

```bash
# Start the server
uv run cli.py serve [--port PORT] [--host HOST] [--dev]

# Upload a document
uv run cli.py upload path/to/your/document.pdf

# Query the documents
uv run cli.py query "What are the main points in the document?"

# Setup the environment
uv run cli.py setup
```

## API Endpoints

- `POST /upload`: Upload a document for analysis
- `POST /query`: Ask questions about the uploaded documents
- `GET /health`: Health check endpoint

## GraphQL Interface

The application includes a GraphQL API for more flexible document querying:

- GraphQL IDE: `http://localhost:8000/graphql`
- GraphQL Endpoint: `POST http://localhost:8000/graphql`

### Example GraphQL Queries

```graphql
# Check system health
{
  health {
    status
  }
}

# List all uploaded documents
{
  documents {
    name
    size
  }
}

# Query documents
{
  query(question: "What are the main points in the document?") {
    response
  }
}
```

## Development

### Running Tests

```bash
uv run -m pytest
```

### Running Test Coverage

```bash
# Run tests with coverage
uv run -m pytest --cov=. --cov-report=term-missing

# Generate HTML coverage report
uv run -m pytest --cov=. --cov-report=html
# Report will be available in htmlcov/index.html
```

### Project Structure

```
.
├── cli.py              # CLI interface
├── main.py             # Main application
├── schema.py           # GraphQL schema definition
├── pyproject.toml      # Project configuration and dependencies
├── tests/              # Test directory
│   ├── test_main.py    # Application tests
│   ├── test_cli.py     # CLI tests
│   └── test_graphql.py # GraphQL tests
└── data/               # Directory for uploaded documents
```

## Example Usage

1. Upload a document:
```bash
uv run cli.py upload path/to/your/document.pdf
```

2. Query the documents:
```bash
uv run cli.py query "What are the main points in the document?"
```

3. Access the GraphQL interface at `http://localhost:8000/graphql` in your browser 