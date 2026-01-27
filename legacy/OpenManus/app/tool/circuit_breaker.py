"""
Circuit Breaker pattern implementation for tool failure management
防止工具重複失敗的熔斷器機制
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # 正常狀態
    OPEN = "open"      # 熔斷狀態
    HALF_OPEN = "half_open"  # 半開狀態


@dataclass
class CircuitBreaker:
    """工具熔斷器，防止重複失敗"""

    failure_threshold: int = 3  # 失敗次數閾值
    recovery_timeout: int = 30 * 60  # 恢復超時（秒）
    half_open_max_calls: int = 1  # 半開狀態最大調用次數

    # 內部狀態
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    failure_count: int = field(default=0, init=False)
    last_failure_time: Optional[float] = field(default=None, init=False)
    half_open_calls: int = field(default=0, init=False)
    consecutive_successes: int = field(default=0, init=False)

    def record_success(self):
        """記錄成功調用"""
        self.consecutive_successes += 1

        if self.state == CircuitState.HALF_OPEN:
            # 半開狀態下成功，恢復到關閉狀態
            logger.info("Circuit breaker recovering from half-open to closed")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            # 重置失敗計數
            if self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self, error: str) -> bool:
        """記錄失敗調用，返回是否觸發熔斷"""
        self.consecutive_successes = 0
        self.failure_count += 1
        self.last_failure_time = time.time()

        # 檢查是否需要熔斷
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            self.state = CircuitState.OPEN
            return True

        # 半開狀態下失敗，立即熔斷
        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker re-opening from half-open state")
            self.state = CircuitState.OPEN
            return True

        return False

    def should_allow_request(self) -> bool:
        """檢查是否允許請求"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # 檢查是否可以進入半開狀態
            if self.last_failure_time and \
               time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info("Circuit breaker attempting recovery to half-open state")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # 半開狀態下限制調用次數
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False

        return False

    def get_state_info(self) -> Dict:
        """獲取熔斷器狀態信息"""
        time_until_recovery = None
        if self.state == CircuitState.OPEN and self.last_failure_time:
            time_until_recovery = max(
                0,
                self.recovery_timeout - (time.time() - self.last_failure_time)
            )

        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "consecutive_successes": self.consecutive_successes,
            "last_failure_time": self.last_failure_time,
            "time_until_recovery": time_until_recovery
        }


class ToolCircuitBreakerManager:
    """工具熔斷器管理器"""

    # 已知的初始化錯誤模式
    INIT_ERROR_PATTERNS = [
        "Browser.__init__() got an unexpected keyword argument",
        "Playwright not installed",
        "BrowserType.launch",
        "Browser initialization failed",
        "Cannot launch browser",
        "Browser config error"
    ]

    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, tool_name: str) -> CircuitBreaker:
        """獲取指定工具的熔斷器"""
        if tool_name not in self.breakers:
            self.breakers[tool_name] = CircuitBreaker()
        return self.breakers[tool_name]

    def should_use_tool(self, tool_name: str) -> bool:
        """檢查是否可以使用工具"""
        breaker = self.get_breaker(tool_name)
        allowed = breaker.should_allow_request()

        if not allowed:
            logger.debug(f"Tool {tool_name} blocked by circuit breaker: {breaker.get_state_info()}")

        return allowed

    def record_tool_success(self, tool_name: str):
        """記錄工具調用成功"""
        breaker = self.get_breaker(tool_name)
        breaker.record_success()
        logger.debug(f"Tool {tool_name} succeeded, state: {breaker.state.value}")

    def record_tool_failure(self, tool_name: str, error: str) -> bool:
        """記錄工具調用失敗，返回是否觸發熔斷"""
        breaker = self.get_breaker(tool_name)

        # 檢查是否是初始化錯誤（更嚴重）
        is_init_error = any(pattern in error for pattern in self.INIT_ERROR_PATTERNS)

        if is_init_error:
            # 初始化錯誤直接熔斷更長時間
            logger.error(f"Tool {tool_name} initialization error detected: {error[:200]}")
            breaker.failure_threshold = 1  # 一次失敗就熔斷
            breaker.recovery_timeout = 60 * 60  # 1小時後才重試
        else:
            # 普通錯誤使用默認設置
            logger.warning(f"Tool {tool_name} failed: {error[:200]}")

        is_opened = breaker.record_failure(error)

        if is_opened:
            logger.error(
                f"Circuit breaker OPENED for tool {tool_name}. "
                f"Will retry after {breaker.recovery_timeout} seconds"
            )

        return is_opened

    def get_status(self) -> Dict[str, Dict]:
        """獲取所有熔斷器狀態"""
        return {
            tool: breaker.get_state_info()
            for tool, breaker in self.breakers.items()
        }

    def reset_tool(self, tool_name: str):
        """手動重置工具熔斷器（用於測試或強制恢復）"""
        if tool_name in self.breakers:
            self.breakers[tool_name] = CircuitBreaker()
            logger.info(f"Circuit breaker for {tool_name} has been reset")

    def get_blocked_tools(self) -> list:
        """獲取當前被熔斷的工具列表"""
        return [
            tool for tool, breaker in self.breakers.items()
            if breaker.state == CircuitState.OPEN
        ]


# 創建全局實例
circuit_breaker_manager = ToolCircuitBreakerManager()