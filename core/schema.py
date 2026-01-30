"""
Domain Schema System - CrewAI Style (Simplified)

Linus: "10 lines of config, not 150"

Each schema defines:
- domain: name
- detect: keywords to match
- intake: what to ask before starting
- expected_output: what the output should contain
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from core.logger import log


@dataclass
class DomainSchema:
    """
    Simplified domain schema - CrewAI style.

    Only 4 fields:
    - domain: identifier
    - detect: keywords for matching
    - intake: prompt for gathering requirements
    - expected_output: prompt for output format
    """
    domain: str
    detect: List[str]
    intake: str
    expected_output: str
    version: str = "1.0"

    def matches(self, prompt: str) -> bool:
        """Check if prompt matches this domain."""
        prompt_lower = prompt.lower()
        return any(kw.lower() in prompt_lower for kw in self.detect)

    def get_intake_prompt(self) -> str:
        """Get the intake requirements prompt."""
        return self.intake.strip()

    def get_output_prompt(self) -> str:
        """Get the expected output prompt."""
        return self.expected_output.strip()


class SchemaLoader:
    """
    Loads simplified domain schemas from YAML files.

    Usage:
        loader = SchemaLoader()
        schema = loader.match("規劃旅遊 4天3夜")
        if schema:
            print(schema.intake)  # What to ask user
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
                    log.debug(f"Loaded schema: {schema.domain}")
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
            intake=data.get('intake', ''),
            expected_output=data.get('expected_output', ''),
            version=data.get('version', '1.0')
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


def detect_schema(prompt: str) -> Optional[DomainSchema]:
    """
    Convenience function to find schema for a prompt.

    Usage:
        schema = detect_schema("規劃旅遊")
        if schema:
            print(schema.intake)  # "Before planning, confirm..."
    """
    return get_schema_loader().match(prompt)
