# Workspace MVP 架構設計 - 平衡通用性與管理性

## 設計理念
**「簡單但不簡陋，通用但不失控」**

## 1. MVP 核心架構（3層設計）

```
workspace/
├── {context_id}/              # 上下文層（通用識別）
│   ├── .meta.json            # 元數據
│   ├── memory/               # 記憶存儲
│   ├── artifacts/            # 產出文件
│   └── temp/                 # 臨時文件
└── _shared/                  # 共享資源
    ├── templates/            # 可重用模板
    └── .registry.json        # 資源註冊表
```

### 為什麼這樣設計？
- **context_id**: 通用識別符，可以是 customer_id、session_id、project_id 等
- **單層結構**: 降低複雜度，但保留擴展性
- **元數據驅動**: 透過 .meta.json 實現靈活管理

## 2. 通用 Context Manager

```python
class ContextManager:
    """通用的上下文管理器 - MVP 核心"""

    def __init__(self, context_type: str, context_id: str = None):
        """
        Args:
            context_type: 上下文類型 (session/customer/project/task)
            context_id: 可選ID，不提供則自動生成
        """
        self.context_type = context_type
        self.context_id = context_id or self._generate_id()
        self.path = WORKSPACE_ROOT / self.context_id
        self.metadata = self._init_metadata()

    def _generate_id(self) -> str:
        """生成ID: {type}_{timestamp}_{short_uuid}"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        short_id = str(uuid.uuid4())[:6]
        return f"{self.context_type}_{timestamp}_{short_id}"

    def _init_metadata(self) -> dict:
        """初始化元數據"""
        return {
            "id": self.context_id,
            "type": self.context_type,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "parent": None,  # 可選的父級關聯
            "tags": [],      # 靈活的標籤系統
            "config": {}     # 自定義配置
        }
```

## 3. 靈活的隔離策略

```python
class IsolationStrategy:
    """可配置的隔離策略"""

    LEVELS = {
        "none": {         # 開發/測試環境
            "share_memory": True,
            "share_artifacts": True,
            "encryption": False
        },
        "basic": {        # 標準隔離（MVP默認）
            "share_memory": False,
            "share_artifacts": "explicit",  # 需明確授權
            "encryption": False
        },
        "strict": {       # 生產環境
            "share_memory": False,
            "share_artifacts": False,
            "encryption": True
        }
    }

    @classmethod
    def get_strategy(cls, level: str = "basic"):
        """獲取隔離策略"""
        return cls.LEVELS.get(level, cls.LEVELS["basic"])
```

## 4. 簡化的配置系統

```python
# config.py 擴展
class WorkspaceConfig:
    """MVP 工作空間配置"""

    # 基本配置
    enabled: bool = True
    root_path: str = "./workspace"

    # 上下文配置
    default_context_type: str = "session"  # session/customer/project
    auto_cleanup: bool = True
    retention_days: int = 7

    # 隔離級別
    isolation_level: str = "basic"  # none/basic/strict

    # 儲存限制
    max_context_size_mb: int = 100
    max_file_size_mb: int = 10

    # 功能開關
    enable_sharing: bool = True      # 是否允許共享
    enable_llm_classify: bool = False # 是否使用LLM分類（可選）
    enable_auto_archive: bool = True  # 是否自動歸檔
```

## 5. 統一的接口設計

```python
class WorkspaceAPI:
    """統一的 Workspace API - 簡單直觀"""

    def create_context(
        self,
        context_type: str = None,
        context_id: str = None,
        metadata: dict = None
    ) -> Context:
        """創建新的工作上下文"""
        context_type = context_type or config.default_context_type
        manager = ContextManager(context_type, context_id)
        if metadata:
            manager.metadata.update(metadata)
        return manager

    def get_context(self, context_id: str) -> Context:
        """獲取現有上下文"""
        path = WORKSPACE_ROOT / context_id
        if not path.exists():
            raise ContextNotFound(context_id)
        return ContextManager.load(context_id)

    def save_artifact(
        self,
        context_id: str,
        content: Any,
        filename: str = None,
        artifact_type: str = "auto"
    ) -> str:
        """保存產出到上下文"""
        context = self.get_context(context_id)

        # 自動決定存儲位置
        if artifact_type == "memory":
            path = context.path / "memory" / filename
        elif artifact_type == "temp":
            path = context.path / "temp" / filename
        else:
            path = context.path / "artifacts" / filename

        # 寫入文件
        path.parent.mkdir(exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(str(content))

        # 更新元數據
        context.metadata["files"] = context.metadata.get("files", [])
        context.metadata["files"].append(str(path))
        context.save_metadata()

        return str(path)

    def share_artifact(
        self,
        source_context: str,
        artifact_path: str,
        target_context: str = None
    ) -> bool:
        """共享產出（根據隔離策略）"""
        strategy = IsolationStrategy.get_strategy(config.isolation_level)

        if not strategy["share_artifacts"]:
            return False

        if strategy["share_artifacts"] == "explicit":
            # 需要明確授權邏輯
            if not self._check_permission(source_context, target_context):
                return False

        # 執行共享
        if target_context:
            # 共享給特定上下文
            self._copy_to_context(artifact_path, target_context)
        else:
            # 共享到 _shared
            self._copy_to_shared(artifact_path)

        return True
```

## 6. 使用範例

### 6.1 基本使用
```python
# 創建會話上下文
api = WorkspaceAPI()
context = api.create_context(
    context_type="session",
    metadata={"user": "user123", "task": "data_analysis"}
)

# 保存產出
api.save_artifact(
    context_id=context.context_id,
    content=analysis_result,
    filename="result.json",
    artifact_type="artifacts"
)

# 保存記憶
api.save_artifact(
    context_id=context.context_id,
    content=conversation_history,
    filename="history.json",
    artifact_type="memory"
)
```

### 6.2 跨系統集成
```python
# 為不同系統創建上下文
slack_context = api.create_context(
    context_type="integration",
    context_id="slack_channel_123",
    metadata={"platform": "slack", "channel": "general"}
)

crm_context = api.create_context(
    context_type="customer",
    context_id="crm_customer_456",
    metadata={"platform": "salesforce", "account": "ABC Corp"}
)
```

### 6.3 靈活的層級關聯
```python
# 透過 metadata 實現層級關係（而非目錄結構）
project_context = api.create_context(
    context_type="project",
    metadata={"name": "Q4_Analysis"}
)

session_context = api.create_context(
    context_type="session",
    metadata={
        "parent": project_context.context_id,  # 關聯到項目
        "user": "analyst_01"
    }
)
```

## 7. 管理功能

### 7.1 自動清理
```python
class AutoCleanup:
    """簡單的自動清理機制"""

    def cleanup_old_contexts(self):
        """清理過期的上下文"""
        cutoff_date = datetime.now() - timedelta(days=config.retention_days)

        for context_dir in WORKSPACE_ROOT.iterdir():
            if context_dir.name.startswith("_"):
                continue  # 跳過系統目錄

            meta_file = context_dir / ".meta.json"
            if meta_file.exists():
                meta = json.loads(meta_file.read_text())
                created = datetime.fromisoformat(meta["created_at"])

                if created < cutoff_date and meta["status"] != "archived":
                    # 歸檔或刪除
                    if config.enable_auto_archive:
                        self._archive_context(context_dir)
                    else:
                        shutil.rmtree(context_dir)
```

### 7.2 簡單的監控
```python
class WorkspaceMonitor:
    """基本的監控功能"""

    def get_stats(self) -> dict:
        """獲取工作空間統計"""
        total_contexts = 0
        total_size = 0
        context_types = {}

        for context_dir in WORKSPACE_ROOT.iterdir():
            if context_dir.is_dir() and not context_dir.name.startswith("_"):
                total_contexts += 1
                total_size += self._get_dir_size(context_dir)

                # 統計類型分佈
                meta_file = context_dir / ".meta.json"
                if meta_file.exists():
                    meta = json.loads(meta_file.read_text())
                    ctx_type = meta.get("type", "unknown")
                    context_types[ctx_type] = context_types.get(ctx_type, 0) + 1

        return {
            "total_contexts": total_contexts,
            "total_size_mb": total_size / 1024 / 1024,
            "context_types": context_types,
            "isolation_level": config.isolation_level
        }
```

## 8. 擴展點設計

```python
class WorkspaceExtension:
    """預留的擴展接口"""

    hooks = {
        "before_create": [],      # 創建前的鉤子
        "after_create": [],       # 創建後的鉤子
        "before_save": [],        # 保存前的鉤子
        "after_archive": []       # 歸檔後的鉤子
    }

    @classmethod
    def register_hook(cls, event: str, handler: callable):
        """註冊擴展鉤子"""
        cls.hooks[event].append(handler)

    @classmethod
    def trigger_hook(cls, event: str, **kwargs):
        """觸發鉤子"""
        for handler in cls.hooks.get(event, []):
            handler(**kwargs)

# 使用範例：添加加密擴展
def encrypt_on_save(context_id: str, content: bytes):
    """保存時加密（擴展功能）"""
    if IsolationStrategy.get_strategy()["encryption"]:
        return encrypt(content)
    return content

WorkspaceExtension.register_hook("before_save", encrypt_on_save)
```

## 9. 遷移路徑

### 從 MVP 到完整版
```python
class MigrationPath:
    """平滑的升級路徑"""

    steps = {
        "1_add_tenant": "在 context_id 前加入 tenant 前綴",
        "2_add_customer": "將 context 分組到 customer 目錄",
        "3_add_encryption": "啟用加密功能",
        "4_add_distributed": "遷移到分散式儲存"
    }

    def can_upgrade(self) -> bool:
        """檢查是否可以升級"""
        # 元數據驅動的設計使升級變得簡單
        return True
```

## 10. 關鍵優勢

1. **通用性**
   - context_id 可適配任何系統
   - 元數據驅動，靈活擴展
   - 不綁定特定業務邏輯

2. **管理性**
   - 統一的 API 接口
   - 可配置的隔離級別
   - 自動清理與監控

3. **簡單性**
   - 單層目錄結構
   - 最少的必要功能
   - 清晰的擴展點

4. **可演化**
   - 預留升級路徑
   - Hook 機制支援擴展
   - 向後相容設計

## 總結

這個 MVP 架構：
- **足夠簡單**：開發者 1 天就能理解並開始使用
- **足夠通用**：適配各種集成場景
- **足夠可控**：提供必要的管理功能
- **足夠靈活**：可根據需求逐步演化

核心理念是**「用元數據管理複雜性，用簡單結構保證通用性」**。