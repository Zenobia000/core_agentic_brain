"""
FastAPI server to bridge Hacker UI frontend with OpenManus backend
"""
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from app.agent.manus import Manus
from app.agent.event_aware_manus import EventAwareManus
from app.events import event_bus, StepEvent, EventPhase
from app.logger import logger
from app.workspace.context_manager import ContextManager
from app.utils.session_manager import SessionManager


# Request/Response models
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    context_type: Optional[str] = "session"


class ChatResponse(BaseModel):
    session_id: str
    response: str
    metadata: Optional[Dict[str, Any]] = {}


class SystemStatus(BaseModel):
    llm_connected: bool
    mcp_servers: int
    workspace_mounted: bool
    active_sessions: int


# Connection Manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.agents: Dict[str, Manus] = {}

    async def connect(self, websocket: WebSocket, session_id: str = None):
        await websocket.accept()

        if not session_id:
            session_id = str(uuid.uuid4())

        self.active_connections[session_id] = websocket
        self.sessions[session_id] = {
            "connected_at": datetime.now().isoformat(),
            "context_manager": ContextManager(context_type="session", context_id=session_id),
            "session_manager": SessionManager()
        }

        # Create agent for this session
        if session_id not in self.agents:
            agent = await EventAwareManus.create()
            self.agents[session_id] = agent

        logger.info(f"WebSocket connected: {session_id}")
        return session_id

    async def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

        # Cleanup agent
        if session_id in self.agents:
            await self.agents[session_id].cleanup()
            del self.agents[session_id]

        if session_id in self.sessions:
            del self.sessions[session_id]

        logger.info(f"WebSocket disconnected: {session_id}")

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        for session_id, websocket in self.active_connections.items():
            if session_id != exclude:
                await websocket.send_json(message)


# Initialize app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Manus Web Server...")
    yield
    # Shutdown
    logger.info("Shutting down Manus Web Server...")
    # Cleanup all agents
    for agent in manager.agents.values():
        await agent.cleanup()


# Create FastAPI app
app = FastAPI(
    title="Manus Web API",
    description="Bridge between Hacker UI and OpenManus",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files - serve Hacker UI if built
ui_path = Path(__file__).parent.parent / "Hacker_UI_Design" / "dist"
if ui_path.exists():
    app.mount("/", StaticFiles(directory=str(ui_path), html=True), name="static")

# Initialize connection manager
manager = ConnectionManager()


@app.get("/api/status")
async def get_status() -> SystemStatus:
    """Get system status"""
    return SystemStatus(
        llm_connected=len(manager.agents) > 0,
        mcp_servers=0,  # TODO: Get actual MCP server count
        workspace_mounted=True,
        active_sessions=len(manager.active_connections)
    )


@app.get("/api/settings")
async def get_settings():
    """Get user settings"""
    return {
        "theme": "matrix",
        "mode": "hacker",
        "shortcuts": {
            "command_palette": "ctrl+p",
            "switch_pane": "ctrl+k",
            "toggle_section": "ctrl+j",
            "goto_error": "ctrl+g"
        }
    }


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Handle chat requests with streaming response"""
    session_id = request.session_id or str(uuid.uuid4())

    # Get or create agent
    if session_id not in manager.agents:
        agent = await EventAwareManus.create()
        manager.agents[session_id] = agent
    else:
        agent = manager.agents[session_id]

    async def generate():
        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"

            # Update task header
            yield f"data: {json.dumps({
                'type': 'task_update',
                'name': request.query[:50],
                'current_phase': 1,
                'total_phases': 3,
                'phase_name': '分析中'
            })}\n\n"

            # Stream thinking updates
            yield f"data: {json.dumps({
                'type': 'thinking_update',
                'summary': '理解問題...',
                'detail': '分析使用者需求'
            })}\n\n"

            # Process with agent
            # Note: This is a simplified version. You'll need to modify Manus.run()
            # to support streaming or create a new streaming method
            response_parts = []

            # Simulate streaming response (replace with actual agent streaming)
            # In real implementation, modify Manus to yield results
            result = await agent.run(request.query)

            # Stream the response token by token
            if result:
                for char in str(result):
                    yield f"data: {json.dumps({'type': 'token', 'token': char})}\n\n"
                    await asyncio.sleep(0.01)  # Simulate typing effect

            # Send completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Error in chat endpoint: {e}")
            yield f"data: {json.dumps({
                'type': 'error',
                'message': str(e)
            })}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    session_id = None

    try:
        # Connect and get session ID
        session_id = await manager.connect(websocket)

        # Send initial connection message
        await manager.send_message(session_id, {
            "type": "connected",
            "payload": {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        })

        # Send initial status
        await manager.send_message(session_id, {
            "type": "context_update",
            "payload": {
                "tokens": [0, 8000],
                "model": "claude-3.5",
                "cost": 0.0,
                "latency": 0.0
            }
        })

        while True:
            # Receive message from client
            data = await websocket.receive_json()
            await handle_websocket_message(session_id, data)

    except WebSocketDisconnect:
        if session_id:
            await manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if session_id:
            await manager.disconnect(session_id)


async def handle_websocket_message(session_id: str, data: dict):
    """Handle incoming WebSocket messages"""
    message_type = data.get("type")
    payload = data.get("payload", {})

    logger.info(f"Received WS message: {message_type} from {session_id}")

    if message_type == "init":
        # Initialize session
        await manager.send_message(session_id, {
            "type": "init_complete",
            "payload": {
                "mode": payload.get("mode", "hacker"),
                "features": ["chat", "tools", "thinking", "export"],
                "session_id": session_id
            }
        })

    elif message_type == "chat":
        # Process chat message
        query = payload.get("query")
        if not query:
            return

        agent = manager.agents.get(session_id)
        if not agent:
            agent = await EventAwareManus.create()
            manager.agents[session_id] = agent

        # Add event handler to send events via WebSocket
        async def send_event(event_data):
            """Forward events from agent to WebSocket"""
            if isinstance(event_data, dict):
                await manager.send_message(session_id, event_data)
            elif isinstance(event_data, StepEvent):
                await manager.send_message(session_id, event_data.to_ws_message())

        # Register the handler
        agent.add_event_handler(send_event)

        # Send initial user message
        await manager.send_message(session_id, {
            "type": "conversation",
            "payload": {
                "role": "user",
                "content": query
            }
        })

        try:
            # Process with agent - events will be emitted automatically
            result = await agent.run(query)

            # Get all events from the run
            events = agent.event_bus.get_history()
            artifacts = agent.event_bus.get_artifacts()
            final_answer = agent.event_bus.get_final_answer()

            # Send final response if not already sent
            if final_answer:
                await manager.send_message(session_id, {
                    "type": "conversation",
                    "payload": {
                        "role": "assistant",
                        "content": final_answer
                    }
                })

            # Send completion feedback
            await manager.send_message(session_id, {
                "type": "feedback",
                "payload": {
                    "type": "success",
                    "data": {
                        "action": "query processed",
                        "details": f"completed in {datetime.now().isoformat()}",
                        "total_steps": len(events),
                        "artifacts_count": len(artifacts)
                    }
                }
            })

        except Exception as e:
            logger.error(f"Error processing chat: {e}")
            await manager.send_message(session_id, {
                "type": "feedback",
                "payload": {
                    "type": "error",
                    "data": {
                        "reason": str(e),
                        "nextAction": "please try again"
                    }
                }
            })

        finally:
            # Clear waiting status
            await manager.send_message(session_id, {
                "type": "task_update",
                "payload": {
                    "waiting_for": None
                }
            })

    elif message_type == "command":
        # Handle commands
        command = payload.get("command")
        await handle_command(session_id, command)

    elif message_type == "export":
        # Handle export request
        format_type = payload.get("format", "md")
        content = await export_conversation(session_id, format_type)
        await manager.send_message(session_id, {
            "type": "export_complete",
            "payload": {
                "format": format_type,
                "content": content
            }
        })


async def handle_command(session_id: str, command: str):
    """Handle slash commands"""
    if not command:
        return

    parts = command.split()
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    if cmd == "/help":
        help_text = """
Available commands:
/help - Show this help message
/clear - Clear conversation
/mode [minimal|standard|hacker] - Change UI mode
/theme [matrix|minimal] - Change theme
/export [md|json] - Export conversation
/status - Show system status
        """
        await manager.send_message(session_id, {
            "type": "conversation",
            "payload": {
                "role": "system",
                "content": help_text
            }
        })

    elif cmd == "/clear":
        await manager.send_message(session_id, {
            "type": "clear_conversation",
            "payload": {}
        })

    elif cmd == "/status":
        status = await get_status()
        await manager.send_message(session_id, {
            "type": "conversation",
            "payload": {
                "role": "system",
                "content": f"System Status:\n- LLM Connected: {status.llm_connected}\n- Active Sessions: {status.active_sessions}\n- Workspace: {status.workspace_mounted}"
            }
        })

    else:
        await manager.send_message(session_id, {
            "type": "conversation",
            "payload": {
                "role": "system",
                "content": f"Unknown command: {cmd}"
            }
        })


async def export_conversation(session_id: str, format_type: str) -> str:
    """Export conversation history"""
    # TODO: Implement actual export from session history
    if format_type == "json":
        return json.dumps({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "messages": []
        })
    else:  # markdown
        return f"# Conversation Export\n\nSession: {session_id}\nDate: {datetime.now().isoformat()}\n\n---\n\n"


@app.get("/api/sessions")
async def get_sessions():
    """Get list of active sessions"""
    sessions = []
    for session_id, session_data in manager.sessions.items():
        sessions.append({
            "id": session_id,
            "connected_at": session_data.get("connected_at"),
            "active": session_id in manager.active_connections
        })
    return sessions


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session"""
    if session_id in manager.sessions:
        await manager.disconnect(session_id)
        return {"status": "success", "message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


if __name__ == "__main__":
    import uvicorn

    # Run server
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )