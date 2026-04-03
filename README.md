# Companion-Agent

本项目是一个运行在本地命令行中的 **AI 美妆陪伴助手**，基于 Python 实现，兼容 OpenAI 风格接口，支持自定义 `API Key`、`Base URL` 和模型名称。

它面向护肤/美妆陪伴场景，提供：

- 护肤打卡与习惯追踪
- 产品推荐与预算分档
- 情感陪伴式对话
- 用户记忆提取与长期记忆存储
- 四级上下文压缩机制
- Skill 可扩展架构
- AsyncGenerator / yield 流式交互模式

---

## 1. 功能特性

### 护肤习惯追踪
- 支持晨间 / 晚间护肤打卡
- 支持查看打卡统计
- 支持皮肤状态记录
- 支持连续打卡信息展示

### 产品推荐
- 根据需求推荐护肤品
- 支持预算档位推荐
- 支持美白、保湿、防晒、抗衰等类别

### 情感陪伴
- 支持自由对话
- 支持人格切换
- 内置多种人格：
  - 专业顾问
  - 美妆闺蜜
  - 知心大姐姐
  - 毒舌达人

### 用户记忆提取机制
- 自动从用户输入中提取长期偏好和经验
- 支持提取：
  - 护肤习惯
  - 产品经验
  - 皮肤问题历史
  - 个人偏好
- 支持通过命令查看记忆内容

### 四级压缩机制
- **Snip**：手动裁剪旧内容
- **MicroCompact**：基于时间的微压缩
- **Collapse**：基于 LLM 的摘要折叠
- **AutoCompact**：极限上下文自动压缩

### Skill 扩展架构
- Skill 基类统一接口
- 注册中心统一管理
- 内置 Habit / Product / Companion 三类 Skill
- 可扩展自定义 Skill

---

## 2. 技术栈

- **Python 3.10+**
- **OpenAI SDK**（兼容 OpenAI 风格 API）
- **Rich**（命令行美化）
- **SQLite3**（对话、打卡、日志数据）
- **Markdown/JSON**（用户档案与知识存储）
- **AsyncGenerator / yield**（流式交互输出）

---

## 3. 项目结构

```text
Companion-Agent/
├── main.py                         # 程序入口
├── agent.py                        # Agent 核心引擎
├── llm_adapter.py                  # OpenAI 兼容接口适配层
├── config.py                       # 配置加载
├── config.json                     # 用户配置
├── database.py                     # SQLite 存储层
├── memory.py                       # 用户记忆系统
├── compress.py                     # 四级压缩系统
├── events.py                       # 事件系统
├── requirements.txt                # 项目依赖
├── .gitignore
├── skills/
│   ├── __init__.py
│   ├── base.py                     # Skill 基类 / 注册中心
│   └── builtins/
│       ├── habit_skill.py          # 习惯追踪 Skill
│       ├── product_skill.py        # 产品推荐 Skill
│       └── companion_skill.py      # 陪伴对话 Skill
├── data/
│   ├── memory.db                   # SQLite 数据库
│   ├── memory_index.md             # 记忆索引
│   └── memory/
│       ├── user/
│       ├── feedback/
│       ├── project/
│       └── reference/
└── 美妆AI陪伴助手PRD.md             # 产品需求文档
```

---

## 4. 快速开始

### 4.1 安装依赖

```bash
pip install -r requirements.txt
```

### 4.2 配置环境变量

在项目根目录创建 `.env`：

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://your-base-url/v1
OPENAI_MODEL=your-model-name
TEMPERATURE=0.7
MAX_TOKENS=2000
LOG_LEVEL=INFO
```

### 4.3 启动项目

Windows 下建议使用 UTF-8：

```bash
python -X utf8 main.py
```

---

## 5. 常用命令

```bash
/help                # 查看帮助
/checkin morning     # 晨间打卡
/checkin evening     # 晚间打卡
/stats               # 查看护肤打卡统计
/log                 # 记录皮肤状态
/personality         # 查看人格选项
/personality set 美妆闺蜜
/profile             # 查看用户档案
/memories            # 查看用户记忆
/snip                # 裁剪旧上下文
/compress            # 手动触发压缩
/compress_stats      # 查看压缩统计
/skills              # 查看已加载技能
/history             # 查看历史对话
/clear               # 清空对话
/exit                # 退出程序
```

---

## 6. 核心设计说明

### 6.1 Agent 核心引擎

Agent 负责：

1. 接收用户输入
2. 匹配 Skill
3. 调用 LLM
4. 保存上下文和历史
5. 自动提取用户记忆
6. 在上下文过长时触发压缩

当前实现采用 **AsyncGenerator + yield** 模式，支持流式输出响应。

### 6.2 Skill 系统

Skill 系统使用统一接口：

- `should_activate()`：判断是否命中当前输入
- `execute()`：执行对应技能逻辑

当前内置：

- `HabitSkill`
- `ProductSkill`
- `CompanionSkill`

### 6.3 用户记忆提取机制

系统会自动识别用户输入中的长期信息，并写入本地 Markdown 记忆文件。

例如：

- “我习惯晚上用珂润面霜” → 护肤习惯
- “我之前用 Olay 小白瓶效果不错” → 产品经验
- “我不喜欢太香的产品” → 个人偏好

### 6.4 四级压缩系统

当上下文变长时，系统支持以下策略：

- **Snip**：删除不再需要的旧工具结果
- **MicroCompact**：超时后清理旧结果
- **Collapse**：使用 LLM 摘要压缩旧对话
- **AutoCompact**：只保留核心信息和最近轮次

---

## 7. 数据存储

### SQLite
用于存储：
- 对话历史
- 打卡记录
- 皮肤日志
- 产品记录

### Markdown / JSON
用于存储：
- 用户档案
- 用户偏好
- 项目状态
- 产品知识
- 护肤知识

所有数据默认保存在本地。

---

## 8. 使用示例

### 示例 1：打卡

```text
>> /checkin morning
```

### 示例 2：产品推荐

```text
>> 推荐一款美白精华
```

### 示例 3：切换人格

```text
>> /personality set 毒舌达人
```

### 示例 4：查看记忆

```text
>> /memories
```

---

## 9. 注意事项

- `.env` 已加入 `.gitignore`，不会自动提交 API Key
- 建议在支持 UTF-8 的终端中运行
- 当前为命令行版本，不包含图形界面
- 产品推荐为演示性质，实际可继续扩展知识库和规则

---

## 10. 后续可扩展方向

- 流式 API 真正逐 token 输出
- 自定义 Skill 动态加载 / 卸载
- 更完整的用户档案初始化流程
- 更强的产品知识库和检索系统
- GUI / Web UI 版本
- 定时提醒与周期报告

---

## 11. 项目来源

本项目根据产品文档 [美妆AI陪伴助手PRD.md](美妆AI陪伴助手PRD.md) 实现。

如果你希望，我还可以继续补：
- GitHub 首页徽章
- 截图区块
- “开发路线图”
- 更专业的开源说明
