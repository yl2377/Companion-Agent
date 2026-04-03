"""记忆系统 - 管理用户档案和长期记忆"""
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from llm_adapter import get_llm


class MemorySystem:
    """记忆系统 - 管理用户档案和长期记忆"""

    # 记忆类型关键词
    MEMORY_KEYWORDS = {
        "habit": ["习惯用", "每天", "一直用", "早上", "晚上", "通常", "一般"],
        "product": ["用过", "用了", "效果", "推荐", "买过", "肌肤之钥"],
        "skin_history": ["之前", "以前", "后来", "以前是", "之前有"],
        "personal": ["我喜欢", "我不要", "讨厌", "想要", "喜欢"],
    }

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"

        self.data_dir = Path(data_dir)
        self.memory_dir = self.data_dir / "memory"
        self.user_dir = self.memory_dir / "user"
        self.feedback_dir = self.memory_dir / "feedback"
        self.project_dir = self.memory_dir / "project"
        self.reference_dir = self.memory_dir / "reference"

    # ========== 用户画像 ==========

    def get_user_profile(self) -> Dict:
        """获取用户档案"""
        profile_path = self.user_dir / "user_profile.md"
        if not profile_path.exists():
            return {}

        content = profile_path.read_text(encoding="utf-8")
        return self._parse_markdown_profile(content)

    def _parse_markdown_profile(self, content: str) -> Dict:
        """解析Markdown用户档案"""
        profile = {}
        current_section = None

        for line in content.split("\n"):
            line = line.strip()

            # 章节标题
            if line.startswith("##"):
                current_section = line.replace("##", "").strip()
                profile[current_section.lower()] = {}
                continue

            # 键值对
            if line.startswith("-"):
                line = line[1:].strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower().replace(" ", "_")
                    value = value.strip()

                    if current_section:
                        if current_section.lower() not in profile:
                            profile[current_section.lower()] = {}
                        profile[current_section.lower()][key] = value
                    else:
                        profile[key] = value

        return profile

    def update_user_profile(self, updates: Dict):
        """更新用户档案"""
        profile_path = self.user_dir / "user_profile.md"

        # 读取现有内容
        if profile_path.exists():
            content = profile_path.read_text(encoding="utf-8")
        else:
            content = "# 用户档案\n\n"

        # 简单更新逻辑 - 替换已存在的键值或添加新键值
        for key, value in updates.items():
            key_line = f"- {key}: "
            # 检查是否存在
            pattern = re.compile(rf"^{re.escape(key_line)}.*$", re.MULTILINE)
            if pattern.search(content):
                content = pattern.sub(f"{key_line}{value}", content)
            else:
                # 尝试找到合适的位置插入
                if "## 基本信息" in content:
                    content = content.replace(
                        "## 基本信息\n",
                        f"## 基本信息\n{key_line}{value}\n"
                    )
                else:
                    content += f"\n- {key}: {value}"

        profile_path.write_text(content, encoding="utf-8")

    # ========== 偏好记忆 ==========

    def add_preference(self, preference_type: str, content: str):
        """添加偏好记忆"""
        if preference_type == "habit":
            self._add_to_memory("preferences.md", f"- 护肤习惯: {content}")
        elif preference_type == "product":
            self._add_to_memory("preferences.md", f"- 产品经验: {content}")
        elif preference_type == "skin_history":
            self._add_to_memory("preferences.md", f"- 皮肤问题: {content}")
        elif preference_type == "personal":
            self._add_to_memory("preferences.md", f"- 个人偏好: {content}")

    def _add_to_memory(self, filename: str, line: str):
        """添加内容到记忆文件"""
        path = self.feedback_dir / filename
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# 记忆文件\n\n", encoding="utf-8")

        content = path.read_text(encoding="utf-8")
        content += f"{line}\n"
        path.write_text(content, encoding="utf-8")

    # ========== 项目状态 ==========

    def get_current_goal(self) -> Optional[str]:
        """获取当前护肤目标"""
        path = self.project_dir / "current_goal.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def set_current_goal(self, goal: str):
        """设置当前护肤目标"""
        path = self.project_dir / "current_goal.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# 当前护肤目标\n\n## 近期目标\n- {goal}\n", encoding="utf-8")

    def get_session_summary(self) -> Optional[str]:
        """获取会话摘要"""
        path = self.project_dir / "session_summary.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def update_session_summary(self, summary: str):
        """更新会话摘要"""
        path = self.project_dir / "session_summary.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# 会话摘要\n\n{summary}\n", encoding="utf-8")

    # ========== 参考知识 ==========

    def get_products_knowledge(self) -> str:
        """获取产品知识库"""
        path = self.reference_dir / "products.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def get_skincare_tips(self) -> str:
        """获取护肤知识"""
        path = self.reference_dir / "skincare_tips.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    # ========== 上下文构建 ==========

    def build_context_for_llm(self) -> Dict[str, str]:
        """构建LLM上下文"""
        profile = self.get_user_profile()

        # 用户基本信息
        user_info = {}
        basic_info = profile.get("基本信息", {})
        if basic_info.get("skin_type"):
            user_info["skin_type"] = basic_info["skin_type"]
        if basic_info.get("budget"):
            user_info["budget"] = basic_info["budget"]
        if basic_info.get("skin_concerns"):
            user_info["skin_concerns"] = basic_info["skin_concerns"].strip("[]").replace("'", "").split(", ")

        return {
            "user_info": user_info,
            "products_knowledge": self.get_products_knowledge(),
            "skincare_tips": self.get_skincare_tips(),
            "preferences": self.get_preferences_summary(),
        }

    # ========== 用户记忆提取 ==========

    async def extract_memory(self, user_input: str, ai_response: str = None) -> Optional[Dict[str, str]]:
        """
        从用户输入中提取记忆

        自动识别以下类型：
        - habit: 护肤习惯 ("我习惯用"、"每天")
        - product: 产品经验 ("用过"、"效果不错")
        - skin_history: 皮肤问题历史 ("之前"、"以前")
        - personal: 偏好约定 ("我喜欢"、"不要")

        Args:
            user_input: 用户输入
            ai_response: AI回复（可选）

        Returns:
            提取的记忆字典，没有则返回None
        """
        # 快速检查是否包含关键词
        has_keyword = False
        for keywords in self.MEMORY_KEYWORDS.values():
            if any(kw in user_input for kw in keywords):
                has_keyword = True
                break

        if not has_keyword and not ai_response:
            return None

        # 调用LLM提取记忆
        llm = get_llm()

        prompt = f"""请从以下用户输入中提取可能需要记忆的信息。

用户输入：{user_input}
{f"AI回复：{ai_response}" if ai_response else ""}

请以下面的JSON格式返回（如果没有需要记忆的信息，返回null）：
{{
    "type": "habit|product|skin_history|personal",
    "content": "具体需要记忆的内容",
    "summary": "一句话概括"
}}

只返回JSON，不要其他内容。
"""

        response = llm.chat([
            {"role": "system", "content": "你是一个记忆提取助手。"},
            {"role": "user", "content": prompt}
        ])

        content = response.get("content", "").strip()
        if not content or content == "null":
            return None

        # 解析JSON
        try:
            # 尝试提取JSON
            if "{" in content:
                json_str = content[content.find("{"):content.rfind("}")+1]
                memory = json.loads(json_str)
                return memory
        except json.JSONDecodeError:
            pass

        return None

    async def store_memory(self, memory: Dict[str, str]) -> bool:
        """
        存储提取的记忆

        Args:
            memory: 记忆字典，包含 type, content, summary

        Returns:
            是否成功存储
        """
        if not memory or not memory.get("type"):
            return False

        memory_type = memory["type"]
        content = memory.get("content", "")
        summary = memory.get("summary", content)

        if not content:
            return False

        # 根据类型存储到不同文件
        timestamp = datetime.now().strftime("%Y-%m-%d")

        if memory_type == "habit":
            self._add_to_memory("preferences.md", f"\n## 护肤习惯 [{timestamp}]\n- {content}")
        elif memory_type == "product":
            self._add_to_memory("preferences.md", f"\n## 产品经验 [{timestamp}]\n- {content}")
        elif memory_type == "skin_history":
            self._add_to_memory("preferences.md", f"\n## 皮肤问题历史 [{timestamp}]\n- {content}")
        elif memory_type == "personal":
            self._add_to_memory("preferences.md", f"\n## 个人偏好 [{timestamp}]\n- {content}")

        return True

    async def process_and_store_memory(self, user_input: str, ai_response: str = None) -> bool:
        """提取并存储记忆的便捷方法"""
        memory = await self.extract_memory(user_input, ai_response)
        if memory:
            return await self.store_memory(memory)
        return False

    # ========== 记忆查看 ==========

    def get_preferences_summary(self) -> str:
        """获取偏好摘要用于上下文"""
        path = self.feedback_dir / "preferences.md"
        if not path.exists():
            return ""

        content = path.read_text(encoding="utf-8")
        # 只返回前500字
        return content[:500] if len(content) > 500 else content

    def list_memories(self) -> Dict[str, List[str]]:
        """列出所有记忆"""
        result = {
            "habits": [],
            "products": [],
            "skin_history": [],
            "personal": [],
        }

        path = self.feedback_dir / "preferences.md"
        if not path.exists():
            return result

        content = path.read_text(encoding="utf-8")
        current_section = None

        for line in content.split("\n"):
            if "## 护肤习惯" in line:
                current_section = "habits"
            elif "## 产品经验" in line:
                current_section = "products"
            elif "## 皮肤问题历史" in line:
                current_section = "skin_history"
            elif "## 个人偏好" in line:
                current_section = "personal"
            elif line.startswith("- ") and current_section:
                result[current_section].append(line[2:])

        return result


# 全局记忆系统实例
_memory: Optional[MemorySystem] = None


def get_memory() -> MemorySystem:
    """获取全局记忆系统实例"""
    global _memory
    if _memory is None:
        _memory = MemorySystem()
    return _memory