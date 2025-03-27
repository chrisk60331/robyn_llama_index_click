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
from multipart import MultipartParser

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

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments for standalone usage
    parser = argparse.ArgumentParser(description='Robyn LlamaIndex API server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to run the server on')
    args = parser.parse_args()
    
    app.start(port=args.port, host=args.host) 