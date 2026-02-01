"""
Universal Problem Framework with Hot-Pluggable Domain Expertise

Architecture:
  schemas/
  ├── framework.yaml     # Core framework (stable)
  ├── routing.yaml       # Problem type routing configuration
  └── domains/           # Hot-pluggable domain expertise
      ├── travel.yaml
      ├── software.yaml
      └── *.yaml         # Drop files here to add domains

Philosophy:
- Core framework is stable (Context/Gap/Constraints/Deliverable)
- Domain expertise is hot-pluggable (add/remove files in domains/)
- Routing logic is configured in routing.yaml, not hardcoded
- LLM decides when to apply domain expertise
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from core.logger import log


@dataclass
class DomainExpertise:
    """Single domain expertise."""
    domain: str
    hints: List[str] = field(default_factory=list)
    expertise: str = ""


@dataclass
class RoutingConfig:
    """Configuration for problem type routing."""
    strategy: str = "llm_decision"
    routing_prompt: str = ""
    fallback_action: str = "use_framework_only"
    fallback_message: str = ""


@dataclass
class UniversalFramework:
    """
    Universal problem-solving framework with hot-pluggable domains.

    - framework: Core 4-element analysis structure
    - domains: Hot-loaded domain expertise from domains/*.yaml
    - routing: Configuration for problem type routing
    """
    framework: str = ""
    domains: Dict[str, DomainExpertise] = field(default_factory=dict)
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    version: str = "1.0"

    def get_framework(self) -> str:
        """Get the universal problem framework."""
        return self.framework.strip()

    def get_domain_expertise(self, domain: str) -> Optional[str]:
        """Get domain-specific expertise if available."""
        if domain in self.domains:
            return self.domains[domain].expertise
        return None

    def get_domain_hints(self, domain: str) -> List[str]:
        """Get hint keywords for a domain."""
        if domain in self.domains:
            return self.domains[domain].hints
        return []

    def list_domains(self) -> List[str]:
        """List available domain expertise."""
        return list(self.domains.keys())

    def get_domains_summary(self) -> str:
        """Get a summary of all domains for routing prompt."""
        lines = []
        for domain_name, domain in self.domains.items():
            hints_str = ", ".join(domain.hints[:5]) if domain.hints else "general"
            lines.append(f"- **{domain_name}**: hints=[{hints_str}]")
        return "\n".join(lines)

    def get_routing_prompt(self) -> str:
        """Get the routing prompt with available domains filled in."""
        if not self.routing.routing_prompt:
            return ""
        return self.routing.routing_prompt.format(
            available_domains=self.get_domains_summary()
        )

    def get_all_expertise(self) -> str:
        """Get all domain expertise combined (for context injection)."""
        parts = []
        for domain_name, domain in self.domains.items():
            if domain.expertise:
                parts.append(f"### {domain_name}\n{domain.expertise}")
        return "\n\n".join(parts)


class FrameworkLoader:
    """
    Loads the universal framework, routing config, and domain expertise.

    Structure:
      schemas/
      ├── framework.yaml     # Core framework
      ├── routing.yaml       # Routing configuration
      └── domains/           # Domain expertise (hot-pluggable)
          └── *.yaml
    """

    def __init__(self, schema_dir: Optional[Path] = None):
        if schema_dir is None:
            project_root = Path(__file__).parent.parent
            schema_dir = project_root / "schemas"

        self.schema_dir = Path(schema_dir)
        self._framework: Optional[UniversalFramework] = None
        self._load()

    def _load(self) -> None:
        """Load framework, routing, and all domain expertise."""
        framework_str = self._load_framework()
        routing = self._load_routing()
        domains = self._load_domains()

        self._framework = UniversalFramework(
            framework=framework_str,
            domains=domains,
            routing=routing,
            version="1.0"
        )

        log.debug(f"Loaded framework with {len(domains)} domains: {list(domains.keys())}")

    def _load_framework(self) -> str:
        """Load core framework from framework.yaml."""
        framework_path = self.schema_dir / "framework.yaml"

        if not framework_path.exists():
            log.warning(f"Framework not found: {framework_path}")
            return ""

        try:
            with open(framework_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data.get('framework', '')
        except Exception as e:
            log.error(f"Failed to load framework: {e}")
            return ""

    def _load_routing(self) -> RoutingConfig:
        """Load routing configuration from routing.yaml."""
        routing_path = self.schema_dir / "routing.yaml"

        if not routing_path.exists():
            log.debug(f"Routing config not found: {routing_path}")
            return RoutingConfig()

        try:
            with open(routing_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            fallback = data.get('fallback', {})
            return RoutingConfig(
                strategy=data.get('strategy', 'llm_decision'),
                routing_prompt=data.get('routing_prompt', ''),
                fallback_action=fallback.get('action', 'use_framework_only'),
                fallback_message=fallback.get('message', '')
            )
        except Exception as e:
            log.error(f"Failed to load routing: {e}")
            return RoutingConfig()

    def _load_domains(self) -> Dict[str, DomainExpertise]:
        """Load all domain expertise from domains/*.yaml."""
        domains_dir = self.schema_dir / "domains"
        domains = {}

        if not domains_dir.exists():
            log.debug(f"Domains directory not found: {domains_dir}")
            return domains

        for domain_file in domains_dir.glob("*.yaml"):
            try:
                with open(domain_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                if data and 'domain' in data:
                    domain_name = data['domain']
                    domains[domain_name] = DomainExpertise(
                        domain=domain_name,
                        hints=data.get('hints', []),
                        expertise=data.get('expertise', '')
                    )
                    log.debug(f"Loaded domain: {domain_name} from {domain_file.name}")

            except Exception as e:
                log.error(f"Failed to load domain {domain_file}: {e}")

        return domains

    def reload(self) -> None:
        """Hot-reload all configuration (call after adding new files)."""
        self._load()
        log.info(f"Reloaded framework with {len(self._framework.domains)} domains")

    @property
    def framework(self) -> UniversalFramework:
        """Get the loaded framework."""
        return self._framework

    def get_problem_framework(self) -> str:
        """Get the core problem analysis framework."""
        return self._framework.get_framework()

    def get_routing_prompt(self) -> str:
        """Get the routing prompt for LLM to determine domain."""
        return self._framework.get_routing_prompt()

    def get_domain_expertise(self, domain: str) -> Optional[str]:
        """Get domain-specific expertise."""
        return self._framework.get_domain_expertise(domain)

    def list_domains(self) -> List[str]:
        """List available domain expertise."""
        return self._framework.list_domains()


# Singleton
_loader: Optional[FrameworkLoader] = None


def get_framework_loader() -> FrameworkLoader:
    """Get singleton FrameworkLoader."""
    global _loader
    if _loader is None:
        _loader = FrameworkLoader()
    return _loader


def reset_framework_loader() -> None:
    """Reset singleton (for testing or hot-reload)."""
    global _loader
    _loader = None


def reload_domains() -> None:
    """Hot-reload all configuration files."""
    loader = get_framework_loader()
    loader.reload()


def get_problem_framework() -> str:
    """
    Get the universal problem analysis framework.

    Core structure (applies to any problem):
    - Context: current state
    - Gap: problem definition
    - Constraints: boundaries
    - Deliverable: expected output
    """
    return get_framework_loader().get_problem_framework()


def get_routing_prompt() -> str:
    """
    Get the routing prompt for LLM to determine which domain to use.

    This prompt includes available domains and hints.
    LLM uses this to decide which domain expertise to inject.
    """
    return get_framework_loader().get_routing_prompt()


def get_domain_expertise(domain: str) -> Optional[str]:
    """
    Get domain-specific expertise if available.

    Domain knowledge is hot-pluggable - add *.yaml files to schemas/domains/
    """
    return get_framework_loader().get_domain_expertise(domain)


def list_available_domains() -> List[str]:
    """List all available domain expertise."""
    return get_framework_loader().list_domains()


# ============================================================
# Backward compatibility layer
# ============================================================

@dataclass
class DomainSchema:
    """
    DEPRECATED: Use UniversalFramework instead.

    Kept for backward compatibility during migration.
    """
    domain: str
    detect: List[str] = field(default_factory=list)
    guidance: str = ""

    def matches(self, prompt: str) -> bool:
        """DEPRECATED: No longer using keyword matching."""
        return False

    def get_guidance(self) -> str:
        """Return combined framework + domain expertise."""
        loader = get_framework_loader()
        parts = [loader.get_problem_framework()]

        # Try to get domain expertise
        expertise = loader.get_domain_expertise(self.domain)
        if expertise:
            parts.append(f"\n## Domain Expertise\n{expertise}")

        return "\n".join(parts)

    def get_okr_prompt(self) -> str:
        """Alias for get_guidance()."""
        return self.get_guidance()


class SchemaLoader:
    """
    DEPRECATED: Use FrameworkLoader instead.

    Kept for backward compatibility.
    """

    def __init__(self, schema_dir: Optional[Path] = None):
        self._framework_loader = get_framework_loader()

    def match(self, prompt: str) -> Optional[DomainSchema]:
        """
        DEPRECATED: Returns universal framework for any prompt.

        No keyword matching - always returns the universal framework.
        """
        return DomainSchema(
            domain="universal",
            detect=[],
            guidance=self._framework_loader.get_problem_framework()
        )

    def list_domains(self) -> List[str]:
        """List available domain expertise."""
        return self._framework_loader.list_domains()


def get_schema_loader() -> SchemaLoader:
    """DEPRECATED: Use get_framework_loader() instead."""
    return SchemaLoader()


def reset_schema_loader() -> None:
    """DEPRECATED: Use reset_framework_loader() instead."""
    reset_framework_loader()


def detect_schema(prompt: str) -> Optional[DomainSchema]:
    """
    DEPRECATED: No longer detecting schemas by keyword.

    Returns universal framework for any prompt.
    """
    return get_schema_loader().match(prompt)
