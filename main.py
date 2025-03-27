import os
from typing import Dict, Any
from dotenv import load_dotenv
from robyn import Robyn, Request, Response
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
import traceback
import io
import python_multipart
from python_multipart import MultipartParser
import json

# Import GraphQL dependencies
import strawberry
# Remove the missing import for graphiql
# import strawberry.utils.graphiql
from schema import schema, index as schema_index

# Load environment variables
load_dotenv()

# Initialize Robyn app
app = Robyn(__file__)

# Initialize LlamaIndex components
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
Settings.llm = llm
Settings.node_parser = SimpleNodeParser()

# Global index for storing document embeddings
index = None

@app.get("/health")
async def health_check(request: Request) -> Response:
    """Health check endpoint."""
    return {"status_code": 200, "body": "OK", "type": "text"}

@app.post("/upload")
async def upload_document(request: Request) -> Response:
    """Upload a document for analysis."""
    try:
        uploaded_file = request.files
        if not uploaded_file:
            return {"status_code": 400, "body": "No file uploaded", "type": "text"}
        
        filename = list(uploaded_file.keys())[0]
        
        file_content = uploaded_file[filename]
        print(file_content)
        save_path = os.path.join("data", filename)

        # Save the file
        with open(save_path, "wb") as f:
            f.write(file_content)

        # Create or update the index
        global index
        documents = SimpleDirectoryReader("data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        
        # Update the schema's index reference
        global schema_index
        schema_index = index

        return {
            "status_code": 200,
            "body": {"message": f"Document {filename} uploaded and indexed successfully"},
            "type": "json"
        }
    except Exception as e:
        traceback.print_exc()
        return {"status_code": 500, "body": str(e), "type": "text"}

@app.post("/query")
async def query_documents(request: Request) -> Response:
    """Query the documents using LlamaIndex."""
    try:
        if index is None:
            return {
                "status_code": 400,
                "body": "No documents have been uploaded yet. Please upload a document first.",
                "type": "text"
            }

        # Parse the request body
        body = request.json()
        if not body or "question" not in body:
            return {"status_code": 400, "body": "No question provided", "type": "text"}

        # Create query engine and get response
        query_engine = index.as_query_engine()
        response = query_engine.query(body["question"])

        return {
            "status_code": 200,
            "body": {"response": str(response)},
            "type": "json"
        }
    except Exception as e:
        return {"status_code": 500, "body": str(e), "type": "text"}

# GraphQL endpoints
@app.get("/graphql", const=True)
async def graphql_ide() -> Response:
    """GraphQL IDE endpoint."""
    # Replace the use of strawberry.utils.graphiql
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GraphiQL</title>
        <style>
            body {
                height: 100%;
                margin: 0;
                width: 100%;
                overflow: hidden;
            }
            #graphiql {
                height: 100vh;
            }
        </style>
        <link rel="stylesheet" href="https://unpkg.com/graphiql/graphiql.min.css" />
    </head>
    <body>
        <div id="graphiql"></div>
        <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
        <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
        <script src="https://unpkg.com/graphiql/graphiql.min.js"></script>
        <script>
            const fetcher = GraphiQL.createFetcher({
                url: '/graphql',
            });
            ReactDOM.render(
                React.createElement(GraphiQL, { fetcher }),
                document.getElementById('graphiql'),
            );
        </script>
    </body>
    </html>
    """
    return {"status_code": 200, "body": html, "type": "html"}

@app.post("/graphql")
async def graphql_endpoint(request: Request) -> Response:
    """GraphQL query endpoint."""
    try:
        body = request.json()
        query = body.get("query")
        variables = body.get("variables")
        context_value = {"request": request}
        root_value = body.get("root_value")
        operation_name = body.get("operation_name")

        data = await schema.execute(
            query,
            variables,
            context_value,
            root_value,
            operation_name,
        )

        # Convert GraphQLError objects to dictionaries to make them serializable
        errors = None
        if data.errors:
            errors = [
                {
                    "message": str(error),
                    "locations": [{"line": loc.line, "column": loc.column} for loc in error.locations] if hasattr(error, "locations") else None,
                    "path": error.path if hasattr(error, "path") else None,
                }
                for error in data.errors
            ]

        response_data = {
            "data": data.data,
            **({"errors": errors} if errors else {}),
            **({"extensions": data.extensions} if data.extensions else {})
        }

        # Use Robyn's dictionary return format instead of Response object
        return {
            "status_code": 200, 
            "body": response_data, 
            "type": "json"
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "status_code": 500, 
            "body": {"error": str(e)}, 
            "type": "json"
        }

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments for standalone usage
    parser = argparse.ArgumentParser(description='Robyn LlamaIndex API server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to run the server on')
    args = parser.parse_args()
    
    app.start(port=args.port, host=args.host) 