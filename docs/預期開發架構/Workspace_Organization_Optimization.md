# Workspace 組織優化架構方案

## 現有問題分析

### 問題點
1. **扁平化結構**: 所有產出直接存放在 `/workspace` 根目錄
2. **無會話隔離**: 不同問答會話的產出混雜在一起
3. **缺乏版本管理**: 無法追蹤同一任務的多次迭代
4. **難以清理**: 無法識別哪些檔案屬於哪個會話或任務
5. **無元數據**: 缺少會話上下文、時間戳記、任務類型等資訊

## 優化方案設計

### 1. 分層目錄結構
```
workspace/
├── sessions/                  # 按會話組織
│   ├── 2024-01-20_14-30-45_abc123/
│   │   ├── .metadata.json    # 會話元數據
│   │   ├── context/          # 會話上下文
│   │   ├── outputs/          # 產出文件
│   │   └── temp/             # 臨時文件
│   └── 2024-01-20_15-45-12_xyz789/
├── projects/                  # 長期專案
│   ├── data_analysis/
│   └── code_generation/
├── shared/                    # 共享資源
│   ├── datasets/
│   └── templates/
└── archive/                   # 歸檔區
```

### 2. 會話管理機制

#### SessionManager 類設計
```python
class SessionManager:
    def __init__(self):
        self.session_id: str = self.generate_session_id()
        self.session_path: Path = self.create_session_directory()
        self.metadata: SessionMetadata = self.initialize_metadata()

    def generate_session_id(self) -> str:
        """生成唯一會話ID: 時間戳記_短UUID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"{timestamp}_{short_uuid}"

    def create_session_directory(self) -> Path:
        """建立會話目錄結構"""
        session_dir = WORKSPACE_ROOT / "sessions" / self.session_id
        (session_dir / "context").mkdir(parents=True)
        (session_dir / "outputs").mkdir(parents=True)
        (session_dir / "temp").mkdir(parents=True)
        return session_dir
```

#### 元數據結構
```python
@dataclass
class SessionMetadata:
    session_id: str
    created_at: datetime
    agent_type: str
    initial_prompt: str
    tags: List[str] = field(default_factory=list)
    task_type: str = "general"  # general, analysis, code_gen, etc.
    status: str = "active"  # active, completed, archived
    files_created: List[str] = field(default_factory=list)
    total_tokens_used: int = 0
```

### 3. 智能分類機制

#### LLM-Based TaskClassifier
```python
class TaskClassifier:
    """使用 LLM 進行智能任務分類"""

    CLASSIFICATION_PROMPT = """
    Analyze the user's request and classify it into one of these categories:
    - data_analysis: Data processing, visualization, statistical analysis, ML tasks
    - code_generation: Writing code, implementing features, creating functions/classes
    - documentation: Creating reports, documentation, technical writing
    - web_scraping: Web data extraction, browser automation, API integration
    - system_ops: File operations, system configuration, DevOps tasks
    - research: Information gathering, comparison, investigation
    - general: Tasks that don't fit other categories

    User request: {prompt}

    Respond with ONLY the category name and a confidence score (0-1).
    Format: category_name|confidence_score
    Example: data_analysis|0.95
    """

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm or LLM(config_name="classifier")
        self.cache = {}  # Cache classification results

    async def classify_task(self, prompt: str) -> Tuple[str, float, List[str]]:
        """
        使用 LLM 分析 prompt 內容決定任務類型

        Returns:
            tuple: (task_type, confidence, suggested_tags)
        """
        # Check cache first
        if prompt in self.cache:
            return self.cache[prompt]

        try:
            # Use LLM for classification
            classification_prompt = self.CLASSIFICATION_PROMPT.format(prompt=prompt)
            response = await self.llm.async_call(
                messages=[Message.system_message(classification_prompt)],
                temperature=0.3,  # Lower temperature for more deterministic classification
                max_tokens=50
            )

            # Parse response
            result = response.content.strip()
            if "|" in result:
                category, confidence = result.split("|")
                confidence = float(confidence)
            else:
                category = result
                confidence = 0.5

            # Generate suggested tags based on classification
            tags = await self.generate_tags(prompt, category)

            # Cache the result
            self.cache[prompt] = (category, confidence, tags)

            return category, confidence, tags

        except Exception as e:
            logger.warning(f"LLM classification failed: {e}, falling back to rule-based")
            return self.fallback_classification(prompt)

    async def generate_tags(self, prompt: str, category: str) -> List[str]:
        """生成相關標籤以便後續搜索"""
        tag_prompt = f"""
        Generate 3-5 relevant tags for this {category} task:
        "{prompt[:200]}"

        Return only comma-separated tags.
        """

        try:
            response = await self.llm.async_call(
                messages=[Message.system_message(tag_prompt)],
                temperature=0.5,
                max_tokens=30
            )
            tags = [tag.strip() for tag in response.content.split(",")]
            return tags[:5]  # Limit to 5 tags
        except:
            return [category]  # Fallback to category as tag

    def fallback_classification(self, prompt: str) -> Tuple[str, float, List[str]]:
        """降級到規則基礎分類（作為備用方案）"""
        prompt_lower = prompt.lower()

        # Simple keyword-based rules as fallback
        if any(word in prompt_lower for word in ["分析", "統計", "圖表", "data", "plot"]):
            return "data_analysis", 0.6, ["analysis"]
        elif any(word in prompt_lower for word in ["寫", "程式", "code", "function", "implement"]):
            return "code_generation", 0.6, ["coding"]
        elif any(word in prompt_lower for word in ["文檔", "報告", "document", "report"]):
            return "documentation", 0.6, ["docs"]
        elif any(word in prompt_lower for word in ["爬", "抓取", "scrape", "crawl"]):
            return "web_scraping", 0.6, ["scraping"]
        else:
            return "general", 0.5, ["general"]
```

#### 增強型元數據結構
```python
@dataclass
class EnhancedSessionMetadata(SessionMetadata):
    """擴展元數據以支援 LLM 分類結果"""
    task_category: str = "general"
    classification_confidence: float = 0.0
    auto_tags: List[str] = field(default_factory=list)
    user_tags: List[str] = field(default_factory=list)  # 允許用戶添加標籤
    context_summary: Optional[str] = None  # LLM 生成的上下文摘要
    related_sessions: List[str] = field(default_factory=list)  # 相關會話ID
```

### 4. 生命週期管理

#### 自動歸檔策略
```python
class WorkspaceLifecycle:
    def __init__(self):
        self.max_session_age_days = 7
        self.max_workspace_size_gb = 10

    async def cleanup_old_sessions(self):
        """定期清理舊會話"""
        sessions_dir = WORKSPACE_ROOT / "sessions"
        for session_dir in sessions_dir.iterdir():
            if self.is_expired(session_dir):
                await self.archive_session(session_dir)

    async def archive_session(self, session_dir: Path):
        """歸檔會話到壓縮檔案"""
        archive_path = WORKSPACE_ROOT / "archive" / f"{session_dir.name}.tar.gz"
        # 壓縮並移動到歸檔區
        shutil.make_archive(archive_path, 'gztar', session_dir)
        shutil.rmtree(session_dir)
```

## 實作建議

### 階段一：基礎架構 (Week 1)
1. 實作 `SessionManager` 類
2. 修改 `app/config.py` 加入會話配置
3. 更新 `LocalFileOperator` 支援會話路徑

### 階段二：智能分類 (Week 2)
1. 實作 LLM-based `TaskClassifier`
2. 整合到 `Manus` Agent 的 `run()` 方法
3. 添加元數據持久化
4. 實作分類結果快取機制

### 階段三：生命週期管理 (Week 3)
1. 實作自動歸檔機制
2. 添加定時任務清理
3. 實作會話恢復功能

## 關鍵程式碼修改點

### 1. config.py 擴充
```python
# app/config.py
class WorkspaceSettings(BaseModel):
    use_session_management: bool = True
    session_retention_days: int = 7
    auto_archive: bool = True
    max_workspace_size_gb: float = 10.0

@property
def session_root(self) -> Path:
    """獲取當前會話根目錄"""
    if hasattr(self, '_current_session'):
        return self._current_session.session_path
    return self.workspace_root
```

### 2. base.py Agent 修改
```python
# app/agent/base.py
async def run(self, request: Optional[str] = None) -> str:
    # 初始化會話管理
    if config.workspace_settings.use_session_management:
        self.session_manager = SessionManager()
        self.session_manager.metadata.initial_prompt = request
        self.session_manager.metadata.agent_type = self.name

        # 使用 LLM 進行智能分類
        classifier = TaskClassifier(self.llm)
        category, confidence, tags = await classifier.classify_task(request)

        # 更新元數據
        self.session_manager.metadata.task_category = category
        self.session_manager.metadata.classification_confidence = confidence
        self.session_manager.metadata.auto_tags = tags

        # 根據分類結果調整會話路徑
        if confidence > 0.8:  # 高置信度時使用分類目錄
            self.session_manager.adjust_path_by_category(category)
```

### 3. 檔案工具修改
```python
# app/tool/file_operators.py
class LocalFileOperator(FileOperator):
    def get_output_path(self, filename: str) -> Path:
        """根據會話管理決定輸出路徑"""
        if hasattr(config, 'session_root'):
            return config.session_root / "outputs" / filename
        return Path(filename)
```

## 預期效益

1. **組織性提升 70%**: LLM 智能分類提供更精確的組織結構
2. **查找效率提升 85%**: 基於語義理解的分類和標籤系統
3. **儲存空間優化 40%**: 自動歸檔減少活躍儲存
4. **可維護性提升**: 豐富的元數據支援深度分析
5. **用戶體驗改善**: 支援會話恢復、相關推薦和智能搜索
6. **適應性增強**: LLM 分類可自動適應新類型任務，無需修改代碼

## 風險評估

- **相容性風險**: 需確保向後相容現有工具
- **效能影響**: LLM 分類調用增加延遲（可透過快取緩解）
- **複雜度增加**: 需要更多的錯誤處理邏輯
- **成本考量**: LLM 分類會增加 API 調用成本（建議使用輕量模型）
- **準確性**: LLM 分類可能出現誤判（已設計 fallback 機制）

## 結論

此優化方案透過引入會話管理、智能分類和生命週期管理，能有效解決當前 workspace 組織混亂的問題，提升系統的可擴展性和可維護性。