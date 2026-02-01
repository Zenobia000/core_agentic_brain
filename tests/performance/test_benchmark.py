#!/usr/bin/env python3
"""Performance benchmarks for Core Agentic Brain."""

import time
import asyncio
from typing import List, Dict
import statistics

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.schema import detect_schema, reset_schema_loader
from core.types import TaskContext


class BenchmarkRunner:
    """Run performance benchmarks for the system."""

    def __init__(self):
        """Initialize benchmark runner."""
        self.results = []

    async def benchmark_schema_detection(self, iterations: int = 100) -> Dict:
        """Benchmark domain schema detection performance."""
        # Ensure fresh schema loader
        reset_schema_loader()

        test_prompts = [
            "What is 2+2?",  # No domain match
            "規劃京都旅行",  # Travel domain
            "Create a sorting algorithm",  # Code domain
            "Plan my vacation to Europe",  # Travel domain
            "寫一個快速排序函數",  # Code domain
        ]

        times = []

        for _ in range(iterations):
            for prompt in test_prompts:
                start = time.perf_counter()
                schema = detect_schema(prompt)
                elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

                times.append(elapsed)

        return {
            "operation": "schema_detection",
            "iterations": iterations * len(test_prompts),
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
            "min_ms": min(times),
            "max_ms": max(times),
            "p95_ms": sorted(times)[int(len(times) * 0.95)],
            "p99_ms": sorted(times)[int(len(times) * 0.99)]
        }

    async def benchmark_cold_start(self) -> Dict:
        """Benchmark cold start time."""
        import importlib

        modules_to_import = [
            "core.kernel",
            "core.llm",
            "core.tools",
            "core.config",
            "core.orchestration",
            "router.llm_analyzer"
        ]

        times = []

        for module_name in modules_to_import:
            start = time.perf_counter()
            importlib.import_module(module_name)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        total_time = sum(times)

        return {
            "operation": "cold_start",
            "total_ms": total_time,
            "modules": len(modules_to_import),
            "breakdown": dict(zip(modules_to_import, times))
        }

    async def run_all_benchmarks(self):
        """Run all performance benchmarks."""
        print("Running performance benchmarks...")
        print("=" * 50)

        # Schema detection benchmark
        print("\nSchema Detection Benchmark")
        schema_results = await self.benchmark_schema_detection(100)
        self._print_results(schema_results)

        # Cold start benchmark
        print("\nCold Start Benchmark")
        cold_start_results = await self.benchmark_cold_start()
        self._print_cold_start(cold_start_results)

        print("\n" + "=" * 50)
        print("Benchmarks complete!")

        return {
            "schema_detection": schema_results,
            "cold_start": cold_start_results
        }

    def _print_results(self, results: Dict):
        """Print benchmark results."""
        print(f"  Iterations: {results['iterations']}")
        print(f"  Mean: {results['mean_ms']:.3f}ms")
        print(f"  Median: {results['median_ms']:.3f}ms")
        print(f"  Std Dev: {results['stdev_ms']:.3f}ms")
        print(f"  Min: {results['min_ms']:.3f}ms")
        print(f"  Max: {results['max_ms']:.3f}ms")
        print(f"  P95: {results['p95_ms']:.3f}ms")
        print(f"  P99: {results['p99_ms']:.3f}ms")

    def _print_cold_start(self, results: Dict):
        """Print cold start results."""
        print(f"  Total: {results['total_ms']:.3f}ms")
        print(f"  Modules: {results['modules']}")
        print("  Breakdown:")
        for module, time_ms in results['breakdown'].items():
            print(f"    {module}: {time_ms:.3f}ms")


async def main():
    """Run benchmarks."""
    runner = BenchmarkRunner()
    await runner.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())