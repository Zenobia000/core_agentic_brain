"""極簡 Logger - Linus 會寫的版本 (<70 行)"""

import os
import sys
import time
import json
from pathlib import Path

# 配置 - 直接用環境變數，不要廢話
HUMAN_MODE = os.getenv("LOG_HUMAN", "true").lower() == "true"
DEBUG_MODE = os.getenv("LOG_DEBUG", "false").lower() == "true"
LOG_DIR = Path(os.getenv("LOG_DIR", "workspace/logs"))

# 確保目錄存在
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 當前 trace_id (全局狀態就全局狀態，不要裝)
_trace_id = None


def set_trace(trace_id: str):
    """設置 trace_id"""
    global _trace_id
    _trace_id = trace_id[:8] if len(trace_id) > 8 else trace_id


def log(event: str, **data):
    """記錄事件 - 就這麼簡單

    Args:
        event: 事件名稱 (task.start, llm.request 等)
        **data: 任何你想記的數據
    """
    # 基本欄位
    entry = {
        'ts': time.strftime('%H:%M:%S'),
        'event': event,
        'trace': _trace_id,
        **data
    }

    # Human 輸出 - 一行搞定
    if HUMAN_MODE:
        summary = data.get('summary', '')
        duration = f"({data.get('duration_ms', 0):.0f}ms)" if 'duration_ms' in data else ''
        success = "✓" if data.get('success') else "✗" if 'success' in data else ""
        error = f"ERROR: {data.get('error', '')[:50]}" if 'error' in data else ""

        # Debug 級別顯示更多細節
        if event in ['debug', 'info'] or DEBUG_MODE:
            # 顯示額外的關鍵資訊
            extras = []

            # 顯示重要的資料欄位
            important_fields = ['agent', 'task', 'prompt', 'response', 'strategy',
                              'complexity', 'agents', 'reasoning', 'decision',
                              'tool', 'parameters', 'result', 'model']

            for field in important_fields:
                if field in data:
                    value = data[field]
                    # 截斷長字串
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    extras.append(f"{field}={value}")

            # 組合輸出
            parts = [entry['ts'], event.ljust(15), summary, duration, success, error]
            main_line = ' '.join(p for p in parts if p)

            if extras and (event == 'debug' or DEBUG_MODE):
                # 在 debug 模式或 debug 事件時顯示詳細資訊
                print(f"{main_line}")
                for extra in extras:
                    print(f"            └─ {extra}")
            else:
                print(main_line)
        else:
            # 組合輸出
            parts = [entry['ts'], event.ljust(15), summary, duration, success, error]
            print(' '.join(p for p in parts if p))

    # Debug 輸出 - JSON 到檔案
    if DEBUG_MODE:
        debug_file = LOG_DIR / f"debug_{time.strftime('%Y%m%d')}.log"
        with open(debug_file, 'a') as f:
            json.dump(entry, f)
            f.write('\n')


def timer(event: str, **kwargs):
    """計時器上下文管理器"""
    class Timer:
        def __init__(self):
            self.kwargs = kwargs

        def __enter__(self):
            self.start = time.time()
            return self

        def __exit__(self, *args):
            self.kwargs['duration_ms'] = (time.time() - self.start) * 1000
            self.kwargs['success'] = args[0] is None
            if args[0]:  # 有異常
                self.kwargs['error'] = str(args[1])
            log(event, **self.kwargs)

    return Timer()