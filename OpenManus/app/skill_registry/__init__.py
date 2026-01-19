"""
Skill Registry - 技能註冊中心
==============================

技能的註冊、發現和管理。
"""

from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class SkillCategory(str, Enum):
    CODE_EXECUTION = "code_execution"
    FILE_OPERATION = "file_operation"
    WEB_INTERACTION = "web_interaction"
    DATA_ANALYSIS = "data_analysis"
    SEARCH = "search"
    UTILITY = "utility"
    CUSTOM = "custom"


class SkillSchema(BaseModel):
    """技能 Schema"""
    input_parameters: Dict[str, Any] = Field(default_factory=dict)
    required_parameters: List[str] = Field(default_factory=list)
    output_type: str = "any"
    
    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        for param in self.required_parameters:
            if param not in input_data:
                return False, f"Missing required parameter: {param}"
        return True, None


class SkillTest(BaseModel):
    """技能測試案例"""
    name: str
    input_data: Dict[str, Any]
    expected_output: Optional[Any] = None
    skip: bool = False


class Skill(BaseModel):
    """技能定義"""
    skill_id: str
    name: str
    description: str = ""
    category: SkillCategory = SkillCategory.CUSTOM
    version: str = "1.0.0"
    schema: SkillSchema = Field(default_factory=SkillSchema)
    tool_class: Optional[str] = None
    tests: List[SkillTest] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    
    def to_openai_function(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.schema.input_parameters,
                "required": self.schema.required_parameters,
            }
        }


class SkillRegistry(BaseModel):
    """技能註冊中心"""
    
    skills: Dict[str, Skill] = Field(default_factory=dict)
    tool_instances: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    def register(
        self,
        name: str,
        description: str = "",
        category: SkillCategory = SkillCategory.CUSTOM,
        schema: Optional[SkillSchema] = None,
        tool_class: Optional[str] = None,
    ) -> Skill:
        skill_id = f"skill_{name}_{uuid.uuid4().hex[:8]}"
        skill = Skill(
            skill_id=skill_id,
            name=name,
            description=description,
            category=category,
            schema=schema or SkillSchema(),
            tool_class=tool_class,
        )
        self.skills[skill_id] = skill
        return skill
    
    def register_from_tool(self, tool_instance: Any) -> Optional[Skill]:
        """從 OpenManus Tool 實例註冊"""
        try:
            name = getattr(tool_instance, "name", tool_instance.__class__.__name__)
            description = getattr(tool_instance, "description", "")
            
            # 判斷分類
            category = SkillCategory.CUSTOM
            name_lower = name.lower()
            if "search" in name_lower:
                category = SkillCategory.SEARCH
            elif "file" in name_lower:
                category = SkillCategory.FILE_OPERATION
            elif "python" in name_lower or "bash" in name_lower:
                category = SkillCategory.CODE_EXECUTION
            elif "browser" in name_lower:
                category = SkillCategory.WEB_INTERACTION
            
            skill = self.register(name=name, description=description, category=category, tool_class=tool_instance.__class__.__name__)
            self.tool_instances[skill.skill_id] = tool_instance
            return skill
        except Exception as e:
            print(f"Warning: Failed to register tool: {e}")
            return None
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        return self.skills.get(skill_id)
    
    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        for skill in self.skills.values():
            if skill.name == name:
                return skill
        return None
    
    def list_skills(self, category: Optional[SkillCategory] = None, enabled_only: bool = True) -> List[Skill]:
        skills = list(self.skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        if enabled_only:
            skills = [s for s in skills if s.enabled]
        return skills
    
    def search_skills(self, query: str) -> List[Skill]:
        query_lower = query.lower()
        return [s for s in self.skills.values() if query_lower in s.name.lower() or query_lower in s.description.lower()]
    
    async def execute_skill(self, skill_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        skill = self.get_skill(skill_id)
        if not skill:
            return {"success": False, "error": f"Skill not found: {skill_id}"}
        if not skill.enabled:
            return {"success": False, "error": f"Skill is disabled: {skill.name}"}
        
        valid, error = skill.schema.validate_input(arguments)
        if not valid:
            return {"success": False, "error": error}
        
        tool = self.tool_instances.get(skill_id)
        if tool and hasattr(tool, "execute"):
            try:
                result = await tool.execute(**arguments)
                return {"success": True, "data": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "No tool instance available"}
    
    def discover_from_tool_collection(self, tool_collection: Any) -> int:
        count = 0
        if hasattr(tool_collection, "tools"):
            for tool in tool_collection.tools:
                if self.register_from_tool(tool):
                    count += 1
        return count
    
    def to_openai_tools(self) -> List[Dict[str, Any]]:
        return [{"type": "function", "function": s.to_openai_function()} for s in self.list_skills()]
    
    def get_statistics(self) -> Dict[str, Any]:
        skills = list(self.skills.values())
        by_category: Dict[str, int] = {}
        for s in skills:
            by_category[s.category.value] = by_category.get(s.category.value, 0) + 1
        return {"total_skills": len(skills), "by_category": by_category}


__all__ = ["SkillCategory", "SkillSchema", "SkillTest", "Skill", "SkillRegistry"]
