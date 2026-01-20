"""Session management for organizing workspace outputs"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Any

from app.config import WORKSPACE_ROOT
from app.logger import logger


@dataclass
class SessionMetadata:
    """Base metadata structure for sessions"""
    session_id: str
    created_at: str  # ISO format string
    agent_type: str
    initial_prompt: str
    tags: List[str] = field(default_factory=list)
    task_type: str = "general"
    status: str = "active"  # active, completed, archived
    files_created: List[str] = field(default_factory=list)
    total_tokens_used: int = 0


@dataclass
class EnhancedSessionMetadata(SessionMetadata):
    """Extended metadata with LLM classification results"""
    task_category: str = "general"
    classification_confidence: float = 0.0
    auto_tags: List[str] = field(default_factory=list)
    user_tags: List[str] = field(default_factory=list)
    context_summary: Optional[str] = None
    related_sessions: List[str] = field(default_factory=list)


class SessionManager:
    """Manages session lifecycle and organization"""

    def __init__(self, use_enhanced: bool = True):
        """
        Initialize session manager

        Args:
            use_enhanced: Whether to use enhanced metadata with LLM classification
        """
        self.session_id = self.generate_session_id()
        self.session_path = self.create_session_directory()
        self.metadata_class = EnhancedSessionMetadata if use_enhanced else SessionMetadata
        self.metadata = self.initialize_metadata()
        self.use_enhanced = use_enhanced
        self.shared_resource_manager = None  # Lazy load when needed
        logger.info(f"Session initialized: {self.session_id}")

    def generate_session_id(self) -> str:
        """Generate unique session ID: timestamp_shortUUID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"{timestamp}_{short_uuid}"

    def create_session_directory(self) -> Path:
        """Create session directory structure"""
        session_dir = WORKSPACE_ROOT / "sessions" / self.session_id

        # Create subdirectories
        directories = ["context", "outputs", "temp"]
        for dir_name in directories:
            (session_dir / dir_name).mkdir(parents=True, exist_ok=True)

        logger.debug(f"Created session directory: {session_dir}")
        return session_dir

    def initialize_metadata(self) -> SessionMetadata:
        """Initialize session metadata"""
        metadata = self.metadata_class(
            session_id=self.session_id,
            created_at=datetime.now().isoformat(),
            agent_type="",  # To be set by agent
            initial_prompt=""  # To be set when task starts
        )
        self.save_metadata(metadata)
        return metadata

    def save_metadata(self, metadata: Optional[SessionMetadata] = None) -> None:
        """Save metadata to file"""
        if metadata is None:
            metadata = self.metadata

        metadata_path = self.session_path / ".metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)

        logger.debug(f"Metadata saved to {metadata_path}")

    def load_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """Load metadata from existing session"""
        session_dir = WORKSPACE_ROOT / "sessions" / session_id
        metadata_path = session_dir / ".metadata.json"

        if not metadata_path.exists():
            logger.warning(f"Metadata not found for session: {session_id}")
            return None

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return self.metadata_class(**data)
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return None

    def update_metadata(self, **kwargs) -> None:
        """Update metadata fields"""
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
        self.save_metadata()

    def add_file(self, file_path: str) -> None:
        """Track file creation in metadata"""
        if file_path not in self.metadata.files_created:
            self.metadata.files_created.append(file_path)
            self.save_metadata()

    def get_output_path(self, filename: str, subdir: str = "outputs") -> Path:
        """
        Get path for output file within session

        Args:
            filename: Name of the file
            subdir: Subdirectory within session (outputs, temp, context)

        Returns:
            Full path for the file
        """
        return self.session_path / subdir / filename

    def adjust_path_by_category(self, category: str, confidence: float = 0.8) -> None:
        """
        Adjust session path based on task category

        Args:
            category: Task category from classifier
            confidence: Confidence threshold to use category-specific path
        """
        if confidence > 0.8 and category != "general":
            # Create project-specific directory if high confidence
            project_dir = WORKSPACE_ROOT / "projects" / category / self.session_id
            project_dir.mkdir(parents=True, exist_ok=True)

            # Create symlink from session to project
            symlink_path = self.session_path / "project_link"
            if not symlink_path.exists():
                symlink_path.symlink_to(project_dir)

            logger.info(f"Session linked to project category: {category}")

    def complete_session(self) -> None:
        """Mark session as completed"""
        self.update_metadata(status="completed")
        logger.info(f"Session completed: {self.session_id}")

    def get_session_summary(self) -> dict:
        """Get summary of current session"""
        return {
            "session_id": self.session_id,
            "path": str(self.session_path),
            "status": self.metadata.status,
            "files_count": len(self.metadata.files_created),
            "tokens_used": self.metadata.total_tokens_used,
            "created_at": self.metadata.created_at,
            "task_type": getattr(self.metadata, 'task_category', self.metadata.task_type)
        }

    @classmethod
    def list_sessions(cls, status: Optional[str] = None) -> List[dict]:
        """
        List all sessions with optional status filter

        Args:
            status: Filter by status (active, completed, archived)

        Returns:
            List of session summaries
        """
        sessions_dir = WORKSPACE_ROOT / "sessions"
        if not sessions_dir.exists():
            return []

        sessions = []
        for session_dir in sessions_dir.iterdir():
            if session_dir.is_dir():
                metadata_path = session_dir / ".metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            if status is None or metadata.get('status') == status:
                                sessions.append({
                                    'session_id': metadata.get('session_id'),
                                    'created_at': metadata.get('created_at'),
                                    'status': metadata.get('status'),
                                    'task_type': metadata.get('task_category', metadata.get('task_type')),
                                    'files_count': len(metadata.get('files_created', []))
                                })
                    except Exception as e:
                        logger.error(f"Failed to read session {session_dir.name}: {e}")

        # Sort by creation time (newest first)
        sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return sessions

    @classmethod
    def resume_session(cls, session_id: str) -> Optional['SessionManager']:
        """
        Resume an existing session

        Args:
            session_id: ID of session to resume

        Returns:
            SessionManager instance or None if session not found
        """
        session_dir = WORKSPACE_ROOT / "sessions" / session_id
        if not session_dir.exists():
            logger.error(f"Session not found: {session_id}")
            return None

        manager = cls.__new__(cls)
        manager.session_id = session_id
        manager.session_path = session_dir
        manager.use_enhanced = True  # Default to enhanced

        # Load existing metadata
        metadata = manager.load_metadata(session_id)
        if metadata:
            manager.metadata = metadata
            manager.metadata_class = type(metadata)
            logger.info(f"Resumed session: {session_id}")
            return manager

        return None

    def share_resource(
        self,
        file_path: str,
        resource_type: str = "auto",
        metadata: Optional[dict] = None
    ) -> Optional[Path]:
        """
        Share a resource from current session to shared directory

        Args:
            file_path: Path to file in current session
            resource_type: Type of resource (dataset/template/auto)
            metadata: Optional metadata for the resource

        Returns:
            Path to shared resource or None if not shared
        """
        # Lazy load shared resource manager
        if not self.shared_resource_manager:
            from app.utils.shared_resource_manager import SharedResourceManager
            self.shared_resource_manager = SharedResourceManager()

        source_path = Path(file_path)
        if not source_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        # Auto-detect resource type if needed
        if resource_type == "auto":
            # Check if it's a data file
            data_extensions = {'.csv', '.json', '.xlsx', '.xls', '.parquet', '.db'}
            if source_path.suffix.lower() in data_extensions:
                resource_type = "dataset"
            else:
                # Check if it should be shared
                content = source_path.read_text() if source_path.suffix in ['.py', '.md', '.txt'] else None
                if self.shared_resource_manager.should_share_resource(source_path, content):
                    resource_type = "template" if content else "dataset"
                else:
                    logger.debug(f"Resource doesn't meet sharing criteria: {file_path}")
                    return None

        # Share the resource
        try:
            if resource_type == "dataset":
                shared_path = self.shared_resource_manager.register_dataset(
                    name=source_path.stem,
                    source_path=source_path,
                    metadata=metadata,
                    session_id=self.session_id
                )
            elif resource_type == "template":
                content = source_path.read_text(encoding='utf-8')
                # Detect template type from extension
                template_types = {
                    '.py': 'code',
                    '.md': 'report',
                    '.json': 'config',
                    '.ipynb': 'jupyter'
                }
                template_type = template_types.get(source_path.suffix, 'general')

                shared_path = self.shared_resource_manager.register_template(
                    name=source_path.stem,
                    content=content,
                    template_type=template_type,
                    metadata=metadata,
                    session_id=self.session_id
                )
            else:
                logger.warning(f"Unknown resource type: {resource_type}")
                return None

            logger.info(f"Resource shared: {source_path.name} -> {shared_path}")
            return shared_path

        except Exception as e:
            logger.error(f"Failed to share resource: {e}")
            return None

    def use_shared_resource(self, resource_name: str, resource_type: str = "auto") -> Optional[Any]:
        """
        Use a shared resource in current session

        Args:
            resource_name: Name of the shared resource
            resource_type: Type of resource (dataset/template/auto)

        Returns:
            Path to dataset or template content, or None if not found
        """
        # Lazy load shared resource manager
        if not self.shared_resource_manager:
            from app.utils.shared_resource_manager import SharedResourceManager
            self.shared_resource_manager = SharedResourceManager()

        if resource_type == "auto":
            # Try dataset first, then template
            result = self.shared_resource_manager.get_dataset(resource_name)
            if result:
                return result
            result = self.shared_resource_manager.get_template(resource_name)
            if result:
                return result
        elif resource_type == "dataset":
            return self.shared_resource_manager.get_dataset(resource_name)
        elif resource_type == "template":
            return self.shared_resource_manager.get_template(resource_name)

        logger.warning(f"Shared resource not found: {resource_name}")
        return None