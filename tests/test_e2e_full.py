#!/usr/bin/env python3
"""
完整 E2E 測試套件 - 多代理協作系統
基於測試資料集進行全面測試
"""

import asyncio
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from core.kernel import Kernel
from core.types import TaskContext


@dataclass
class TestResult:
    """測試結果"""
    test_id: str
    category: str
    success: bool
    execution_time_ms: float
    complexity: str = None
    strategy: str = None
    agents_used: List[str] = None
    error: str = None
    response_preview: str = None


class E2ETestRunner:
    """E2E 測試執行器"""

    def __init__(self, test_data_path: str = "tests/test_data.json"):
        """初始化測試執行器"""
        self.kernel = None
        self.test_data = None
        self.results: List[TestResult] = []
        self.test_data_path = test_data_path
        self.start_time = None
        self.end_time = None

    def load_test_data(self):
        """載入測試資料"""
        with open(self.test_data_path, 'r', encoding='utf-8') as f:
            self.test_data = json.load(f)
        print(f"✅ 載入測試資料: {len(self.test_data['test_cases'])} 個類別")

    async def setup(self):
        """設置測試環境"""
        print("\n" + "=" * 80)
        print("🧪 E2E 測試套件 - 多代理協作系統")
        print("=" * 80)

        try:
            self.kernel = Kernel()
            print("✅ Kernel 初始化成功")

            self.load_test_data()
            return True

        except Exception as e:
            print(f"❌ 初始化失敗: {e}")
            return False

    async def run_single_test(
        self,
        test_case: Dict,
        category: str
    ) -> TestResult:
        """執行單個測試"""
        test_id = test_case['id']
        prompt = test_case['prompt']

        print(f"\n  [{test_id}] {prompt[:50]}...")

        start_time = time.time()
        result = TestResult(
            test_id=test_id,
            category=category,
            success=False,
            execution_time_ms=0
        )

        try:
            # 執行任務
            exec_result = await self.kernel.execute(prompt)
            execution_time_ms = (time.time() - start_time) * 1000

            result.execution_time_ms = execution_time_ms
            result.success = exec_result.success
            result.response_preview = exec_result.response[:100] if exec_result.response else None

            # 提取元資料
            if exec_result.metadata:
                result.agents_used = exec_result.metadata.get('agents_used', [])

                # 從 routing 元資料提取資訊
                if 'routing' in exec_result.metadata:
                    routing = exec_result.metadata['routing']
                    result.complexity = routing.get('complexity')
                    result.strategy = routing.get('strategy')

                # 從 execution_chain 提取代理資訊
                if 'execution_chain' in exec_result.metadata:
                    chain = exec_result.metadata['execution_chain']
                    result.agents_used = [step['agent'] for step in chain]

            # 驗證預期
            validation_passed = True

            # 檢查執行時間
            max_time = test_case.get('max_execution_time_ms', 10000)
            if execution_time_ms > max_time:
                print(f"    ⚠️ 超時: {execution_time_ms:.0f}ms > {max_time}ms")
                validation_passed = False
            else:
                print(f"    ⏱️ 時間: {execution_time_ms:.0f}ms")

            # 檢查回應內容
            if 'expected_response_contains' in test_case and exec_result.response:
                response_lower = exec_result.response.lower()
                for keyword in test_case['expected_response_contains']:
                    if keyword.lower() not in response_lower:
                        print(f"    ⚠️ 缺少關鍵詞: {keyword}")
                        validation_passed = False

            # 檢查工具調用
            if 'expected_tool_calls' in test_case:
                tool_count = exec_result.metadata.get('tool_count', 0)
                if tool_count == 0:
                    print(f"    ⚠️ 未調用預期的工具")
                    validation_passed = False

            result.success = exec_result.success and validation_passed

            if result.success:
                print(f"    ✅ 成功")
            else:
                print(f"    ❌ 失敗")

        except Exception as e:
            result.error = str(e)
            result.execution_time_ms = (time.time() - start_time) * 1000
            print(f"    ❌ 異常: {e}")

        return result

    async def run_category_tests(
        self,
        category_name: str,
        category_data: Dict
    ) -> List[TestResult]:
        """執行一個類別的所有測試"""
        print(f"\n📂 {category_name.upper()}")
        print(f"   {category_data['description']}")
        print("-" * 70)

        results = []

        for test_case in category_data['cases']:
            result = await self.run_single_test(test_case, category_name)
            results.append(result)
            self.results.append(result)

            # 短暫延遲避免 API 限流
            await asyncio.sleep(0.5)

        # 類別統計
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        avg_time = sum(r.execution_time_ms for r in results) / total_count if total_count > 0 else 0

        print(f"\n  📊 類別統計: {success_count}/{total_count} 成功, 平均時間: {avg_time:.0f}ms")

        return results

    async def run_all_tests(self):
        """執行所有測試"""
        self.start_time = datetime.now()
        print(f"\n⏰ 開始時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 執行各類別測試
        for category_name, category_data in self.test_data['test_cases'].items():
            if not isinstance(category_data, dict) or 'cases' not in category_data:
                continue

            await self.run_category_tests(category_name, category_data)

        self.end_time = datetime.now()
        print(f"\n⏰ 結束時間: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ 總耗時: {(self.end_time - self.start_time).total_seconds():.1f} 秒")

    def analyze_results(self):
        """分析測試結果"""
        print("\n" + "=" * 80)
        print("📊 測試結果分析")
        print("=" * 80)

        if not self.results:
            print("❌ 無測試結果")
            return

        # 整體統計
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        success_rate = success / total * 100 if total > 0 else 0

        print(f"\n📈 整體統計:")
        print(f"  • 總測試數: {total}")
        print(f"  • 成功: {success}")
        print(f"  • 失敗: {total - success}")
        print(f"  • 成功率: {success_rate:.1f}%")

        # 按類別統計
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {
                    'total': 0,
                    'success': 0,
                    'total_time': 0,
                    'complexities': {},
                    'strategies': {}
                }

            cat = categories[result.category]
            cat['total'] += 1
            if result.success:
                cat['success'] += 1
            cat['total_time'] += result.execution_time_ms

            # 統計複雜度
            if result.complexity:
                cat['complexities'][result.complexity] = \
                    cat['complexities'].get(result.complexity, 0) + 1

            # 統計策略
            if result.strategy:
                cat['strategies'][result.strategy] = \
                    cat['strategies'].get(result.strategy, 0) + 1

        print(f"\n📊 類別分析:")
        for category, stats in categories.items():
            print(f"\n  🏷️ {category}:")
            print(f"    • 成功率: {stats['success']}/{stats['total']} " +
                  f"({stats['success']/stats['total']*100:.1f}%)")
            print(f"    • 平均時間: {stats['total_time']/stats['total']:.0f}ms")

            if stats['complexities']:
                print(f"    • 複雜度分布: {stats['complexities']}")
            if stats['strategies']:
                print(f"    • 策略分布: {stats['strategies']}")

        # 性能分析
        print(f"\n⚡ 性能分析:")
        execution_times = [r.execution_time_ms for r in self.results]
        if execution_times:
            print(f"  • 最快: {min(execution_times):.0f}ms")
            print(f"  • 最慢: {max(execution_times):.0f}ms")
            print(f"  • 平均: {sum(execution_times)/len(execution_times):.0f}ms")

        # 錯誤分析
        errors = [r for r in self.results if r.error]
        if errors:
            print(f"\n❌ 錯誤列表:")
            for error in errors[:5]:  # 只顯示前5個錯誤
                print(f"  • [{error.test_id}] {error.error[:100]}")

        # 複雜度與策略匹配
        print(f"\n🎯 複雜度與策略匹配:")
        complexity_strategy_match = {}
        for result in self.results:
            if result.complexity and result.strategy:
                key = f"{result.complexity}->{result.strategy}"
                complexity_strategy_match[key] = \
                    complexity_strategy_match.get(key, 0) + 1

        for match, count in sorted(complexity_strategy_match.items()):
            print(f"  • {match}: {count} 次")

    def generate_report(self):
        """生成測試報告"""
        report_path = f"tests/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report = {
            "test_run": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": (self.end_time - self.start_time).total_seconds()
                                  if self.start_time and self.end_time else 0
            },
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results if r.success),
                "failed": sum(1 for r in self.results if not r.success),
                "success_rate": sum(1 for r in self.results if r.success) / len(self.results) * 100
                              if self.results else 0
            },
            "results": [
                {
                    "test_id": r.test_id,
                    "category": r.category,
                    "success": r.success,
                    "execution_time_ms": r.execution_time_ms,
                    "complexity": r.complexity,
                    "strategy": r.strategy,
                    "agents_used": r.agents_used,
                    "error": r.error,
                    "response_preview": r.response_preview
                }
                for r in self.results
            ]
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📝 測試報告已保存: {report_path}")

        return report_path

    async def run_scenario(self, scenario_name: str, scenario_data: Dict):
        """執行測試場景"""
        print(f"\n🎬 場景: {scenario_name}")
        print(f"   {scenario_data['description']}")
        print("-" * 70)

        for test_id in scenario_data['sequence']:
            # 查找測試案例
            test_case = None
            category = None

            for cat_name, cat_data in self.test_data['test_cases'].items():
                if 'cases' in cat_data:
                    for case in cat_data['cases']:
                        if case['id'] == test_id:
                            test_case = case
                            category = cat_name
                            break
                if test_case:
                    break

            if test_case:
                result = await self.run_single_test(test_case, category)
                self.results.append(result)
            else:
                print(f"  ⚠️ 找不到測試案例: {test_id}")

            await asyncio.sleep(0.5)

    async def run(self, mode="full"):
        """執行測試

        Args:
            mode: 測試模式
                - "full": 執行所有測試
                - "quick": 只執行簡單測試
                - "scenario": 執行場景測試
        """
        if not await self.setup():
            return False

        try:
            if mode == "full":
                await self.run_all_tests()
            elif mode == "quick":
                # 只執行簡單和性能測試
                for category in ["simple_tasks", "performance_tasks"]:
                    if category in self.test_data['test_cases']:
                        await self.run_category_tests(
                            category,
                            self.test_data['test_cases'][category]
                        )
            elif mode == "scenario":
                # 執行場景測試
                if 'test_scenarios' in self.test_data:
                    for scenario_name, scenario_data in self.test_data['test_scenarios'].items():
                        await self.run_scenario(scenario_name, scenario_data)

            # 分析結果
            self.analyze_results()

            # 生成報告
            self.generate_report()

            return True

        except Exception as e:
            print(f"\n❌ 測試執行失敗: {e}")
            traceback.print_exc()
            return False


async def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="E2E 測試套件")
    parser.add_argument(
        "--mode",
        choices=["full", "quick", "scenario"],
        default="full",
        help="測試模式"
    )
    parser.add_argument(
        "--data",
        default="tests/test_data.json",
        help="測試資料路徑"
    )

    args = parser.parse_args()

    runner = E2ETestRunner(test_data_path=args.data)
    success = await runner.run(mode=args.mode)

    if success:
        print("\n✅ 測試完成！")
        return 0
    else:
        print("\n❌ 測試失敗！")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)