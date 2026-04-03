"""事件系统"""
from enum import Enum
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


class EventType(Enum):
    """事件类型"""
    # 生命周期
    SESSION_START = "session_start"
    SESSION_END = "session_end"

    # 对话
    USER_MESSAGE = "user_message"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONSE = "agent_response"

    # 工具
    TOOL_SELECT = "tool_select"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_END = "tool_call_end"
    TOOL_ERROR = "tool_error"

    # 记忆
    MEMORY_STORE = "memory_store"
    MEMORY_RETRIEVE = "memory_retrieve"

    # Skill
    SKILL_LOAD = "skill_load"
    SKILL_UNLOAD = "skill_unload"
    SKILL_ACTIVATE = "skill_activate"

    # 钩子
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    PRE_MESSAGE = "pre_message"
    POST_MESSAGE = "post_message"


@dataclass
class Event:
    """事件"""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventHub:
    """事件中心"""

    def __init__(self):
        self.listeners: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Event] = []

    def on(self, event_type: EventType, callback: Callable):
        """订阅事件"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def off(self, event_type: EventType, callback: Callable):
        """取消订阅"""
        if event_type in self.listeners:
            self.listeners[event_type].remove(callback)

    async def emit(self, event: Event):
        """发布事件"""
        self.event_history.append(event)

        if event.type in self.listeners:
            for callback in self.listeners[event.type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    # 静默处理事件回调错误
                    pass

    def get_history(self, event_type: EventType = None, limit: int = 50) -> List[Event]:
        """获取事件历史"""
        if event_type:
            return [e for e in self.event_history if e.type == event_type][-limit:]
        return self.event_history[-limit:]

    def clear_history(self):
        """清除事件历史"""
        self.event_history.clear()


import asyncio


# 全局事件中心
_event_hub: EventHub = None


def get_event_hub() -> EventHub:
    """获取全局事件中心"""
    global _event_hub
    if _event_hub is None:
        _event_hub = EventHub()
    return _event_hub