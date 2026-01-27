# web/server.py
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# A simple in-memory "runner" to avoid re-initializing the agent for every connection
# In a real app, you'd have a more robust way to manage agent state.
agent_instance = None

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
    """The WebSocket endpoint for agent interaction."""
    global agent_instance
    await websocket.accept()
    
    # Import Agent here to avoid circular dependencies and slow startup
    from core.agent import Agent

    # Initialize the agent if it's not already
    if agent_instance is None:
        try:
            agent_instance = Agent()
            print("Agent initialized for WebSocket.")
        except Exception as e:
            await websocket.send_json({"type": "error", "content": f"Failed to initialize agent: {e}"})
            await websocket.close()
            return
            
    try:
        while True:
            # Wait for a message from the client (the user's query)
            user_query = await websocket.receive_text()
            
            # A simple way to stream thoughts and actions back to the client
            # We override the print function within the agent's scope for this
            async def stream_to_client(*args, **kwargs):
                content = " ".join(map(str, args))
                await websocket.send_json({"type": "thought", "content": content})

            # You can monkey-patch the print function in the agent's dependencies
            # This is a bit of a hack for a simple example. A better way would be
            # to pass a callback function into the agent's run method.
            # For this example, we'll just run the agent and send the final result.
            
            await websocket.send_json({"type": "thought", "content": f"Agent starting task: {user_query}"})
            
            final_response = agent_instance.run(user_query)
            
            await websocket.send_json({"type": "final", "content": final_response})

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
