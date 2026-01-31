# web/server.py
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# A simple in-memory kernel to avoid re-initializing for every connection
# In a real app, you'd have a more robust way to manage kernel state.
kernel_instance = None

app = FastAPI()

# Mount the 'static' directory to serve files like index.html, style.css, app.js
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
async def read_root():
    """Serves the main index.html file."""
    return {"message": "Server is running. Navigate to /static/index.html to use the web UI."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The WebSocket endpoint for kernel-based agent interaction."""
    global kernel_instance
    await websocket.accept()

    # Import Kernel here to avoid circular dependencies and slow startup
    from core.kernel import Kernel

    # Initialize the kernel if it's not already
    if kernel_instance is None:
        try:
            kernel_instance = Kernel()
            print("Kernel initialized for WebSocket.")
        except Exception as e:
            await websocket.send_json({"type": "error", "content": f"Failed to initialize kernel: {e}"})
            await websocket.close()
            return

    try:
        while True:
            # Wait for a message from the client (the user's query)
            user_query = await websocket.receive_text()

            await websocket.send_json({"type": "thought", "content": f"Processing: {user_query}"})

            # Execute through kernel (OKR-based orchestration)
            result = await kernel_instance.execute(user_query)

            if result.success:
                await websocket.send_json({"type": "final", "content": result.response})
            else:
                await websocket.send_json({"type": "error", "content": result.error or "Execution failed"})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        try:
            await websocket.send_json({"type": "error", "content": error_message})
        except RuntimeError:
            pass # Websocket might be closed already

if __name__ == "__main__":
    print("Starting web server...")
    print("Navigate to http://127.0.0.1:8000/static/index.html")
    config = {}
    try:
        from core.config import get_config
        config = get_config().get("server", {})
    except (ImportError, FileNotFoundError):
        print("Could not load config, using default server settings.")
        
    uvicorn.run(
        "web.server:app",
        host=config.get("host", "127.0.0.1"),
        port=config.get("port", 8000),
        reload=True # Use reload for development
    )
