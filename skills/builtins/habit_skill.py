"""习惯追踪Skill"""
import re
import json
from datetime import datetime
from typing import List

from skills.base import BaseSkill, SkillContext, SkillResult
from database import get_database


class HabitSkill(BaseSkill):
    """习惯追踪Skill - 打卡、提醒、统计"""

    name = "habit_skill"
    description = "习惯追踪 - 护肤打卡、提醒、统计、皮肤记录"
    version = "1.0.0"
    category = "habit"

    # 晨间护肤步骤
    MORNING_STEPS = ["洁面", "爽肤水", "精华", "面霜", "防晒"]
    # 晚间护肤步骤
    EVENING_STEPS = ["卸妆", "洁面", "爽肤水", "精华", "面霜", "眼霜"]

    async def should_activate(self, user_input: str, context: SkillContext) -> bool:
        """判断是否应该激活"""
        input_lower = user_input.lower()

        # 打卡相关关键词
        checkin_keywords = ["打卡", "checkin", "晨间", "晚间", "护肤"]
        return any(kw in input_lower for kw in checkin_keywords)

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行习惯追踪"""
        user_input = context.user_input.lower()

        # 判断意图
        if "统计" in context.user_input or "/stats" in context.user_input:
            return await self._show_stats(context)
        elif "记录" in context.user_input or "/log" in context.user_input:
            return await self._log_skin(context, **kwargs)
        elif "打卡" in context.user_input or "checkin" in user_input:
            return await self._checkin(context, **kwargs)
        else:
            # 默认询问是否要打卡
            return SkillResult(
                success=True,
                content=self._get_checkin_prompt(),
                should_respond=False,
            )

    def _get_checkin_prompt(self) -> str:
        """获取打卡提示"""
        return """你好呀！请问是晨间护肤还是晚间护肤呢？

  [1] ☀️ 晨间护肤
  [2] 🌙 晚间护肤
  [3] 📝 自定义打卡

请回复选项或直接输入"晨间"/"晚间" """

    async def _checkin(self, context: SkillContext, **kwargs) -> SkillResult:
        """处理打卡"""
        user_input = context.user_input.lower()
        db = get_database()

        # 判断是晨间还是晚间
        if "晨" in context.user_input or "morning" in user_input:
            checkin_type = "morning"
            type_name = "晨间护肤"
            steps = self.MORNING_STEPS
        elif "晚" in context.user_input or "evening" in user_input:
            checkin_type = "evening"
            type_name = "晚间护肤"
            steps = self.EVENING_STEPS
        elif "自定义" in context.user_input:
            checkin_type = "custom"
            type_name = "自定义护肤"
            steps = []
        else:
            # 询问用户
            return SkillResult(
                success=True,
                content=self._get_checkin_prompt(),
                should_respond=False,
            )

        # 获取用户选择的步骤（如果有）
        selected_steps = kwargs.get("selected_steps", None)
        if selected_steps is None:
            # 让用户选择步骤
            steps_text = "\n".join([f"  [{i+1}] {step}" for i, step in enumerate(steps)])
            content = f"""请选择完成的步骤（用逗号分隔多个选项），直接回车跳过：

{steps_text}

已选项可直接回复，如：1,3,4 或 洁面,爽肤水,精华
"""
            return SkillResult(
                success=True,
                content=content,
                should_respond=False,
                action="awaiting_steps",
            )

        # 记录打卡
        if isinstance(selected_steps, str):
            # 解析用户输入的步骤
            items = [s.strip() for s in selected_steps.split(",")]
        else:
            items = selected_steps

        db.add_checkin(checkin_type, items)
        stats = db.get_checkin_stats()

        # 构建回复
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        items_text = "\n".join([f"  ☑️ {item}" for item in items])

        content = f"""✅ {type_name}打卡完成！

打卡时间：{now}

今日完成项目：
{items_text}

📅 连续打卡：{stats['streak']}天
💪 太棒了！坚持就是胜利！
"""
        return SkillResult(success=True, content=content)

    async def _show_stats(self, context: SkillContext) -> SkillResult:
        """显示统计"""
        db = get_database()
        stats = db.get_checkin_stats()

        content = f"""📊 护肤习惯统计

总打卡次数：{stats['total']}次
  ☀️ 晨间护肤：{stats['morning']}次
  🌙 晚间护肤：{stats['evening']}次

🔥 连续打卡：{stats['streak']}天

继续保持！💪
"""
        return SkillResult(success=True, content=content)

    async def _log_skin(self, context: SkillContext, **kwargs) -> SkillResult:
        """记录皮肤状态"""
        # 简化实现
        content = """请记录今天的皮肤状态：

1. 总体状态：[很好/良好/一般/较差]
2. 油光程度：1-5（1=很干，5=很油）
3. 水分程度：1-5（1=很干，5=很润）
4. 肌肤问题：[如痘痘、过敏、泛红等，用逗号分隔]
5. 备注：[其他想记录的]

请按顺序回复，如：良好,3,4,痘痘 """
        return SkillResult(
            success=True,
            content=content,
            should_respond=False,
            action="awaiting_skin_log",
        )


def get_checkin_steps_from_input(user_input: str) -> List[str]:
    """从用户输入解析打卡步骤"""
    # 尝试匹配数字选项
    import re
    numbers = re.findall(r"\d+", user_input)
    if numbers:
        # 如果是数字选项
        step_map = {
            "1": "洁面", "2": "爽肤水", "3": "精华",
            "4": "面霜", "5": "防晒", "6": "眼霜", "7": "卸妆",
        }
        return [step_map.get(n, n) for n in numbers]

    # 直接使用输入的文字
    return [s.strip() for s in user_input.split(",")]