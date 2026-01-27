"""Shared resource management for cross-session assets"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.config import WORKSPACE_ROOT
from app.logger import logger


class SharedResourceManager:
    """Manages shared resources across sessions"""

    def __init__(self):
        """Initialize shared resource manager"""
        self.shared_root = WORKSPACE_ROOT / "shared"
        self.datasets_dir = self.shared_root / "datasets"
        self.templates_dir = self.shared_root / "templates"
        self._ensure_directories()
        self._load_registry()

    def _ensure_directories(self) -> None:
        """Ensure shared directories exist"""
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Shared directories initialized at {self.shared_root}")

    def _load_registry(self) -> None:
        """Load resource registry"""
        self.registry_path = self.shared_root / ".registry.json"
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                self.registry = json.load(f)
        else:
            self.registry = {
                "datasets": {},
                "templates": {},
                "created_at": datetime.now().isoformat()
            }
            self._save_registry()

    def _save_registry(self) -> None:
        """Save resource registry"""
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def register_dataset(
        self,
        name: str,
        source_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Path:
        """
        Register a dataset as shared resource

        Args:
            name: Dataset name
            source_path: Path to source file
            metadata: Optional metadata
            session_id: Session that created this dataset

        Returns:
            Path to shared dataset
        """
        # Create unique dataset directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dataset_name = f"{name}_{timestamp}" if not name.endswith(timestamp) else name
        dataset_path = self.datasets_dir / dataset_name

        # Copy file or directory to shared location
        if source_path.is_dir():
            shutil.copytree(source_path, dataset_path, dirs_exist_ok=True)
        else:
            dataset_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dataset_path)

        # Register in registry
        self.registry["datasets"][dataset_name] = {
            "name": name,
            "path": str(dataset_path),
            "created_at": datetime.now().isoformat(),
            "session_id": session_id,
            "metadata": metadata or {},
            "usage_count": 0,
            "last_accessed": None
        }
        self._save_registry()

        logger.info(f"Dataset registered: {dataset_name}")
        return dataset_path

    def register_template(
        self,
        name: str,
        content: str,
        template_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Path:
        """
        Register a template as shared resource

        Args:
            name: Template name
            content: Template content
            template_type: Type of template (code, report, config, etc.)
            metadata: Optional metadata
            session_id: Session that created this template

        Returns:
            Path to saved template
        """
        # Determine file extension based on type
        extensions = {
            "code": ".py",
            "report": ".md",
            "config": ".json",
            "jupyter": ".ipynb",
            "general": ".txt"
        }
        ext = extensions.get(template_type, ".txt")

        # Create template file
        template_filename = f"{name}{ext}"
        template_path = self.templates_dir / template_type / template_filename
        template_path.parent.mkdir(parents=True, exist_ok=True)

        # Save template content
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Register in registry
        template_key = f"{template_type}/{template_filename}"
        self.registry["templates"][template_key] = {
            "name": name,
            "path": str(template_path),
            "type": template_type,
            "created_at": datetime.now().isoformat(),
            "session_id": session_id,
            "metadata": metadata or {},
            "usage_count": 0,
            "last_used": None
        }
        self._save_registry()

        logger.info(f"Template registered: {template_key}")
        return template_path

    def get_dataset(self, name: str) -> Optional[Path]:
        """
        Get path to a shared dataset

        Args:
            name: Dataset name (can be partial match)

        Returns:
            Path to dataset or None if not found
        """
        # Find matching dataset
        for dataset_name, info in self.registry["datasets"].items():
            if name in dataset_name or name == info["name"]:
                # Update usage statistics
                info["usage_count"] += 1
                info["last_accessed"] = datetime.now().isoformat()
                self._save_registry()

                path = Path(info["path"])
                if path.exists():
                    logger.debug(f"Dataset accessed: {dataset_name}")
                    return path
                else:
                    logger.warning(f"Dataset file missing: {dataset_name}")

        return None

    def get_template(self, name: str, template_type: Optional[str] = None) -> Optional[str]:
        """
        Get content of a shared template

        Args:
            name: Template name
            template_type: Optional type filter

        Returns:
            Template content or None if not found
        """
        # Find matching template
        for template_key, info in self.registry["templates"].items():
            if name in info["name"] and (not template_type or info["type"] == template_type):
                # Update usage statistics
                info["usage_count"] += 1
                info["last_used"] = datetime.now().isoformat()
                self._save_registry()

                path = Path(info["path"])
                if path.exists():
                    logger.debug(f"Template accessed: {template_key}")
                    return path.read_text(encoding='utf-8')
                else:
                    logger.warning(f"Template file missing: {template_key}")

        return None

    def list_datasets(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available datasets

        Args:
            session_id: Optional filter by session

        Returns:
            List of dataset information
        """
        datasets = []
        for name, info in self.registry["datasets"].items():
            if not session_id or info.get("session_id") == session_id:
                datasets.append({
                    "name": info["name"],
                    "key": name,
                    "created_at": info["created_at"],
                    "usage_count": info["usage_count"],
                    "metadata": info.get("metadata", {})
                })
        return datasets

    def list_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available templates

        Args:
            template_type: Optional type filter

        Returns:
            List of template information
        """
        templates = []
        for key, info in self.registry["templates"].items():
            if not template_type or info["type"] == template_type:
                templates.append({
                    "name": info["name"],
                    "key": key,
                    "type": info["type"],
                    "created_at": info["created_at"],
                    "usage_count": info["usage_count"],
                    "metadata": info.get("metadata", {})
                })
        return templates

    def should_share_resource(self, file_path: Path, content: Optional[str] = None) -> bool:
        """
        Determine if a resource should be shared

        Criteria for sharing:
        1. Large datasets (>1MB)
        2. Common file types (CSV, JSON, Excel, etc.)
        3. Template-like content (contains placeholders)
        4. Reusable code modules

        Args:
            file_path: Path to file
            content: Optional file content for analysis

        Returns:
            True if resource should be shared
        """
        # Check file size (share if > 1MB)
        if file_path.exists() and file_path.stat().st_size > 1024 * 1024:
            return True

        # Check common data formats
        data_extensions = {'.csv', '.json', '.xlsx', '.xls', '.parquet', '.db', '.sqlite'}
        if file_path.suffix.lower() in data_extensions:
            return True

        # Check for template patterns if content provided
        if content:
            template_indicators = [
                '{{', '}}',  # Jinja2/Mustache style
                '${', '}',   # Shell/JS template literal style
                '<#', '#>',  # Template tags
                'TODO:', 'FIXME:', 'XXX:',  # Development markers
                '__NAME__', '__DATE__', '__VERSION__'  # Common placeholders
            ]
            if any(indicator in content for indicator in template_indicators):
                return True

        # Check for reusable code patterns
        code_patterns = ['class Base', 'def template_', 'abstract class', 'interface ']
        if content and any(pattern in content for pattern in code_patterns):
            return True

        return False

    def cleanup_unused(self, days: int = 30) -> int:
        """
        Clean up unused shared resources

        Args:
            days: Remove resources not accessed for this many days

        Returns:
            Number of resources removed
        """
        from datetime import timedelta

        removed_count = 0
        cutoff_date = datetime.now() - timedelta(days=days)

        # Check datasets
        for name in list(self.registry["datasets"].keys()):
            info = self.registry["datasets"][name]
            last_accessed = info.get("last_accessed")

            if not last_accessed or datetime.fromisoformat(last_accessed) < cutoff_date:
                # Remove file
                path = Path(info["path"])
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()

                # Remove from registry
                del self.registry["datasets"][name]
                removed_count += 1
                logger.info(f"Removed unused dataset: {name}")

        # Check templates (only remove if never used)
        for key in list(self.registry["templates"].keys()):
            info = self.registry["templates"][key]

            if info["usage_count"] == 0:
                created_at = datetime.fromisoformat(info["created_at"])
                if created_at < cutoff_date:
                    # Remove file
                    path = Path(info["path"])
                    if path.exists():
                        path.unlink()

                    # Remove from registry
                    del self.registry["templates"][key]
                    removed_count += 1
                    logger.info(f"Removed unused template: {key}")

        self._save_registry()
        return removed_count