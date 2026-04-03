"""配置加载模块"""
import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """应用配置"""
    # OpenAI 配置
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    log_level: str = "INFO"

    # 用户配置
    user_id: str = "default"
    skin_type: Optional[str] = None
    skin_concerns: list = None
    age_range: Optional[str] = None
    budget: str = "中端"
    personality: str = "美妆闺蜜"
    reminder_enabled: bool = False
    reminder_time: str = "20:00"
    language: str = "zh-CN"

    def __post_init__(self):
        if self.skin_concerns is None:
            self.skin_concerns = []


def load_env() -> dict:
    """从 .env 文件加载环境变量"""
    env_path = Path(__file__).parent / ".env"
    env_vars = {}

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()

    return env_vars


def load_config() -> Config:
    """加载完整配置"""
    env_vars = load_env()

    # 加载用户配置
    config_path = Path(__file__).parent / "config.json"
    user_config = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)

    user_data = user_config.get("user", {})
    prefs_data = user_config.get("preferences", {})

    return Config(
        openai_api_key=env_vars.get("OPENAI_API_KEY", ""),
        openai_base_url=env_vars.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_model=env_vars.get("OPENAI_MODEL", "gpt-4"),
        temperature=float(env_vars.get("TEMPERATURE", "0.7")),
        max_tokens=int(env_vars.get("MAX_TOKENS", "2000")),
        log_level=env_vars.get("LOG_LEVEL", "INFO"),
        user_id=user_data.get("user_id", "default"),
        skin_type=user_data.get("skin_type"),
        skin_concerns=user_data.get("skin_concerns", []),
        age_range=user_data.get("age_range"),
        budget=user_data.get("budget", "中端"),
        personality=user_data.get("personality", "美妆闺蜜"),
        reminder_enabled=prefs_data.get("reminder_enabled", False),
        reminder_time=prefs_data.get("reminder_time", "20:00"),
        language=prefs_data.get("language", "zh-CN"),
    )


def save_user_config(config: Config, config_path: str = None):
    """保存用户配置"""
    if config_path is None:
        config_path = Path(__file__).parent / "config.json"

    user_config = {
        "user": {
            "user_id": config.user_id,
            "skin_type": config.skin_type,
            "skin_concerns": config.skin_concerns,
            "age_range": config.age_range,
            "budget": config.budget,
            "personality": config.personality,
        },
        "preferences": {
            "reminder_enabled": config.reminder_enabled,
            "reminder_time": config.reminder_time,
            "language": config.language,
        }
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(user_config, f, ensure_ascii=False, indent=2)


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = load_config()
    return _config