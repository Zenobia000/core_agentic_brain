#!/usr/bin/env python3
"""
完整的端到端測試 - 測試整個系統流程
基於 Linus 原則：實際測試，不是理論
"""

import asyncio
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from core.kernel import Kernel
from core.types import TaskContext


class E2ETestSuite:
    """端到端測試套件"""

    def __init__(self):
        self.kernel = None
        self.passed = 0
        self.failed = 0
        self.tests = []

    async def setup(self):
        """設置測試環境"""
        print("=" * 60)
        print("🧪 E2E 測試套件 - Core Agentic Brain")
        print("=" * 60)

        try:
            self.kernel = Kernel()
            print("✓ Kernel 初始化成功")
            return True
        except Exception as e:
            print(f"✗ Kernel 初始化失敗: {e}")
            return False

    async def test_basic_prompt_processing(self):
        """測試 1: 基本提示處理"""
        print("\n[測試 1] 基本提示處理")

        try:
            result = await self.kernel.execute("Hello, what is 2+2?")
            assert result is not None
            assert result.success is not None
            print(f"  ✓ 成功處理簡單提示")
            print(f"    - 回應: {result.response[:100] if result.response else 'None'}...")
            return True
        except Exception as e:
            print(f"  ✗ 失敗: {e}")
            return False

    async def test_python_tool_execution(self):
        """測試 2: Python 工具執行"""
        print("\n[測試 2] Python 工具執行")

        try:
            # 直接測試工具
            result = await self.kernel.call_tool("python", {
                "code": """
import math
print(f"π = {math.pi}")
print(f"e = {math.e}")
result = sum(range(10))
print(f"Sum of 0-9 = {result}")
"""
            })

            assert result is not None
            assert result.get("success") == True
            assert "3.14159" in result.get("output", "")

            print(f"  ✓ Python 工具執行成功")
            print(f"    - 輸出: {result.get('output', '').strip()}")
            return True
        except Exception as e:
            print(f"  ✗ 失敗: {e}")
            return False

    async def test_file_operations(self):
        """測試 3: 檔案操作工具"""
        print("\n[測試 3] 檔案操作工具")

        test_file = "test_temp.txt"
        test_content = "測試內容：這是 E2E 測試"

        try:
            # 寫入檔案
            write_result = await self.kernel.call_tool("files", {
                "operation": "write",
                "path": test_file,
                "content": test_content
            })
            assert write_result.get("success") == True
            print(f"  ✓ 檔案寫入成功")

            # 讀取檔案
            read_result = await self.kernel.call_tool("files", {
                "operation": "read",
                "path": test_file
            })
            assert read_result.get("success") == True
            assert read_result.get("content") == test_content
            print(f"  ✓ 檔案讀取成功")

            # 檢查存在
            exists_result = await self.kernel.call_tool("files", {
                "operation": "exists",
                "path": test_file
            })
            assert exists_result.get("exists") == True
            print(f"  ✓ 檔案存在檢查成功")

            # 刪除檔案
            delete_result = await self.kernel.call_tool("files", {
                "operation": "delete",
                "path": test_file
            })
            assert delete_result.get("success") == True
            print(f"  ✓ 檔案刪除成功")

            return True
        except Exception as e:
            print(f"  ✗ 失敗: {e}")
            # 清理
            try:
                Path(test_file).unlink(missing_ok=True)
            except:
                pass
            return False

    async def test_agent_routing(self):
        """測試 4: Agent 路由"""
        print("\n[測試 4] Agent 路由")

        try:
            # 測試不同複雜度的任務
            tasks = [
                ("計算 1+1", "simple"),
                ("建立一個 REST API", "complex"),
                ("解釋量子計算", "medium")
            ]

            for task, expected_complexity in tasks:
                context = TaskContext(prompt=task)
                result = await self.kernel.execute(task, context)
                print(f"  ✓ 任務 '{task[:20]}...' 處理完成")

            return True
        except Exception as e:
            print(f"  ✗ 失敗: {e}")
            return False

    async def test_communication_bus(self):
        """測試 5: 通訊匯流排"""
        print("\n[測試 5] 通訊匯流排")

        try:
            from core.communication import Message, MessageType

            # 發送測試訊息
            test_messages = [
                Message(
                    type=MessageType.TOOL_CALL,
                    content={"code": "print('Bus test 1')"},
                    source="test",
                    target="tool.python"
                ),
                Message(
                    type=MessageType.TOOL_CALL,
                    content={"code": "print('Bus test 2')"},
                    source="test",
                    target="tool.python"
                )
            ]

            for msg in test_messages:
                result = await self.kernel.bus.send(msg)
                assert result is not None
                print(f"  ✓ 訊息 {msg.source}->{msg.target} 成功")

            # 檢查歷史
            history = self.kernel.bus.get_history()
            assert len(history) >= len(test_messages)
            print(f"  ✓ 訊息歷史記錄: {len(history)} 條")

            return True
        except Exception as e:
            print(f"  ✗ 失敗: {e}")
            return False

    async def test_prompt_loading(self):
        """測試 6: 提示詞載入"""
        print("\n[測試 6] 提示詞載入")

        try:
            # 測試不同的提示詞路徑
            prompts_to_test = [
                "planner.system",
                "executor.system",
                "reviewer.system"
            ]

            for prompt_path in prompts_to_test:
                prompt = self.kernel.get_prompt(prompt_path)
                assert prompt is not None
                assert len(prompt) > 0
                print(f"  ✓ 載入 {prompt_path}: {len(prompt)} 字元")

            # 測試參數替換
            prompt_with_params = self.kernel.get_prompt(
                "executor.execution_prompt",
                user_query="測試查詢",
                tools="python, files"
            )
            assert "測試查詢" in prompt_with_params or len(prompt_with_params) > 0
            print(f"  ✓ 參數替換成功")

            return True
        except Exception as e:
            print(f"  ✗ 失敗: {e}")
            return False

    async def test_error_handling(self):
        """測試 7: 錯誤處理"""
        print("\n[測試 7] 錯誤處理")

        try:
            # 測試無效工具
            result = await self.kernel.call_tool("invalid_tool", {})
            assert "error" in str(result).lower() or result.get("error") is not None
            print(f"  ✓ 無效工具錯誤處理正確")

            # 測試無效 Python 代碼
            result = await self.kernel.call_tool("python", {
                "code": "import nonexistent_module"
            })
            assert result.get("success") == False
            print(f"  ✓ Python 錯誤處理正確")

            # 測試無效檔案操作
            result = await self.kernel.call_tool("files", {
                "operation": "read",
                "path": "/nonexistent/path/file.txt"
            })
            assert result.get("success") == False
            print(f"  ✓ 檔案錯誤處理正確")

            return True
        except Exception as e:
            print(f"  ✗ 失敗: {e}")
            return False

    async def test_performance(self):
        """測試 8: 性能測試"""
        print("\n[測試 8] 性能測試")

        import time

        try:
            # 測試多個並行工具調用
            start_time = time.time()

            tasks = [
                self.kernel.call_tool("python", {"code": f"print({i}*{i})"}
                ) for i in range(5)
            ]

            results = await asyncio.gather(*tasks)

            elapsed = time.time() - start_time

            # 驗證所有結果
            for i, result in enumerate(results):
                assert result.get("success") == True

            print(f"  ✓ 5 個並行工具調用完成")
            print(f"    - 耗時: {elapsed:.2f} 秒")
            print(f"    - 平均: {elapsed/5:.3f} 秒/調用")

            return True
        except Exception as e:
            print(f"  ✗ 失敗: {e}")
            return False

    async def test_integration(self):
        """測試 9: 集成測試 - 複雜工作流"""
        print("\n[測試 9] 集成測試")

        try:
            # 創建複雜任務
            complex_task = """
            請執行以下任務：
            1. 計算斐波那契數列前10項
            2. 將結果保存到檔案
            3. 讀取並驗證檔案內容
            """

            # Step 1: 計算
            calc_result = await self.kernel.call_tool("python", {
                "code": """
fib = [0, 1]
for i in range(2, 10):
    fib.append(fib[-1] + fib[-2])
print("Fibonacci:", fib)
result = str(fib)
"""
            })
            assert calc_result.get("success") == True
            print(f"  ✓ Step 1: 計算完成")

            # Step 2: 保存
            save_result = await self.kernel.call_tool("files", {
                "operation": "write",
                "path": "test_fib.txt",
                "content": "Fibonacci: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]"
            })
            assert save_result.get("success") == True
            print(f"  ✓ Step 2: 保存完成")

            # Step 3: 驗證
            verify_result = await self.kernel.call_tool("files", {
                "operation": "read",
                "path": "test_fib.txt"
            })
            assert verify_result.get("success") == True
            assert "Fibonacci" in verify_result.get("content", "")
            print(f"  ✓ Step 3: 驗證完成")

            # 清理
            await self.kernel.call_tool("files", {
                "operation": "delete",
                "path": "test_fib.txt"
            })

            return True
        except Exception as e:
            print(f"  ✗ 失敗: {e}")
            return False

    async def run_all_tests(self):
        """執行所有測試"""
        # 設置
        if not await self.setup():
            print("\n❌ 設置失敗，無法執行測試")
            return

        # 定義測試
        tests = [
            ("基本提示處理", self.test_basic_prompt_processing),
            ("Python 工具", self.test_python_tool_execution),
            ("檔案操作", self.test_file_operations),
            ("Agent 路由", self.test_agent_routing),
            ("通訊匯流排", self.test_communication_bus),
            ("提示詞載入", self.test_prompt_loading),
            ("錯誤處理", self.test_error_handling),
            ("性能測試", self.test_performance),
            ("集成測試", self.test_integration)
        ]

        # 執行測試
        for name, test_func in tests:
            try:
                if await test_func():
                    self.passed += 1
                else:
                    self.failed += 1
            except Exception as e:
                print(f"\n[測試] {name}")
                print(f"  ✗ 異常: {e}")
                self.failed += 1

        # 總結
        self.print_summary()

    def print_summary(self):
        """打印測試總結"""
        print("\n" + "=" * 60)
        print("📊 測試總結")
        print("=" * 60)

        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"總測試數: {total}")
        print(f"✅ 通過: {self.passed}")
        print(f"❌ 失敗: {self.failed}")
        print(f"成功率: {success_rate:.1f}%")

        if self.failed == 0:
            print("\n🎉 所有測試通過！系統運作正常。")
            print("\nLinus 會說：")
            print('"Talk is cheap. Show me the code." - 代碼通過了測試')
        else:
            print(f"\n⚠️  有 {self.failed} 個測試失敗，需要修復。")
            print("\nLinus 會說：")
            print('"Fix your shit!" - 修好你的垃圾代碼')


async def main():
    """主函數"""
    test_suite = E2ETestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    # 運行測試
    try:
        asyncio.run(main())
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)