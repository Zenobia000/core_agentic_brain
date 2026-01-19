"""
Control Plane - 控制平面
========================

負責治理、策略和可觀測性。
- Policy: RBAC/ABAC + 審批
- Ops: Observability + Cost + SLO + Audit
- Governance: Versioning + Change Mgmt
"""

from __future__ import annotations
import json
import uuid
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field


# =============================================================================
# Policy Plane
# =============================================================================

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Permission(BaseModel):
    name: str
    resource: str
    actions: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    
    def allows(self, action: str) -> bool:
        return "*" in self.actions or action in self.actions


class Role(BaseModel):
    name: str
    permissions: List[Permission] = Field(default_factory=list)
    parent_roles: List[str] = Field(default_factory=list)
    
    def has_permission(self, resource: str, action: str) -> bool:
        return any(p.resource == resource and p.allows(action) for p in self.permissions)


class Policy(BaseModel):
    name: str
    conditions: Dict[str, Any] = Field(default_factory=dict)
    effect: str = "allow"
    applicable_roles: List[str] = Field(default_factory=list)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        for key, expected in self.conditions.items():
            if context.get(key) != expected:
                return False
        return True


class ApprovalRequest(BaseModel):
    request_id: str
    requester: str
    action: str
    resource: str
    reason: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)


class PolicyEngine(BaseModel):
    """策略引擎 - RBAC/ABAC"""
    
    roles: Dict[str, Role] = Field(default_factory=dict)
    policies: List[Policy] = Field(default_factory=list)
    tool_whitelist: Set[str] = Field(default_factory=set)
    tool_blacklist: Set[str] = Field(default_factory=set)
    tool_risk_levels: Dict[str, RiskLevel] = Field(default_factory=dict)
    pending_approvals: Dict[str, ApprovalRequest] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_role(self, role: Role) -> None:
        self.roles[role.name] = role
    
    def check_permission(self, role_name: str, resource: str, action: str) -> tuple[bool, Optional[str]]:
        role = self.roles.get(role_name)
        if not role:
            return False, f"Role '{role_name}' not found"
        if role.has_permission(resource, action):
            return True, None
        return False, f"Permission denied for {action} on {resource}"
    
    def is_tool_allowed(self, tool_name: str) -> tuple[bool, Optional[str]]:
        if tool_name in self.tool_blacklist:
            return False, f"Tool '{tool_name}' is blacklisted"
        if self.tool_whitelist and tool_name not in self.tool_whitelist:
            return False, f"Tool '{tool_name}' not in whitelist"
        return True, None
    
    def get_tool_risk_level(self, tool_name: str) -> RiskLevel:
        return self.tool_risk_levels.get(tool_name, RiskLevel.LOW)
    
    @classmethod
    def create_default(cls) -> "PolicyEngine":
        engine = cls()
        engine.add_role(Role(name="admin", permissions=[Permission(name="all", resource="*", actions=["*"])]))
        engine.add_role(Role(name="agent", permissions=[
            Permission(name="use_tools", resource="tool", actions=["use"]),
            Permission(name="read_files", resource="file", actions=["read"]),
        ]))
        engine.tool_risk_levels = {"bash": RiskLevel.HIGH, "python_execute": RiskLevel.MEDIUM}
        return engine


# =============================================================================
# Ops Plane
# =============================================================================

class SpanType(str, Enum):
    TASK = "task"
    PLAN = "plan"
    TOOL_CALL = "tool_call"
    LLM_CALL = "llm_call"


class Span(BaseModel):
    span_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str
    name: str
    span_type: SpanType
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Any] = None
    status: str = "running"
    error: Optional[str] = None
    
    def end(self, output: Any = None, error: Optional[str] = None) -> None:
        self.end_time = datetime.now()
        self.status = "failed" if error else "completed"
        self.error = error
        if output:
            self.output_data = output


class Trace(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    spans: List[Span] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def create_span(self, name: str, span_type: SpanType, input_data: Optional[Dict] = None) -> Span:
        span = Span(trace_id=self.trace_id, name=name, span_type=span_type, input_data=input_data)
        self.spans.append(span)
        return span
    
    def end(self) -> None:
        self.end_time = datetime.now()


class CostRecord(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0
    model: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class CostTracker(BaseModel):
    records: List[CostRecord] = Field(default_factory=list)
    budget_limit_usd: Optional[float] = None
    
    pricing: Dict[str, Dict[str, float]] = Field(default_factory=lambda: {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    })
    
    def record(self, input_tokens: int, output_tokens: int, model: str) -> CostRecord:
        pricing = self.pricing.get(model, {"input": 0.01, "output": 0.03})
        cost = (input_tokens / 1000) * pricing["input"] + (output_tokens / 1000) * pricing["output"]
        
        rec = CostRecord(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=cost,
            model=model
        )
        self.records.append(rec)
        return rec
    
    def get_total_cost(self) -> float:
        return sum(r.estimated_cost_usd for r in self.records)
    
    def is_over_budget(self) -> bool:
        return self.budget_limit_usd is not None and self.get_total_cost() > self.budget_limit_usd


class AuditLog(BaseModel):
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_name: str
    actor: str
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class OpsPlane(BaseModel):
    """維運平面 - 可觀測性"""
    
    traces: Dict[str, Trace] = Field(default_factory=dict)
    current_trace_id: Optional[str] = None
    cost_tracker: CostTracker = Field(default_factory=CostTracker)
    audit_logs: List[AuditLog] = Field(default_factory=list)
    storage_path: Optional[Path] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def start_trace(self, name: str, metadata: Optional[Dict] = None) -> Trace:
        trace = Trace(name=name, metadata=metadata or {})
        self.traces[trace.trace_id] = trace
        self.current_trace_id = trace.trace_id
        return trace
    
    def get_current_trace(self) -> Optional[Trace]:
        return self.traces.get(self.current_trace_id) if self.current_trace_id else None
    
    def end_trace(self, trace_id: Optional[str] = None) -> None:
        tid = trace_id or self.current_trace_id
        if tid and tid in self.traces:
            self.traces[tid].end()
    
    def record_cost(self, input_tokens: int, output_tokens: int, model: str) -> CostRecord:
        return self.cost_tracker.record(input_tokens, output_tokens, model)
    
    def log_audit(self, event_type: str, event_name: str, actor: str, success: bool = True, error: Optional[str] = None) -> AuditLog:
        log = AuditLog(event_type=event_type, event_name=event_name, actor=actor, success=success, error_message=error)
        self.audit_logs.append(log)
        return log
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            "traces_count": len(self.traces),
            "total_cost_usd": self.cost_tracker.get_total_cost(),
            "audit_logs_count": len(self.audit_logs),
        }


# =============================================================================
# Governance Plane
# =============================================================================

class AssetType(str, Enum):
    PROMPT = "prompt"
    SKILL = "skill"
    POLICY = "policy"


class AssetStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class VersionedAsset(BaseModel):
    asset_id: str
    asset_type: AssetType
    name: str
    content: Any
    version: str = "1.0.0"
    status: AssetStatus = AssetStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    
    def bump_version(self, bump_type: str = "patch") -> str:
        parts = self.version.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        if bump_type == "major":
            major, minor, patch = major + 1, 0, 0
        elif bump_type == "minor":
            minor, patch = minor + 1, 0
        else:
            patch += 1
        self.version = f"{major}.{minor}.{patch}"
        return self.version
    
    def publish(self) -> None:
        self.status = AssetStatus.ACTIVE


class GovernancePlane(BaseModel):
    """治理平面 - 版本控制"""
    
    assets: Dict[str, Dict[str, VersionedAsset]] = Field(default_factory=dict)
    version_history: Dict[str, List[VersionedAsset]] = Field(default_factory=dict)
    
    def register_asset(self, asset_type: AssetType, name: str, content: Any) -> VersionedAsset:
        asset_id = f"{asset_type.value}_{name}_{uuid.uuid4().hex[:8]}"
        asset = VersionedAsset(asset_id=asset_id, asset_type=asset_type, name=name, content=content)
        
        if asset_type.value not in self.assets:
            self.assets[asset_type.value] = {}
        self.assets[asset_type.value][asset_id] = asset
        self.version_history[asset_id] = [asset.model_copy(deep=True)]
        return asset
    
    def get_asset(self, asset_id: str) -> Optional[VersionedAsset]:
        for assets_by_type in self.assets.values():
            if asset_id in assets_by_type:
                return assets_by_type[asset_id]
        return None
    
    def update_asset(self, asset_id: str, content: Any, bump_type: str = "patch") -> Optional[VersionedAsset]:
        asset = self.get_asset(asset_id)
        if asset:
            self.version_history[asset_id].append(asset.model_copy(deep=True))
            asset.content = content
            asset.bump_version(bump_type)
        return asset
    
    def register_prompt(self, name: str, content: str) -> VersionedAsset:
        return self.register_asset(AssetType.PROMPT, name, content)
    
    def get_statistics(self) -> Dict[str, Any]:
        total = sum(len(assets) for assets in self.assets.values())
        return {"total_assets": total, "by_type": {k: len(v) for k, v in self.assets.items()}}


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Policy
    "RiskLevel", "Permission", "Role", "Policy", "ApprovalRequest", "PolicyEngine",
    # Ops
    "SpanType", "Span", "Trace", "CostRecord", "CostTracker", "AuditLog", "OpsPlane",
    # Governance
    "AssetType", "AssetStatus", "VersionedAsset", "GovernancePlane",
]
