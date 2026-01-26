"""
Sandbox Service - 安全沙箱執行服務
支援 Bash 和 Python 程式執行
"""

from typing import List, Dict, Any, Optional
import asyncio
import tempfile
import os
import logging

from core.protocols import MCPServiceProtocol

logger = logging.getLogger(__name__)


class SandboxService(MCPServiceProtocol):
    """
    沙箱執行服務
    
    功能:
    - execute_bash: 執行 Bash 命令
    - execute_python: 執行 Python 程式
    - file_read: 讀取檔案
    - file_write: 寫入檔案
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._service_id = "sandbox"
        self._capabilities = [
            "execute_bash",
            "execute_python",
            "file_read",
            "file_write"
        ]
        
        # 配置
        self.docker_enabled = self.config.get("docker_enabled", False)
        self.timeout = self.config.get("timeout", 30)
        self.memory_limit = self.config.get("memory_limit", "512m")
        self.working_dir = self.config.get("working_dir", "/tmp/sandbox")
        
        # Docker 客戶端
        self.docker_client = None
        
        self._initialized = False
    
    @property
    def service_id(self) -> str:
        return self._service_id
    
    @property
    def capabilities(self) -> List[str]:
        return self._capabilities
    
    async def initialize(self) -> None:
        """初始化服務"""
        # 建立工作目錄
        os.makedirs(self.working_dir, exist_ok=True)
        
        # 初始化 Docker (如果啟用)
        if self.docker_enabled:
            try:
                import docker
                self.docker_client = docker.from_env()
                logger.info("Docker client initialized")
            except Exception as e:
                logger.warning(f"Docker not available: {e}")
                self.docker_enabled = False
        
        self._initialized = True
        logger.info(f"✅ {self.service_id} initialized")
    
    async def execute(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """執行方法"""
        if not self._initialized:
            await self.initialize()
        
        if method == "execute_bash":
            return await self._execute_bash(
                command=params.get("command", ""),
                timeout=params.get("timeout", self.timeout)
            )
        
        elif method == "execute_python":
            return await self._execute_python(
                code=params.get("code"),
                file=params.get("file"),
                timeout=params.get("timeout", self.timeout)
            )
        
        elif method == "file_read":
            return await self._file_read(params.get("path", ""))
        
        elif method == "file_write":
            return await self._file_write(
                path=params.get("path", ""),
                content=params.get("content", "")
            )
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    async def health_check(self) -> bool:
        """健康檢查"""
        return True
    
    async def shutdown(self) -> None:
        """關閉服務"""
        logger.info(f"{self.service_id} shutdown")
    
    # ========== 內部方法 ==========
    
    async def _execute_bash(
        self, 
        command: str, 
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        執行 Bash 命令
        
        Args:
            command: 要執行的命令
            timeout: 超時時間
            
        Returns:
            執行結果
        """
        if self.docker_enabled:
            return await self._execute_in_docker(
                image="alpine:latest",
                command=["/bin/sh", "-c", command],
                timeout=timeout
            )
        
        # 本地執行 (有安全風險，僅限開發環境)
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            
            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "exit_code": proc.returncode,
                "success": proc.returncode == 0
            }
            
        except asyncio.TimeoutError:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "exit_code": -1,
                "success": False
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "success": False
            }
    
    async def _execute_python(
        self,
        code: Optional[str] = None,
        file: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        執行 Python 程式
        
        Args:
            code: Python 程式碼
            file: Python 檔案路徑
            timeout: 超時時間
            
        Returns:
            執行結果
        """
        if not code and not file:
            return {
                "error": "Must provide either 'code' or 'file'",
                "success": False
            }
        
        # 如果提供程式碼，寫入臨時檔案
        temp_file = None
        if code:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                dir=self.working_dir,
                delete=False
            )
            temp_file.write(code)
            temp_file.close()
            file = temp_file.name
        
        try:
            result = await self._execute_bash(
                f"python3 {file}",
                timeout=timeout
            )
            return result
            
        finally:
            # 清理臨時檔案
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    async def _execute_in_docker(
        self,
        image: str,
        command: List[str],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """在 Docker 容器中執行"""
        try:
            container = self.docker_client.containers.run(
                image,
                command,
                detach=True,
                mem_limit=self.memory_limit,
                cpu_quota=50000,
                network_mode="none",
                remove=False
            )
            
            try:
                result = container.wait(timeout=timeout)
                logs = container.logs()
                
                return {
                    "stdout": logs.decode("utf-8", errors="replace"),
                    "stderr": "",
                    "exit_code": result.get("StatusCode", -1),
                    "success": result.get("StatusCode", -1) == 0
                }
            finally:
                container.remove(force=True)
                
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "success": False
            }
    
    async def _file_read(self, path: str) -> Dict[str, Any]:
        """讀取檔案"""
        try:
            # 安全檢查：只允許讀取工作目錄內的檔案
            full_path = os.path.join(self.working_dir, path)
            if not full_path.startswith(self.working_dir):
                return {"error": "Access denied", "success": False}
            
            with open(full_path, 'r') as f:
                content = f.read()
            
            return {
                "content": content,
                "path": path,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _file_write(self, path: str, content: str) -> Dict[str, Any]:
        """寫入檔案"""
        try:
            # 安全檢查
            full_path = os.path.join(self.working_dir, path)
            if not full_path.startswith(self.working_dir):
                return {"error": "Access denied", "success": False}
            
            # 建立目錄
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
            
            return {
                "path": path,
                "bytes_written": len(content),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
