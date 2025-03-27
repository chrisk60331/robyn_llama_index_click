import click
import uvicorn
from pathlib import Path
import os
from dotenv import load_dotenv

@click.group()
def cli():
    """Robyn + LlamaIndex Analysis POC CLI"""
    pass

@cli.command()
@click.option('--port', default=8000, help='Port to run the server on')
@click.option('--host', default='127.0.0.1', help='Host to run the server on')
@click.option('--dev', is_flag=True, default=False, help='Enable development mode with hot reloading')
def serve(port: int, host: str, dev: bool):
    """Start the Robyn server"""
    if dev:
        import subprocess
        import sys
        
        # Use the Robyn CLI directly with the --dev flag
        click.echo(f"Starting development server with hot reloading on {host}:{port}")
        subprocess.run([
            sys.executable, 
            "-m", "robyn", 
            "main.py", 
            "--dev",
            "--port", str(port),
            "--host", host
        ])
    else:
        from main import app
        app.start(port=port, host=host)

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def upload(file_path: str):
    """Upload a document for analysis"""
    import httpx
    from pathlib import Path
    
    file_name = Path(file_path).name
    with open(file_path, 'rb') as f:
        files = {'file': (file_name, f, 'application/pdf')}
        response = httpx.post('http://localhost:8000/upload', files=files)
        click.echo(response.json())

@cli.command()
@click.argument('question')
def query(question: str):
    """Query the documents"""
    import httpx
    
    response = httpx.post(
        'http://localhost:8000/query',
        json={'question': question}
    )
    click.echo(response.json())

@cli.command()
def setup():
    """Setup the project environment"""
    # Create data directory if it doesn't exist
    Path('data').mkdir(exist_ok=True)
    
    # Create .env file if it doesn't exist
    if not Path('.env').exists():
        Path('.env').write_text('OPENAI_API_KEY=your_api_key_here\n')
        click.echo("Created .env file. Please update with your OpenAI API key.")
    
    click.echo("Setup complete!")

if __name__ == '__main__':
    cli() 