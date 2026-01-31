"""
Domain Schema System - OKR-Based

Philosophy: Define goals, not paths. Let AI decide how to achieve them.

Each schema defines:
- domain: identifier
- detect: keywords to match
- objective: what to achieve
- key_results: measurable outcomes (checklists)
- constraints: hard rules
- success_criteria: when is it done
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from core.logger import log


@dataclass
class DomainSchema:
    """
    OKR-based domain schema.

    Defines WHAT to achieve, not HOW to achieve it.
    AI decides the path, schema defines the destination.
    """
    domain: str
    detect: List[str]
    objective: str = ""
    key_results: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    success_criteria: str = ""
    version: str = "1.0"

    def matches(self, prompt: str) -> bool:
        """Check if prompt matches this domain."""
        prompt_lower = prompt.lower()
        return any(kw.lower() in prompt_lower for kw in self.detect)

    def get_okr_prompt(self) -> str:
        """
        Generate OKR prompt for injection.

        This tells AI WHAT to achieve, not HOW.
        """
        parts = []

        # Objective
        if self.objective:
            parts.append(f"## OBJECTIVE\n{self.objective.strip()}")

        # Key Results
        if self.key_results:
            parts.append("\n## KEY RESULTS (Must be achieved)")
            for kr_name, kr_data in self.key_results.items():
                if isinstance(kr_data, dict):
                    desc = kr_data.get('description', '')
                    checklist = kr_data.get('checklist', [])
                    parts.append(f"\n### {kr_name.replace('_', ' ').title()}")
                    if desc:
                        parts.append(f"{desc}")
                    for item in checklist:
                        parts.append(f"  - [ ] {item}")

        # Constraints
        if self.constraints:
            parts.append("\n## CONSTRAINTS (Must not violate)")
            for c in self.constraints:
                parts.append(f"  - {c}")

        # Success Criteria
        if self.success_criteria:
            parts.append(f"\n## SUCCESS CRITERIA\n{self.success_criteria.strip()}")

        return "\n".join(parts)


class SchemaLoader:
    """
    Loads OKR-based domain schemas from YAML files.

    Usage:
        loader = SchemaLoader()
        schema = loader.match("規劃旅遊 4天3夜")
        if schema:
            print(schema.get_okr_prompt())  # Goals and constraints
    """

    def __init__(self, schema_dir: Optional[Path] = None):
        if schema_dir is None:
            project_root = Path(__file__).parent.parent
            schema_dir = project_root / "schemas"

        self.schema_dir = Path(schema_dir)
        self._schemas: List[DomainSchema] = []
        self._load_all()

    def _load_all(self) -> None:
        """Load all schema files."""
        if not self.schema_dir.exists():
            log.debug(f"Schema directory not found: {self.schema_dir}")
            return

        for schema_file in self.schema_dir.glob("*.yaml"):
            try:
                schema = self._load_file(schema_file)
                if schema:
                    self._schemas.append(schema)
                    log.debug(f"Loaded schema: {schema.domain} v{schema.version}")
            except Exception as e:
                log.error(f"Failed to load {schema_file}: {e}")

    def _load_file(self, path: Path) -> Optional[DomainSchema]:
        """Load a single schema file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'domain' not in data:
            return None

        return DomainSchema(
            domain=data.get('domain', 'unknown'),
            detect=data.get('detect', []),
            objective=data.get('objective', ''),
            key_results=data.get('key_results', {}),
            constraints=data.get('constraints', []),
            success_criteria=data.get('success_criteria', ''),
            version=data.get('version', '1.0'),
        )

    def match(self, prompt: str) -> Optional[DomainSchema]:
        """Find matching schema for a prompt."""
        for schema in self._schemas:
            if schema.matches(prompt):
                return schema
        return None

    def list_domains(self) -> List[str]:
        """List all loaded domains."""
        return [s.domain for s in self._schemas]


# Singleton
_loader: Optional[SchemaLoader] = None


def get_schema_loader() -> SchemaLoader:
    """Get singleton SchemaLoader."""
    global _loader
    if _loader is None:
        _loader = SchemaLoader()
    return _loader


def reset_schema_loader() -> None:
    """Reset singleton (for testing)."""
    global _loader
    _loader = None


def detect_schema(prompt: str) -> Optional[DomainSchema]:
    """
    Convenience function to find schema for a prompt.

    Usage:
        schema = detect_schema("規劃旅遊")
        if schema:
            print(schema.get_okr_prompt())  # OKR goals
    """
    return get_schema_loader().match(prompt)
