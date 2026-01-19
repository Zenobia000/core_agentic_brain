"""
Tool Gateway - 工具網關
======================

所有外部工具的統一介面。
- Tool Contract: 標準化工具合約
- Tool Adapter: 適配不同來源 (MCP/HTTP/gRPC)
"""

from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ToolProtocol(str, Enum):
    LOCAL = "local"
    MCP = "mcp"
    HTTP = "http"
    GRPC = "grpc"


class ToolContract(BaseModel):
    """工具合約"""
    name: str
    description: str = ""
    protocol: ToolProtocol = ToolProtocol.LOCAL
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = 30.0
    
    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in input_data:
                return False, f"Missing required field: {field}"
        return True, None


class ToolResult(BaseModel):
    """工具執行結果"""
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class ToolAdapter(ABC):
    """工具適配器基類"""
    protocol: ToolProtocol
    
    @abstractmethod
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[ToolContract]:
        pass


class LocalToolAdapter(ToolAdapter):
    """本地工具適配器"""
    protocol = ToolProtocol.LOCAL
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.contracts: Dict[str, ToolContract] = {}
    
    def register(self, name: str, func: Callable, contract: Optional[ToolContract] = None) -> None:
        self.tools[name] = func
        self.contracts[name] = contract or ToolContract(name=name, description=func.__doc__ or "")
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        if tool_name not in self.tools:
            return ToolResult(success=False, error=f"Tool not found: {tool_name}")
        
        start = time.time()
        try:
            func = self.tools[tool_name]
            import asyncio
            result = await func(**arguments) if asyncio.iscoroutinefunction(func) else func(**arguments)
            return ToolResult(success=True, data=result, execution_time_ms=(time.time() - start) * 1000)
        except Exception as e:
            return ToolResult(success=False, error=str(e), execution_time_ms=(time.time() - start) * 1000)
    
    async def list_tools(self) -> List[ToolContract]:
        return list(self.contracts.values())


class HTTPToolAdapter(ToolAdapter):
    """HTTP 工具適配器"""
    protocol = ToolProtocol.HTTP
    
    def __init__(self):
        self.endpoints: Dict[str, Dict[str, Any]] = {}
        self.contracts: Dict[str, ToolContract] = {}
    
    def register_endpoint(self, name: str, url: str, method: str = "POST") -> None:
        self.endpoints[name] = {"url": url, "method": method}
        self.contracts[name] = ToolContract(name=name, protocol=ToolProtocol.HTTP)
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        if tool_name not in self.endpoints:
            return ToolResult(success=False, error=f"Endpoint not found: {tool_name}")
        
        endpoint = self.endpoints[tool_name]
        start = time.time()
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                if endpoint["method"].upper() == "GET":
                    response = await client.get(endpoint["url"], params=arguments)
                else:
                    response = await client.post(endpoint["url"], json=arguments)
                response.raise_for_status()
                return ToolResult(success=True, data=response.json(), execution_time_ms=(time.time() - start) * 1000)
        except Exception as e:
            return ToolResult(success=False, error=str(e), execution_time_ms=(time.time() - start) * 1000)
    
    async def list_tools(self) -> List[ToolContract]:
        return list(self.contracts.values())


class ToolGateway(BaseModel):
    """工具網關 - 統一管理所有工具"""
    
    adapters: Dict[str, ToolAdapter] = Field(default_factory=dict)
    tool_to_adapter: Dict[str, str] = Field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True
    
    def register_adapter(self, name: str, adapter: ToolAdapter) -> None:
        self.adapters[name] = adapter
    
    def register_local_tool(self, name: str, func: Callable) -> None:
        if "local" not in self.adapters:
            self.adapters["local"] = LocalToolAdapter()
        self.adapters["local"].register(name, func)
        self.tool_to_adapter[name] = "local"
    
    async def list_all_tools(self) -> List[ToolContract]:
        all_tools = []
        for adapter in self.adapters.values():
            tools = await adapter.list_tools()
            all_tools.extend(tools)
        return all_tools
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        adapter_name = self.tool_to_adapter.get(tool_name)
        
        if not adapter_name:
            for name, adapter in self.adapters.items():
                tools = await adapter.list_tools()
                if any(t.name == tool_name for t in tools):
                    adapter_name = name
                    self.tool_to_adapter[tool_name] = name
                    break
        
        if not adapter_name or adapter_name not in self.adapters:
            return ToolResult(success=False, error=f"No adapter found for tool: {tool_name}")
        
        result = await self.adapters[adapter_name].execute(tool_name, arguments)
        
        self.execution_history.append({
            "tool_name": tool_name,
            "success": result.success,
            "timestamp": datetime.now().isoformat(),
        })
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        total = len(self.execution_history)
        success = len([h for h in self.execution_history if h["success"]])
        return {
            "total_executions": total,
            "success_rate": success / total if total > 0 else 0,
        }


__all__ = [
    "ToolProtocol", "ToolContract", "ToolResult",
    "ToolAdapter", "LocalToolAdapter", "HTTPToolAdapter",
    "ToolGateway",
]
