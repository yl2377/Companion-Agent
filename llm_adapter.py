"""LLM适配器 - 支持OpenAI兼容API"""
import os
import json
from typing import List, Dict, Optional, Any
from openai import OpenAI

from config import get_config


class LLMAdapter:
    """大语言模型适配器"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        config = get_config()

        self.client = OpenAI(
            api_key=api_key or config.openai_api_key,
            base_url=base_url or config.openai_base_url,
        )
        self.model = model or config.openai_model
        self.config = config

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        tools: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            tools: 工具定义

        Returns:
            响应字典
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                tools=tools,
            )

            result = {
                "content": response.choices[0].message.content,
                "tool_calls": [],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            }

            # 处理工具调用
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        }
                    })

            return result

        except Exception as e:
            return {
                "error": str(e),
                "content": None,
                "tool_calls": [],
            }

    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        tools: List[Dict] = None,
    ) -> Dict[str, Any]:
        """异步版本"""
        return self.chat(messages, temperature, max_tokens, tools)

    def build_system_prompt(
        self,
        personality: str = None,
        user_info: Dict = None,
        skills: List[str] = None,
    ) -> str:
        """构建系统提示词"""
        config = get_config()
        personality = personality or config.personality

        # 人格设定
        personalities = {
            "专业顾问": "你是一位专业、严谨的美妆护肤顾问。你的回复详细、数据导向，喜欢用成分和功效说话。",
            "美妆闺蜜": "你是一位活泼、亲切的美妆闺蜜。你的回复温暖可爱，喜欢用emoji，适当地鼓励用户。",
            "知心大姐姐": "你是一位温柔的大姐姐，善于倾听，给予用户温暖的鼓励和支持。",
            "毒舌达人": "你是一位犀利、直接的美妆博主，幽默风趣，讲话一针见血。",
        }

        base_prompt = personalities.get(
            personality,
            "你是一位温暖的美妆护肤陪伴助手。"
        )

        # 用户信息
        user_info_text = ""
        if user_info:
            parts = []
            if user_info.get("skin_type"):
                parts.append(f"肤质：{user_info['skin_type']}")
            if user_info.get("budget"):
                parts.append(f"预算：{user_info['budget']}")
            if user_info.get("skin_concerns"):
                parts.append(f"肌肤问题：{', '.join(user_info['skin_concerns'])}")
            if parts:
                user_info_text = "\n用户信息：" + ", ".join(parts)

        # Skills
        skills_text = ""
        if skills:
            skills_text = f"\n可用技能：{', '.join(skills)}"

        return f"""你是{base_prompt}

{user_info_text}
{skills_text}

回复要求：
- 根据用户设定的人格风格进行回复
- 适当使用emoji让对话更生动
- 温暖亲切，给予用户鼓励
- 如果用户询问护肤问题，给出专业的建议
- 保持对话的连贯性，记得之前的对话内容
"""


# 全局LLM实例
_llm: Optional[LLMAdapter] = None


def get_llm() -> LLMAdapter:
    """获取全局LLM实例"""
    global _llm
    if _llm is None:
        _llm = LLMAdapter()
    return _llm