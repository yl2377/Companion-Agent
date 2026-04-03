"""Skill系统 - 基类定义"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import asyncio


@dataclass
class SkillContext:
    """Skill执行上下文"""
    user_input: str
    user_id: str
    profile: Dict = field(default_factory=dict)
    memory: Any = None
    llm: Any = None
    database: Any = None
    config: Any = None


@dataclass
class SkillResult:
    """Skill执行结果"""
    success: bool
    content: str
    should_respond: bool = True  # 是否需要Agent生成回复
    action: Optional[str] = None  # 执行的具体动作


class BaseSkill(ABC):
    """Skill基类"""

    name: str = "base_skill"  # Skill名称
    description: str = "基础Skill"  # 功能描述
    version: str = "1.0.0"  # 版本号
    category: str = "general"  # 分类

    @abstractmethod
    async def should_activate(self, user_input: str, context: SkillContext) -> bool:
        """
        判断是否应该激活此Skill

        Args:
            user_input: 用户输入
            context: 执行上下文

        Returns:
            True表示应该激活此Skill
        """
        pass

    @abstractmethod
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """
        执行Skill

        Args:
            context: 执行上下文
            **kwargs: 额外参数

        Returns:
            Skill执行结果
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} category={self.category}>"


class SkillRegistry:
    """Skill注册中心"""

    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill):
        """注册Skill"""
        self.skills[skill.name] = skill

    def unregister(self, name: str):
        """注销Skill"""
        if name in self.skills:
            del self.skills[name]

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取Skill"""
        return self.skills.get(name)

    def list_skills(self) -> List[Dict[str, str]]:
        """列出所有已注册的Skills"""
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "version": skill.version,
                "category": skill.category,
            }
            for skill in self.skills.values()
        ]

    async def match_skills(self, user_input: str, context: SkillContext) -> List[BaseSkill]:
        """匹配可能激活的Skills"""
        matched = []
        for skill in self.skills.values():
            try:
                if await skill.should_activate(user_input, context):
                    matched.append(skill)
            except Exception as e:
                # 静默处理匹配错误
                pass
        return matched

    async def execute_matched(
        self, skills: List[BaseSkill], context: SkillContext, **kwargs
    ) -> Optional[SkillResult]:
        """执行匹配到的Skill"""
        if not skills:
            return None

        # 执行第一个匹配的Skill
        skill = skills[0]
        try:
            result = await skill.execute(context, **kwargs)
            return result
        except Exception as e:
            return SkillResult(
                success=False,
                content=f"Skill执行出错: {str(e)}",
            )


# 全局注册中心
_registry: Optional[SkillRegistry] = None


def get_registry() -> SkillRegistry:
    """获取全局Skill注册中心"""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry