# Core Agentic Brain 🧠

**A minimalist, progressive agent platform following Linus Torvalds' design philosophy**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/architecture-layered-green.svg)](docs/project_architecture/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> "Good Taste" - Eliminate special cases, not add conditions
> Core system < 500 lines, cold start < 2 seconds

Core Agentic Brain is a progressive, layered agent architecture that starts minimal and grows with your needs. Built with extreme simplicity in mind, following the Linux kernel creator's philosophy of clean, practical code.

## 🎉 What's New

- ✅ **Layer 1 Complete**: Smart routing system with specialized agents (Planner, Executor, Reviewer)
- ✅ **Structured Logging**: Integrated structlog for comprehensive system observability
- ✅ **Type System**: Full type definitions for robust development
- 🚀 **100% Layer 0 & 1 Implementation**: Core and routing layers fully operational

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip or poetry
- OpenAI API key (or compatible LLM)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/core_agentic_brain.git
cd core_agentic_brain

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Basic Usage

```bash
# Interactive mode (CLI)
python3 main.py

# Direct task execution
python3 main.py --task "Calculate the sum of 1 to 100"

# Specify configuration mode
python3 main.py --mode minimal  # Fastest, Layer 0 only
python3 main.py --mode standard  # Layer 1 routing enabled (default)
python3 main.py --mode enterprise # Full features (coming soon)
```

## 📁 Architecture Overview

The project follows a **progressive layered architecture**:

```
Layer 0: Minimal Core (95% Complete) ✅
├── < 500 lines total
├── Cold start < 2s
└── Basic tools only

Layer 1: Smart Routing (20% Complete) 🚧
├── Task complexity analysis
├── Fast path vs Agent path
└── Multi-agent orchestration

Layer 2: Enterprise Features (10% Complete) 📅
├── RBAC permissions
├── Audit logging
└── MCP protocol support
```

## 📚 Documentation

- [System Architecture](docs/project_architecture/01_System_Architecture.md) - Complete system design
- [Implementation Guide](docs/project_architecture/03_Technical_Implementation_Guide.md) - Developer guide
- [API Specification](docs/project_architecture/04_API_Specification.md) - API reference
- [Folder Structure](docs/project_architecture/FOLDER_STRUCTURE.md) - Project organization
- [WBS Progress](docs/project_architecture/WBS_Progress_Tracking.md) - Development tracking

## 🧪 Testing

```bash
# Run all tests
python3 -m pytest

# Run specific test module
python3 -m pytest tests/unit/test_types.py -v

# Run with coverage
python3 -m pytest --cov=core --cov-report=html
```

## 🛠️ Development

### Current Progress (45% Overall)
- ✅ Layer 0 Core: 95% complete
- 🚧 Layer 1 Routing: 20% complete
- 📅 Layer 2 Enterprise: 10% complete

### Priority Tasks
1. ✅ Create `core/types.py` - Data structures
2. ✅ Write unit tests for core modules
3. ✅ Implement router system
4. ⬜ Implement agent system
5. ⬜ Add browser and shell tools

See [Implementation Checklist](docs/project_architecture/IMPLEMENTATION_CHECKLIST.md) for detailed status.

## 🔧 Configuration

The system supports three configuration modes:

### Minimal Mode (Default)
- Fastest startup, < 500 lines of code
- Direct tool execution
- Perfect for simple tasks

### Standard Mode
- Adds intelligent routing
- Task complexity analysis
- Agent orchestration for complex tasks

### Enterprise Mode
- Full feature set
- RBAC permissions
- Audit logging
- MCP protocol support

Configuration is loaded from `config.yaml` with environment variable overrides:

```yaml
# config.yaml example
llm:
  provider: openai
  model: gpt-3.5-turbo

tools:
  enabled:
    - python
    - files
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Keep it simple - Linus philosophy applies
2. No special cases - eliminate them, don't add conditions
3. Test your code - aim for >80% coverage
4. Document clearly - code should be self-explanatory

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Linus Torvalds' kernel design philosophy
- Built for Claude Code and MCP compatibility
- Community contributions and feedback

---

**Project Status:** Active Development 🚧
**Version:** 0.1.0 (Pre-release)
**Last Updated:** 2026-01-27
