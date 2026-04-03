"""Skill模块初始化"""
from skills.base import BaseSkill, SkillContext, SkillResult, SkillRegistry, get_registry

# 导入内置Skills
from skills.builtins.habit_skill import HabitSkill
from skills.builtins.product_skill import ProductSkill
from skills.builtins.companion_skill import CompanionSkill


def load_builtin_skills():
    """加载内置Skills"""
    registry = get_registry()

    # 注册内置Skills
    registry.register(HabitSkill())
    registry.register(ProductSkill())
    registry.register(CompanionSkill())

    return registry