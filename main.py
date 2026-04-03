#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""美妆AI陪伴助手 - 主程序 - AsyncGenerator模式"""
import asyncio
import sys
import io

# 设置控制台编码为UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from pathlib import Path
from typing import AsyncGenerator

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from config import get_config, load_env
from agent import Agent, get_agent
from database import get_database
from events import get_event_hub, EventType, Event


console = Console()


def print_banner():
    """打印欢迎界面"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              🌸 Beauty AI Companion 🌸                   ║
║                                                           ║
║           您的私人美妆护肤AI助手                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    if HAS_RICH:
        rprint(banner)
    else:
        print(banner)


async def init_app():
    """初始化应用"""
    print("Loading...")

    # 加载配置
    config = get_config()

    if not config.openai_api_key or config.openai_api_key == "your-api-key-here":
        console.print("[yellow]⚠️ 请先在 .env 文件中配置 OPENAI_API_KEY[/yellow]")
        console.print("[dim]示例：[/dim]")
        console.print("[dim]OPENAI_API_KEY=sk-your-api-key[/dim]")
        console.print("[dim]OPENAI_BASE_URL=https://api.openai.com/v1[/dim]")
        return None

    print("✓ 配置加载完成")

    # 初始化数据库
    db = get_database()
    print("✓ 数据库初始化完成")

    # 初始化事件中心
    event_hub = get_event_hub()
    print("✓ 事件系统初始化完成")

    # 测试连接
    try:
        from llm_adapter import get_llm
        llm = get_llm()
        test_result = llm.chat([{"role": "user", "content": "hi"}])
        if "error" in test_result:
            console.print(f"[yellow]⚠️ AI服务连接警告: {test_result['error']}[/yellow]")
        else:
            print("✓ 连接成功！")
    except Exception as e:
        console.print(f"[yellow]⚠️ AI服务连接警告: {str(e)}[/yellow]")

    # 初始化Agent
    agent = get_agent()
    skills = agent.registry.list_skills()
    print(f"✓ 已加载 Skills: {', '.join([s['name'] for s in skills])}")

    return agent


async def chat_stream(agent: Agent, user_input: str) -> AsyncGenerator[str, None]:
    """
    聊天流 - 使用async generator
    通过yield逐步获取AI响应
    """
    async for chunk in agent.process_stream(user_input):
        yield chunk


async def main():
    """主函数 - 使用AsyncGenerator模式"""
    print_banner()

    # 初始化
    agent = await init_app()
    if not agent:
        console.print("\n[red]初始化失败，请检查配置后重试[/red]")
        return

    console.print()

    # 打印欢迎信息
    personality = agent.config.personality
    greetings = {
        "专业顾问": "你好，我是你的专业美妆护肤顾问。有什么护肤问题可以问我~",
        "美妆闺蜜": "嗨~我是你的美妆闺蜜🌸 有什么想聊的吗？",
        "知心大姐姐": "你好呀~我是知心大姐姐，有什么心事可以跟我说哦~",
        "毒舌达人": "来了来了~我是毒舌美妆博主，有话直说！",
    }

    greeting = greetings.get(personality, "你好！我是你的美妆护肤AI助手 🌸")

    if HAS_RICH:
        rprint(Panel(greeting, title="AI助手", border_style="magenta"))
    else:
        print(greeting)

    console.print()
    console.print("[dim]我可以帮你：[/dim]")
    console.print("  • 记录护肤打卡、追踪习惯")
    console.print("  • 推荐护肤品和替代方案")
    console.print("  • 陪你聊天、给你鼓励")
    console.print("  • 更多技能可通过 /skills 查看")
    console.print()
    console.print("[dim]有什么我可以帮你的吗？可以直接输入你的问题或需求~[/dim]")
    console.print()

    # 主循环 - 使用async generator
    while True:
        try:
            user_input = input(">> ").strip()

            if not user_input:
                continue

            # 退出命令
            if user_input.lower() in ["/exit", "/quit", "退出", "exit", "quit"]:
                console.print("\n[magenta]再见~ 有需要随时找我哦！🌸[/magenta]\n")
                break

            # 使用async generator处理输入
            console.print()
            full_response = ""

            async for chunk in chat_stream(agent, user_input):
                # 过滤事件标记
                if chunk.startswith("["):
                    if chunk == "[EXIT]":
                        console.print("\n[magenta]再见~ 有需要随时找我哦！🌸[/magenta]\n")
                        return
                    continue

                # 流式输出
                full_response += chunk
                if HAS_RICH:
                    rprint(f"[cyan]{chunk}[/cyan]", end="")
                else:
                    print(chunk, end="", flush=True)

            console.print()
            console.print()

        except KeyboardInterrupt:
            console.print("\n\n[magenta]再见~ 有需要随时找我哦！🌸[/magenta]\n")
            break
        except Exception as e:
            console.print(f"\n[red]发生错误: {str(e)}[/red]\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        console.print(f"[red]启动失败: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")