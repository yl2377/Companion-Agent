"""压缩系统 - 四级渐进压缩"""
import time
import json
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from config import get_config
from llm_adapter import get_llm
from database import get_database


class CompressionLevel(Enum):
    """压缩级别"""
    NONE = "none"           # 无压缩
    SNIP = "snip"           # 裁剪 - 用户主动标记
    MICRO_COMPACT = "micro" # 微压缩 - 时间触发
    COLLAPSE = "collapse"   # 折叠 - LLM摘要
    AUTO_COMPACT = "auto"   # 自动压缩 - 最终兜底


@dataclass
class CompressionStats:
    """压缩统计"""
    level: CompressionLevel
    original_tokens: int
    compressed_tokens: int
    trigger_reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class CompressionConfig:
    """压缩配置"""
    # Snip 配置
    keep_recent_tool_results: int = 2

    # MicroCompact 配置
    micro_compact_threshold_minutes: float = 30.0

    # Collapse 配置
    collapse_threshold_percent: float = 30.0

    # AutoCompact 配置
    auto_compact_threshold_percent: float = 15.0

    # 保留内容
    keep_system_prompt: bool = True
    keep_recent_turns: int = 5  # 保留最近N轮对话


class CompressionSystem:
    """
    四级渐进压缩系统

    触发条件对比：
    | 级别 | 触发方式 | 触发条件 | 压缩成本 | 信息损失 |
    |------|----------|----------|----------|----------|
    | Snip | 用户/命令 | 手动指定清除 | 0 | 完全丢失 |
    | MicroCompact | 自动 | 时间阈值(30分钟) | 0 | 完全丢失 |
    | Collapse | 自动 | token剩余<30% | LLM调用 | 转换为摘要 |
    | AutoCompact | 自动 | token剩余<15% | LLM调用 | 激进压缩 |
    """

    def __init__(self, config: CompressionConfig = None):
        self.config = config or CompressionConfig()
        self.llm = get_llm()
        self.db = get_database()
        self.stats_history: List[CompressionStats] = []
        self.last_compact_time: float = time.time()
        self.tool_result_map: Dict[str, Dict] = {}  # tool_call_id -> 内容映射

    def estimate_tokens(self, text: str) -> int:
        """简单估算token数量（中文字符约等于1.5个token）"""
        if not text:
            return 0
        # 粗略估算：中文每个字符 ~1.5 token，英文每个字符 ~0.25 token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars * 0.25)

    def analyze_context(self, messages: List[Dict]) -> Dict[str, Any]:
        """分析当前上下文状态"""
        total_text = ""
        tool_results = []
        recent_turns = []

        for msg in messages:
            if msg.get("role") == "system":
                total_text += msg.get("content", "")
            elif msg.get("content"):
                total_text += msg.get("content", "")
                if msg.get("role") in ["user", "assistant"]:
                    recent_turns.append(msg)

            # 收集工具结果
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                for tc in tool_calls:
                    if isinstance(tc, dict):
                        tool_results.append(tc)

        # 检查工具结果新鲜度
        current_time = time.time()
        stale_tool_results = []
        for tc in tool_results:
            # 简单检查：假设消息按时间顺序
            pass

        return {
            "total_tokens": self.estimate_tokens(total_text),
            "total_messages": len(messages),
            "tool_result_count": len(tool_results),
            "recent_turns": len(recent_turns),
            "time_since_last_compact": current_time - self.last_compact_time,
        }

    def determine_compression_level(self, analysis: Dict) -> CompressionLevel:
        """确定需要使用的压缩级别"""
        # 估算上下文窗口剩余比例（假设最大窗口 128k）
        max_tokens = 128000
        used_tokens = analysis["total_tokens"]
        remaining_percent = ((max_tokens - used_tokens) / max_tokens) * 100

        # 检查时间（用于MicroCompact）
        time_threshold = self.config.micro_compact_threshold_minutes * 60
        time_elapsed = analysis["time_since_last_compact"]

        # 级别判断
        if remaining_percent < self.config.auto_compact_threshold_percent:
            return CompressionLevel.AUTO_COMPACT
        elif remaining_percent < self.config.collapse_threshold_percent:
            return CompressionLevel.COLLAPSE
        elif time_elapsed > time_threshold:
            return CompressionLevel.MICRO_COMPACT
        else:
            return CompressionLevel.NONE

    # ========== Level 1: Snip 裁剪 ==========

    async def snip(self, messages: List[Dict], target_content: str = None) -> List[Dict]:
        """
        Snip（裁剪）：用户主动标记不需要的工具结果，直接替换为标记文本

        Args:
            messages: 消息列表
            target_content: 要裁剪的内容（可选，不指定则裁剪所有工具结果）

        Returns:
            裁剪后的消息列表
        """
        result = []
        cleared_count = 0

        for msg in messages:
            if msg.get("tool_calls"):
                # 保留工具调用ID，清除结果
                new_msg = msg.copy()
                new_msg["content"] = "[Old tool result content cleared]"
                cleared_count += len(msg.get("tool_calls"))
                result.append(new_msg)
            else:
                result.append(msg)

        if cleared_count > 0:
            self.stats_history.append(CompressionStats(
                level=CompressionLevel.SNIP,
                original_tokens=0,
                compressed_tokens=0,
                trigger_reason=f"用户主动裁剪，清理{cleared_count}个工具结果"
            ))

        return result

    # ========== Level 2: MicroCompact 微压缩 ==========

    async def micro_compact(self, messages: List[Dict]) -> List[Dict]:
        """
        MicroCompact（微压缩）：基于时间触发，保留最近N个工具结果

        触发条件：距离上一次助手消息超过30分钟

        Returns:
            压缩后的消息列表
        """
        result = []
        keep_count = self.config.keep_recent_tool_results
        cleared_count = 0

        # 统计工具结果
        tool_results = []
        for i, msg in enumerate(messages):
            if msg.get("tool_calls"):
                tool_results.append((i, msg))

        # 保留最近的，其他清除
        for i, msg in messages:
            if msg in [t[1] for t in tool_results]:
                # 找到这个工具结果的位置
                tool_idx = next((j for j, t in enumerate(tool_results) if t[1] == msg), -1)
                if tool_idx >= keep_count:
                    # 清除
                    new_msg = msg.copy()
                    new_msg["content"] = "[Old tool result content cleared]"
                    result.append(new_msg)
                    cleared_count += 1
                else:
                    result.append(msg)
            else:
                result.append(msg)

        if cleared_count > 0:
            self.last_compact_time = time.time()
            self.stats_history.append(CompressionStats(
                level=CompressionLevel.MICRO_COMPACT,
                original_tokens=0,
                compressed_tokens=0,
                trigger_reason=f"时间触发，清理{cleared_count}个旧工具结果"
            ))

        return result

    # ========== Level 3: Collapse 折叠 ==========

    async def collapse(self, messages: List[Dict]) -> List[Dict]:
        """
        Collapse（折叠）：调用LLM将旧对话压缩为精简摘要

        触发条件：上下文token剩余 < 30%

        Returns:
            压缩后的消息列表
        """
        if len(messages) <= self.config.keep_recent_turns + 1:
            return messages  # 内容太少，不需要压缩

        # 分离保留部分和可压缩部分
        system_msg = None
        if messages[0].get("role") == "system":
            system_msg = messages[0]
            messages = messages[1:]

        keep_count = self.config.keep_recent_turns
        keep_messages = messages[-keep_count:]
        compress_messages = messages[:-keep_count]

        if not compress_messages:
            return messages

        # 构建压缩提示
        compress_prompt = self._build_compress_prompt(compress_messages)

        # 调用LLM压缩
        response = self.llm.chat([
            {"role": "system", "content": "你是一个对话摘要助手。请将以下对话压缩为精简摘要，保留关键信息。"},
            {"role": "user", "content": compress_prompt}
        ])

        summary = response.get("content", "") if response else ""

        # 构建新消息列表
        result = []
        if system_msg:
            result.append(system_msg)

        # 添加摘要作为压缩标记
        result.append({
            "role": "system",
            "content": f"[对话摘要] {summary}"
        })

        # 添加保留的最近消息
        result.extend(keep_messages)

        # 统计
        original_tokens = self.estimate_tokens(self._messages_to_text(compress_messages))
        compressed_tokens = self.estimate_tokens(summary)

        self.last_compact_time = time.time()
        self.stats_history.append(CompressionStats(
            level=CompressionLevel.COLLAPSE,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            trigger_reason=f"Token剩余<{self.config.collapse_threshold_percent}%，触发折叠压缩"
        ))

        return result

    def _build_compress_prompt(self, messages: List[Dict]) -> str:
        """构建压缩提示"""
        prompt = "请将以下对话压缩为100字以内的摘要，保留：\n"
        prompt += "1. 用户肤质和护肤目标\n"
        prompt += "2. 产品偏好和过敏信息\n"
        prompt += "3. 关键交互历史\n"
        prompt += "4. 打卡记录摘要\n\n"
        prompt += "对话内容：\n"

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if content and role != "system":
                prompt += f"{role}: {content[:200]}\n"

        return prompt

    def _messages_to_text(self, messages: List[Dict]) -> str:
        """将消息列表转为文本"""
        return "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in messages
            if msg.get("content")
        ])

    # ========== Level 4: AutoCompact 自动压缩 ==========

    async def auto_compact(self, messages: List[Dict]) -> List[Dict]:
        """
        AutoCompact（自动压缩）：最终兜底方案，激进压缩

        触发条件：上下文token剩余 < 15%

        策略：
        - 保留：核心用户档案 + 最近1轮对话 + 长期记忆摘要
        - 丢弃：所有工具结果
        - 压缩：更早的对话内容
        """
        # 提取系统消息（用户档案）
        system_msg = None
        if messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            messages = messages[1:]

        # 保留最近1轮对话
        keep_messages = messages[-2:] if len(messages) >= 2 else messages

        # 构建核心档案
        profile_prompt = """请保留以下核心信息，用50字以内概括：
- 用户肤质和预算
- 当前护肤目标
- 最近一次对话的要点
"""
        # 获取用户档案信息
        profile_info = self._get_user_profile_summary()

        # 构建最终消息
        result = []

        # 添加核心档案
        if system_msg:
            result.append({
                "role": "system",
                "content": f"{system_msg.get('content', '')}\n\n[上下文已高度压缩]\n用户核心信息：{profile_info}"
            })

        # 添加最近对话
        result.extend(keep_messages)

        self.last_compact_time = time.time()
        self.stats_history.append(CompressionStats(
            level=CompressionLevel.AUTO_COMPACT,
            original_tokens=0,
            compressed_tokens=0,
            trigger_reason="Token剩余<15%，触发自动压缩"
        ))

        return result

    def _get_user_profile_summary(self) -> str:
        """获取用户档案摘要"""
        try:
            from memory import get_memory
            memory = get_memory()
            profile = memory.get_user_profile()

            basic = profile.get("基本信息", {})
            parts = []
            if basic.get("skin_type"):
                parts.append(f"肤质:{basic['skin_type']}")
            if basic.get("budget"):
                parts.append(f"预算:{basic['budget']}")
            if basic.get("personality"):
                parts.append(f"人格:{basic['personality']}")

            return ", ".join(parts) if parts else "用户信息未设置"
        except:
            return "无法获取用户信息"

    # ========== 主压缩接口 ==========

    async def compress(self, messages: List[Dict]) -> List[Dict]:
        """
        自动选择合适的压缩级别执行压缩

        Returns:
            (压缩后的消息列表, 是否进行了压缩)
        """
        analysis = self.analyze_context(messages)
        level = self.determine_compression_level(analysis)

        if level == CompressionLevel.NONE:
            return messages, False

        elif level == CompressionLevel.SNIP:
            return await self.snip(messages), True

        elif level == CompressionLevel.MICRO_COMPACT:
            return await self.micro_compact(messages), True

        elif level == CompressionLevel.COLLAPSE:
            return await self.collapse(messages), True

        elif level == CompressionLevel.AUTO_COMPACT:
            return await self.auto_compact(messages), True

        return messages, False

    def get_stats(self) -> List[CompressionStats]:
        """获取压缩历史统计"""
        return self.stats_history[-10:]  # 返回最近10条


# 全局实例
_compression_system: Optional[CompressionSystem] = None


def get_compression_system() -> CompressionSystem:
    """获取全局压缩系统实例"""
    global _compression_system
    if _compression_system is None:
        _compression_system = CompressionSystem()
    return _compression_system


# ========== 便捷函数 ==========

async def auto_compress(messages: List[Dict]) -> tuple[List[Dict], bool]:
    """自动压缩接口"""
    system = get_compression_system()
    return await system.compress(messages)


async def snip_content(messages: List[Dict], content: str = None) -> List[Dict]:
    """Snip裁剪接口"""
    system = get_compression_system()
    return await system.snip(messages, content)