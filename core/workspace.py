"""
Workspace Manager - Structured artifact management
Linus: "Simple tools that do one thing well"

Provides isolated run directories for each execution, ensuring:
- Security: Tools operate within sandboxed directories
- Traceability: All artifacts linked to specific run_id
- Reproducibility: Input/output clearly separated
"""

from pathlib import Path
from typing import Optional, Dict, Any
import os

from core.logger import logger


class WorkspaceManager:
    """Manages structured workspace directories for execution runs."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize WorkspaceManager.

        Args:
            config: Configuration dictionary. Expected keys:
                - workspace.root: Root directory for workspace (default: workspace/)
        """
        self.config = config or {}
        self._root = self._resolve_root()

    def _resolve_root(self) -> Path:
        """Resolve workspace root from config or environment."""
        # Priority: config > environment > default
        root = None

        # Check nested config structure
        if self.config:
            workspace_config = self.config.get("workspace", {})
            if isinstance(workspace_config, dict):
                root = workspace_config.get("root")
            elif isinstance(workspace_config, str):
                root = workspace_config

        # Fallback to environment
        if not root:
            root = os.getenv("WORKSPACE_ROOT", "workspace")

        path = Path(root)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def root(self) -> Path:
        """Get workspace root directory."""
        return self._root

    def create_run_context(self, run_id: str) -> Path:
        """
        Create isolated directory structure for a specific run.

        Args:
            run_id: Unique identifier for this execution run

        Returns:
            Path to the run's workspace directory

        Directory structure created:
            workspace/runs/{run_id}/
                input/   - Initial files for the task
                output/  - Final artifacts produced
                temp/    - Intermediate working files
        """
        run_path = self._root / "runs" / run_id

        # Create standard subdirectories
        subdirs = ["input", "output", "temp"]
        for subdir in subdirs:
            (run_path / subdir).mkdir(parents=True, exist_ok=True)

        logger.debug(f"Created workspace context: {run_path}")
        return run_path

    def get_run_path(self, run_id: str) -> Optional[Path]:
        """
        Get existing run directory path.

        Args:
            run_id: Unique identifier for the execution run

        Returns:
            Path to run directory if exists, None otherwise
        """
        run_path = self._root / "runs" / run_id
        return run_path if run_path.exists() else None

    def resolve_path(
        self,
        workspace_path: Path,
        filename: str,
        subdir: str = "output"
    ) -> Path:
        """
        Resolve a safe path within the workspace.

        Args:
            workspace_path: Run's workspace directory
            filename: Relative filename
            subdir: Target subdirectory (input/output/temp)

        Returns:
            Absolute path within the workspace

        Raises:
            ValueError: If path escapes workspace bounds
        """
        # Normalize and validate subdir
        if subdir not in ("input", "output", "temp"):
            subdir = "output"

        target = workspace_path / subdir / filename

        # Security: Ensure path doesn't escape workspace
        try:
            target.resolve().relative_to(workspace_path.resolve())
        except ValueError:
            raise ValueError(
                f"Path '{filename}' escapes workspace bounds"
            )

        return target

    def find_file(
        self,
        workspace_path: Path,
        filename: str
    ) -> Optional[Path]:
        """
        Find a file in workspace, searching input > output > temp.

        Args:
            workspace_path: Run's workspace directory
            filename: Relative filename to find

        Returns:
            Path to found file, None if not found
        """
        search_order = ["input", "output", "temp"]

        for subdir in search_order:
            candidate = workspace_path / subdir / filename
            if candidate.exists():
                return candidate

        return None

    def cleanup_run(self, run_id: str, keep_output: bool = True) -> bool:
        """
        Clean up a run's workspace.

        Args:
            run_id: Run identifier to clean
            keep_output: If True, preserve output/ directory

        Returns:
            True if cleanup succeeded
        """
        import shutil

        run_path = self._root / "runs" / run_id
        if not run_path.exists():
            return True

        try:
            if keep_output:
                # Remove only input and temp
                for subdir in ["input", "temp"]:
                    subdir_path = run_path / subdir
                    if subdir_path.exists():
                        shutil.rmtree(subdir_path)
                logger.debug(f"Cleaned up workspace (kept output): {run_id}")
            else:
                # Remove entire run directory
                shutil.rmtree(run_path)
                logger.debug(f"Cleaned up workspace completely: {run_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup workspace {run_id}: {e}")
            return False
