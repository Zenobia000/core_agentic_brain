#!/usr/bin/env python3
"""
OpenCode Platform - 快速啟動腳本
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# 確保載入 .env 檔案（使用專案根目錄）
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)

# 設置 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_cli():
    """啟動 CLI"""
    from cli.main import app
    app()


def run_tui():
    """啟動 TUI"""
    from cli.tui.app import run_tui
    run_tui()


def run_api():
    """啟動 API"""
    import uvicorn
    from config.settings import settings
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )


def run_demo():
    """執行演示"""
    asyncio.run(_demo())


async def _demo():
    """演示腳本"""
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    
    console = Console()
    
    console.print(Panel.fit(
        "[bold cyan]OpenCode Platform Demo[/bold cyan]\n"
        "OpenCode-Centric Intelligent Platform",
        border_style="cyan"
    ))
    
    console.print("\n[bold]1. Initializing Engine...[/bold]")
    
    try:
        from core.engine import OpenCodeEngine
        from core.protocols import Intent, Context, EventType
        
        engine = OpenCodeEngine(config={"use_redis": False})
        await engine.initialize()
        
        console.print("[green]✅ Engine initialized[/green]")
        
        # 測試對話
        console.print("\n[bold]2. Testing Chat...[/bold]")
        
        context = Context(session_id="demo", user_id="demo_user")
        intent = Intent.create(
            content="什麼是 RAG？",
            context=context
        )
        
        console.print(f"[dim]Query: {intent.content}[/dim]\n")
        
        async for event in engine.process_intent(intent):
            if event.type == EventType.THINKING:
                console.print(f"[dim]💭 {event.payload.get('content', '')}[/dim]")
            elif event.type == EventType.TOOL_CALL:
                console.print(f"[cyan]🔧 {event.payload.get('content', '')}[/cyan]")
            elif event.type == EventType.ANSWER:
                answer = event.payload.get('content', '')
                console.print(Panel(Markdown(answer), title="Answer", border_style="green"))
            elif event.type == EventType.ERROR:
                console.print(f"[red]❌ {event.payload.get('content', '')}[/red]")
        
        # 關閉
        await engine.shutdown()
        console.print("\n[green]✅ Demo complete[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


def check_deps():
    """檢查依賴"""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    table = Table(title="Dependency Check")
    table.add_column("Package")
    table.add_column("Status")
    
    packages = [
        ("typer", "CLI"),
        ("rich", "CLI"),
        ("textual", "TUI"),
        ("fastapi", "API"),
        ("openai", "LLM"),
        ("qdrant_client", "Vector DB"),
        ("redis", "Cache"),
        ("pydantic", "Config"),
    ]
    
    for pkg, purpose in packages:
        try:
            __import__(pkg)
            table.add_row(f"{pkg} ({purpose})", "[green]✓[/green]")
        except ImportError:
            table.add_row(f"{pkg} ({purpose})", "[red]✗[/red]")
    
    console.print(table)
    
    # 檢查環境變數
    console.print("\n[bold]Environment Variables:[/bold]")
    
    env_vars = [
        "OPENAI_API_KEY",
        "REDIS_HOST",
        "QDRANT_HOST",
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            display = value[:10] + "..." if len(value) > 10 else value
            console.print(f"  {var}: [green]{display}[/green]")
        else:
            console.print(f"  {var}: [yellow]not set[/yellow]")


def main():
    parser = argparse.ArgumentParser(description="OpenCode Platform Launcher")
    parser.add_argument(
        "command",
        choices=["cli", "tui", "api", "demo", "check"],
        help="Command to run"
    )
    
    args = parser.parse_args()
    
    if args.command == "cli":
        run_cli()
    elif args.command == "tui":
        run_tui()
    elif args.command == "api":
        run_api()
    elif args.command == "demo":
        run_demo()
    elif args.command == "check":
        check_deps()


if __name__ == "__main__":
    main()
