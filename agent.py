"""Agent核心引擎 - AsyncGenerator模式 - 带四级压缩系统"""
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime

from config import get_config
from llm_adapter import LLMAdapter, get_llm
from database import get_database
from memory import get_memory
from skills.base import SkillContext, SkillRegistry, get_registry
from skills import load_builtin_skills
from events import EventType, Event, get_event_hub
from skills.builtins.habit_skill import get_checkin_steps_from_input
from compress import get_compression_system, CompressionLevel


class Agent:
    """AI Agent核心引擎"""

    def __init__(self):
        self.config = get_config()
        self.llm = get_llm()
        self.db = get_database()
        self.memory = get_memory()
        self.registry = get_registry()
        self.event_hub = get_event_hub()

        # 加载内置Skills
        load_builtin_skills()

        # 压缩系统
        self.compression = get_compression_system()

        # 对话上下文
        self.messages: List[Dict[str, str]] = []

        # 等待用户输入状态
        self.awaiting_input: Optional[str] = None
        self.awaiting_context: Dict = {}

        # 初始化系统消息
        self._init_system_message()

    def _init_system_message(self):
        """初始化系统消息"""
        context_data = self.memory.build_context_for_llm()
        system_prompt = self.llm.build_system_prompt(
            personality=self.config.personality,
            user_info=context_data["user_info"],
            skills=[s["name"] for s in self.registry.list_skills()],
        )

        self.messages = [{"role": "system", "content": system_prompt}]

    async def process(self, user_input: str) -> str:
        """处理用户输入（兼容模式）"""
        result = ""
        async for chunk in self.process_stream(user_input):
            result = chunk
        return result

    async def process_stream(self, user_input: str) -> AsyncGenerator[str, None]:
        """
        处理用户输入 - AsyncGenerator模式
        使用yield逐步输出处理结果
        """
        # 发送用户消息事件
        await self.event_hub.emit(Event(
            type=EventType.USER_MESSAGE,
            data={"content": user_input}
        ))

        # yield事件标记
        yield "[EVENT:USER_MESSAGE]"

        # 检查是否在等待用户输入
        if self.awaiting_input:
            result = await self._handle_awaiting_input(user_input)
            yield result
            return

        # 检查是否是命令
        if user_input.startswith("/"):
            result = await self._handle_command(user_input)
            if result == "/exit":
                yield "[EXIT]"
            else:
                yield result
            return

        # 添加用户消息
        self.messages.append({"role": "user", "content": user_input})
        self.db.add_conversation("user", user_input)

        # 构建上下文
        context = SkillContext(
            user_input=user_input,
            user_id=self.config.user_id,
            profile=self.memory.get_user_profile(),
            memory=self.memory,
            llm=self.llm,
            database=self.db,
            config=self.config,
        )

        # 匹配Skills
        matched_skills = await self.registry.match_skills(user_input, context)

        if matched_skills:
            # 执行Skill
            result = await self.registry.execute_matched(matched_skills, context)

            if result and result.content:
                # 返回Skill结果
                self.messages.append({"role": "assistant", "content": result.content})
                self.db.add_conversation("assistant", result.content)
                yield result.content
                return

        # 使用LLM生成回复
        async for chunk in self._generate_response_stream():
            yield chunk

    async def _generate_response_stream(self) -> AsyncGenerator[str, None]:
        """使用LLM生成回复 - AsyncGenerator流式输出"""
        await self.event_hub.emit(Event(
            type=EventType.AGENT_THINKING,
            data={}
        ))
        yield "[EVENT:THINKING]"

        # 获取对话历史用于上下文
        history = self.db.get_conversations_for_context(limit=10)

        # 构建消息列表
        messages = self.messages.copy()
        # 添加最近的历史对话
        for msg in history[-10:]:
            if msg["role"] != "system":
                messages.append({"role": msg["role"], "content": msg["content"]})

        # 检查并执行压缩
        compressed, was_compressed = await self.compression.compress(messages)
        if was_compressed:
            analysis = self.compression.analyze_context(messages)
            level = self.compression.determine_compression_level(analysis)
            yield f"[EVENT:COMPRESSED level={level.value}]"

        # 使用压缩后的消息
        messages_to_send = compressed if was_compressed else messages

        response = self.llm.chat(messages_to_send)

        if "error" in response:
            yield f"抱歉，AI服务出现了问题：{response['error']}"
            return

        content = response["content"] or "好的，我明白了~"

        # 分块输出（模拟流式效果）
        chunk_size = 20
        for i in range(0, len(content), chunk_size):
            yield content[i:i + chunk_size]

        # 保存到历史
        self.messages.append({"role": "assistant", "content": content})
        self.db.add_conversation("assistant", content)

        # 自动提取并存储记忆
        user_input = next(
            (m.get("content", "") for m in self.messages if m.get("role") == "user"),
            ""
        )
        if user_input:
            await self.memory.process_and_store_memory(user_input, content)

        await self.event_hub.emit(Event(
            type=EventType.AGENT_RESPONSE,
            data={"content": content}
        ))
        yield "[EVENT:RESPONSE_DONE]"

    async def _generate_response(self) -> str:
        """兼容模式：生成完整回复"""
        result = ""
        async for chunk in self._generate_response_stream():
            if not chunk.startswith("["):
                result += chunk
        return result

    async def _handle_command(self, user_input: str) -> str:
        """处理命令"""
        cmd = user_input.lower().strip()

        if cmd in ["/exit", "/quit", "退出"]:
            return "/exit"

        elif cmd in ["/stats", "/stats habit"]:
            context = SkillContext(
                user_input=user_input,
                user_id=self.config.user_id,
                profile={},
                memory=self.memory,
                llm=self.llm,
                database=self.db,
                config=self.config,
            )
            from skills.builtins.habit_skill import HabitSkill
            skill = HabitSkill()
            result = await skill._show_stats(context)
            return result.content

        elif cmd == "/personality" or cmd == "/personality list":
            from skills.builtins.companion_skill import CompanionSkill
            skill = CompanionSkill()
            result = skill._list_personalities()
            return result.content

        elif cmd.startswith("/personality set"):
            from skills.builtins.companion_skill import CompanionSkill
            personality = user_input.replace("/personality set", "").strip()
            skill = CompanionSkill()
            result = await skill._set_personality(
                SkillContext(user_input=personality, user_id=self.config.user_id),
                personality
            )
            return result.content

        elif cmd == "/profile":
            profile = self.memory.get_user_profile()
            content = "📋 你的用户档案：\n\n"

            basic = profile.get("基本信息", {})
            if basic:
                content += f"- 用户ID: {basic.get('user_id', 'default')}\n"
                content += f"- 肤质: {basic.get('skin_type', '未设置')}\n"
                content += f"- 预算: {basic.get('budget', '中端')}\n"
                content += f"- 人格: {basic.get('personality', '美妆闺蜜')}\n"

            concerns = profile.get("肤质信息", {}).get("skin_concerns", "[]")
            if concerns and concerns != "[]":
                content += f"- 肌肤问题: {concerns}\n"

            return content

        elif cmd == "/memories" or cmd == "/memory":
            # 查看已记忆的信息
            memories = self.memory.list_memories()
            content = "🧠 你的记忆：\n\n"

            if not any(memories.values()):
                return "暂无记忆记录，我会自动记住你提到的护肤习惯、产品体验等信息~"

            if memories.get("habits"):
                content += "📝 护肤习惯：\n"
                for h in memories["habits"][-5:]:
                    content += f"  • {h}\n"
                content += "\n"

            if memories.get("products"):
                content += "🛍️ 产品经验：\n"
                for p in memories["products"][-5:]:
                    content += f"  • {p}\n"
                content += "\n"

            if memories.get("skin_history"):
                content += "📆 皮肤问题历史：\n"
                for s in memories["skin_history"][-5:]:
                    content += f"  • {s}\n"
                content += "\n"

            if memories.get("personal"):
                content += "💖 个人偏好：\n"
                for p in memories["personal"][-5:]:
                    content += f"  • {p}\n"

            return content

        elif cmd == "/skills" or cmd == "/skills list":
            skills = self.registry.list_skills()
            content = "🛠 已加载的Skills：\n\n"
            for s in skills:
                content += f"- {s['name']} (v{s['version']})\n"
                content += f"  {s['description']}\n\n"
            return content

        elif cmd == "/history":
            history = self.db.get_conversations(limit=10)
            if not history:
                return "暂无对话历史"

            content = "📜 最近对话：\n\n"
            for msg in reversed(history):
                role = "你" if msg["role"] == "user" else "AI"
                content += f"{role}: {msg['content'][:50]}...\n"
            return content

        elif cmd == "/clear":
            self.messages = self._init_system_message()
            self.db.clear_conversations()
            return "✅ 对话已清除"

        elif cmd.startswith("/checkin"):
            context = SkillContext(
                user_input=user_input,
                user_id=self.config.user_id,
                profile={},
                memory=self.memory,
                llm=self.llm,
                database=self.db,
                config=self.config,
            )
            from skills.builtins.habit_skill import HabitSkill
            skill = HabitSkill()
            result = await skill.execute(context)
            if result.action:
                self.awaiting_input = "checkin_steps"
                self.awaiting_context = {"context": context}
            return result.content

        elif cmd == "/stats":
            context = SkillContext(
                user_input=user_input,
                user_id=self.config.user_id,
                profile={},
                memory=self.memory,
                llm=self.llm,
                database=self.db,
                config=self.config,
            )
            from skills.builtins.habit_skill import HabitSkill
            skill = HabitSkill()
            result = await skill._show_stats(context)
            return result.content

        elif cmd == "/snip":
            # 用户主动裁剪不需要的内容
            compressed = await self.compression.snip(self.messages)
            self.messages = compressed
            return "✅ 已裁剪旧的工具结果"

        elif cmd == "/compress":
            # 手动触发压缩
            compressed, was_compressed = await self.compression.compress(self.messages)
            if was_compressed:
                self.messages = compressed
                stats = self.compression.get_stats()
                if stats:
                    last = stats[-1]
                    return f"✅ 压缩完成！\n级别: {last.level.value}\n原因: {last.trigger_reason}"
            return "当前无需压缩"

        elif cmd == "/compress_stats":
            # 显示压缩统计
            stats = self.compression.get_stats()
            if not stats:
                return "暂无压缩记录"
            content = "📊 压缩统计：\n\n"
            for s in reversed(stats[-5:]):
                content += f"- {s.level.value}: {s.trigger_reason}\n"
            return content

        elif cmd == "/help":
            return """📚 可用命令：

  /help              显示帮助
  /checkin [选项]    护肤打卡 (如 /checkin morning)
  /stats             查看打卡统计
  /snip              裁剪旧工具结果
  /compress          手动触发压缩
  /compress_stats    查看压缩统计
  /log               记录皮肤状态
  /product           产品推荐 (直接说"推荐XX"也可以)
  /personality       查看人格选项
  /personality set <人格>  切换人格
  /profile           查看用户档案
  /memories          查看记忆记录
  /skills            查看已加载的技能
  /history           查看历史对话
  /clear             清除对话
  /exit              退出

也可以直接输入你想说的话，我会陪你聊天~"""

        else:
            return f"❌ 未知命令：{cmd}\n输入 /help 查看可用命令"

    async def _handle_awaiting_input(self, user_input: str) -> str:
        """处理等待用户输入的情况"""
        awaiting = self.awaiting_input
        self.awaiting_input = None

        if awaiting == "checkin_steps":
            context = self.awaiting_context.get("context")
            steps = get_checkin_steps_from_input(user_input)
            from skills.builtins.habit_skill import HabitSkill
            skill = HabitSkill()
            result = await skill.execute(context, selected_steps=steps)
            return result.content

        elif awaiting == "awaiting_category":
            category_map = {"1": "美白", "2": "保湿", "3": "防晒", "4": "抗衰老", "5": "祛痘控油", "6": None}
            category = category_map.get(user_input.strip(), user_input)

            context = SkillContext(
                user_input=f"推荐{category}" if category else "推荐产品",
                user_id=self.config.user_id,
                profile={},
                memory=self.memory,
                llm=self.llm,
                database=self.db,
                config=self.config,
            )

            from skills.builtins.product_skill import ProductSkill
            skill = ProductSkill()
            result = await skill.execute(context, budget="2")
            if "预算" in result.content:
                self.awaiting_input = "awaiting_budget"
            return result.content

        return "好的，请继续~"


# 全局Agent实例
_agent: Optional[Agent] = None


def get_agent() -> Agent:
    """获取全局Agent实例"""
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent