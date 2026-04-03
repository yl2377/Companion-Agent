"""情感陪伴Skill"""
import re
from skills.base import BaseSkill, SkillContext, SkillResult
from config import get_config, save_user_config


class CompanionSkill(BaseSkill):
    """情感陪伴Skill - 闲聊、情绪支持、人格管理"""

    name = "companion_skill"
    description = "情感陪伴 - 闲聊、情绪倾听、人格切换"
    version = "1.0.0"
    category = "companion"

    # 预设人格
    PERSONALITIES = {
        "专业顾问": {
            "description": "专业、详细、数据导向",
            "greeting": "你好，我是你的专业美妆护肤顾问。有什么护肤问题可以问我~",
        },
        "美妆闺蜜": {
            "description": "活泼、亲切、带emoji",
            "greeting": "嗨~我是你的美妆闺蜜🌸 有什么想聊的吗？",
        },
        "知心大姐姐": {
            "description": "温柔、倾听、鼓励",
            "greeting": "你好呀~我是知心大姐姐有什么心事可以跟我说哦~",
        },
        "毒舌达人": {
            "description": "犀利、直接、有趣",
            "greeting": "来了来了~我是毒舌美妆博主，有话直说！",
        },
    }

    async def should_activate(self, user_input: str, context: SkillContext) -> bool:
        """判断是否应该激活"""
        # 这是一个默认Skill，当没有其他Skill匹配时激活
        return True

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行情感陪伴"""
        user_input = context.user_input

        # 检查是否是命令
        if user_input.startswith("/"):
            return await self._handle_command(context)

        # 检查是否在设置人格
        action = kwargs.get("action")
        if action == "set_personality":
            return await self._set_personality(context, user_input)

        # 检查是否需要进入AI对话
        # 这里返回None，让Agent使用LLM进行对话
        return SkillResult(
            success=True,
            content=None,  # 让Agent生成回复
            should_respond=True,
        )

    async def _handle_command(self, context: SkillContext) -> SkillResult:
        """处理命令"""
        user_input = context.user_input.lower()

        if "personality" in user_input or "人格" in user_input:
            return await self._handle_personality_command(context)
        elif "help" in user_input or "帮助" in user_input:
            return await self._show_help(context)
        else:
            return SkillResult(
                success=True,
                content=None,
                should_respond=True,
            )

    async def _handle_personality_command(self, context: SkillContext) -> SkillResult:
        """处理人格命令"""
        user_input = context.user_input.lower()

        # 设置人格
        if "set" in user_input or "设置" in user_input or "切换" in user_input:
            # 提取人格名称
            for p in self.PERSONALITIES:
                if p in context.user_input:
                    return await self._set_personality(context, p)

            # 显示人格列表让用户选择
            return self._list_personalities()
        elif "list" in user_input or "列表" in user_input or "查看" in user_input:
            return self._list_personalities()
        else:
            return self._list_personalities()

    def _list_personalities(self) -> SkillResult:
        """列出可用人格"""
        content = "可选择的人格：\n\n"

        for i, (name, info) in enumerate(self.PERSONALITIES.items(), 1):
            content += f"  [{i}] {name}\n"
            content += f"      {info['description']}\n\n"

        content += "输入 /personality set <人格名称> 来切换人格\n"
        content += "例如：/personality set 美妆闺蜜"

        return SkillResult(
            success=True,
            content=content,
            should_respond=False,
            action="awaiting_personality",
        )

    async def _set_personality(self, context: SkillContext, personality: str = None) -> SkillResult:
        """设置人格"""
        if personality is None:
            personality = context.user_input.strip()

        # 匹配最接近的人格
        matched = None
        for p in self.PERSONALITIES:
            if p in personality or personality in p:
                matched = p
                break

        if matched:
            # 保存配置
            config = get_config()
            config.personality = matched
            save_user_config(config)

            info = self.PERSONALITIES[matched]
            content = f"✅ 人格已切换为：{matched}\n"
            content += f"   {info['greeting']}"

            return SkillResult(
                success=True,
                content=content,
                should_respond=False,
            )
        else:
            return self._list_personalities()

    async def _show_help(self, context: SkillContext) -> SkillResult:
        """显示帮助"""
        content = """可用命令：

  /help              显示帮助
  /checkin [选项]    护肤打卡
  /stats             查看打卡统计
  /log               记录皮肤状态
  /product           产品推荐
  /personality       查看/切换人格
  /profile           查看用户档案
  /skills            查看已加载的技能
  /history           查看历史对话
  /clear             清除对话
  /exit              退出程序

也可以直接输入你想说的话，我会陪你聊天~
"""
        return SkillResult(
            success=True,
            content=content,
            should_respond=False,
        )

    def get_current_personality(self) -> str:
        """获取当前人格"""
        config = get_config()
        return config.personality