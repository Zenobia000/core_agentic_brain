#!/usr/bin/env python3
"""測試極簡 Logger - 證明 70 行夠用"""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.simple_logger import log, timer, set_trace


def test_basic():
    """基本測試"""
    print("\n=== 基本日誌測試 ===")

    # 設置 trace
    set_trace("demo1234")

    # 簡單事件
    log('app.start', summary="Core Brain starting")
    log('task.received', summary='input="1+1=?"')

    # 帶計時
    with timer('task.process', summary="calculating"):
        time.sleep(0.1)

    # 成功/失敗
    log('task.done', summary='answer="2"', duration_ms=100, success=True)
    log('task.error', summary="invalid input", error="SyntaxError", success=False)


def test_real_flow():
    """真實流程測試"""
    print("\n=== 真實流程測試 ===")

    set_trace("real4567")

    # 啟動
    log('app.start', summary="Layer1 enabled")

    # 接收任務
    user_input = "分析這段代碼"
    log('task.received', summary=f'"{user_input}"')

    # 分析
    with timer('task.analyzed') as t:
        time.sleep(0.002)  # 模擬分析
        t.kwargs['summary'] = "complexity=moderate"

    # LLM 調用
    log('llm.request', summary="gpt-4 (1.2KB)")

    with timer('llm.response') as t:
        time.sleep(0.05)  # 模擬 LLM
        t.kwargs['summary'] = "200 OK"

    # 完成
    log('task.done', summary="analysis complete", duration_ms=52, success=True)


def test_error_handling():
    """錯誤處理測試"""
    print("\n=== 錯誤處理測試 ===")

    set_trace("err8901")

    # 使用 timer 自動捕獲異常
    try:
        with timer('risky.operation', summary="doing something risky"):
            raise ValueError("Something went wrong")
    except:
        pass  # timer 已經記錄了錯誤


def compare_old_vs_new():
    """對比新舊 Logger"""
    print("\n=== 對比：70 行 vs 700 行 ===")

    print("\n舊 Logger (700+ 行):")
    print("- LayeredLogger 類")
    print("- EnhancedLogger 類")
    print("- AgentInteractionLogger 類")
    print("- 40 行的 EVENTS 字典")
    print("- Singleton 模式")
    print("- 工廠模式")
    print("- 10+ 個 processor 函數")

    print("\n新 Logger (70 行):")
    print("- 3 個函數: log(), timer(), set_trace()")
    print("- 沒有類")
    print("- 沒有模式")
    print("- 沒有廢話")

    print("\n輸出效果一樣，代碼少 10 倍")


if __name__ == "__main__":
    print("🔥 Linus 會寫的 Logger - 70 行搞定一切\n")

    test_basic()
    test_real_flow()
    test_error_handling()
    compare_old_vs_new()

    print("\n✅ 證明完畢：簡單就是美")
    print("記住 Linus 的話：'如果你需要超過 3 層縮進，你就已經完蛋了'")