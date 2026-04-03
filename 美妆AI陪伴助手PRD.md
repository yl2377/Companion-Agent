# 美妆AI陪伴私人助手 - 产品需求文档 (PRD)

**文档版本**: v1.1
**创建日期**: 2026-04-02
**作者**: Claude
**状态**: 草稿

---

## 1. 产品概述

### 1.1 产品定位

一款运行在本地命令行终端的AI美妆个人护理陪伴助手，融合习惯养成、产品推荐、情感陪伴三大核心功能，通过自研Agent框架调用大语言模型，为用户提供个性化的护肤陪伴体验。

### 1.2 核心价值

- **习惯养成追踪**：智能提醒早晚护肤流程，记录护肤打卡
- **产品推荐**：根据用户需求和预算推荐护肤品
- **情感陪伴**：根据用户设定的AI人格进行温暖对话
- **Skill扩展**：模块化的Skill系统，用户可自行添加教程
- **本地隐私保护**：所有数据存储在本地，不上传云端

### 1.3 目标用户

- 18-50岁有护肤需求的女性用户
- 对美妆护肤有兴趣，但缺乏系统知识的用户
- 希望能获得个性化建议和持续陪伴的用户

---

## 2. 技术架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI 交互层                                │
│                   (Python Console / Rich)                       │
├─────────────────────────────────────────────────────────────────┤
│                      Agent 核心引擎                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐   │
│  │ 事件驱动    │ │ 工具系统    │ │ 推理引擎                │   │
│  │ EventHub    │ │ ToolRegistry│ │ (ReAct)                │   │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                         Skill 系统                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Skill 注册中心 (动态加载)                   │   │
│  │  内置 Skill: 习惯追踪 | 产品推荐 | 情感陪伴              │   │
│  │  用户自定义 Skill: 教程、技能等                          │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                    Memory System (记忆系统)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐   │
│  │ 工作记忆    │ │ 情景记忆    │ │ 长期记忆                │   │
│  │ (上下文)    │ │ (SQLite)    │ │ (Markdown)              │   │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     LLM Adapter Layer                           │
│              (OpenAI API - 自定义 BaseURL)                      │
├─────────────────────────────────────────────────────────────────┤
│                     存储层 (混合方案)                            │
│    ┌─────────────┐                    ┌─────────────┐          │
│    │  Markdown  │                    │   SQLite    │          │
│    │  用户档案   │                    │ 对话历史    │          │
│    │  配置文件   │                    │ 打卡记录    │          │
│    │  产品知识库 │                    │ 皮肤日志    │          │
│    └─────────────┘                    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 模块 | 技术选型 | 说明 |
|------|----------|------|
| 编程语言 | Python 3.10+ | 主要开发语言 |
| LLM 调用 | OpenAI SDK | 用户提供 API Key 和 BaseURL |
| CLI 美化 | Rich | 终端输出美化 |
| 存储 - 结构化数据 | sqlite3 (原生) | 对话历史、打卡记录等 |
| 存储 - 用户数据 | Markdown/JSON | 用户档案、配置等 |
| 向量检索 | 内置简单实现 | 轻量级语义检索 |
| 异步 | asyncio (原生) | Python 内置异步 |
| 配置管理 | pydantic | 数据校验 |
| 依赖管理 | pip | Python 包管理 |

### 2.3 配置说明

用户需在配置文件中提供：

```python
# config/settings.py 或 .env 文件

OPENAI_API_KEY = "用户自己的api key"      # OpenAI API Key
OPENAI_BASE_URL = "用户自己的baseurl"      # API 代理地址
OPENAI_MODEL = "gpt-4"                     # 使用的模型
```

支持的 BaseURL 示例：
- OpenAI 官方: `https://api.openai.com/v1`
- OpenAI 代理: `https://api.x.com/v1`（用户自定义）
- 其他兼容 API: `https://<your-endpoint>/v1`

---

## 3. 功能模块

### 3.1 功能架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                      功能模块树                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ├── 1. 习惯追踪模块                                        │
│  │     ├── 1.1 护肤打卡                                    │
│  │     │     ├── 晨间护肤打卡                               │
│  │     │     ├── 晚间护肤打卡                               │
│  │     │     └── 自定义打卡项                               │
│  │     ├── 1.2 习惯提醒                                    │
│  │     │     ├── 定时提醒（需手动查看）                     │
│  │     │     └── 周期性总结                                 │
│  │     ├── 1.3 进度统计                                    │
│  │     │     ├── 连续打卡天数                               │
│  │     │     └── 月度打卡率                                 │
│  │     └── 1.4 周期记录                                    │
│  │           ├── 皮肤状态记录                               │
│  │           └── 使用产品记录                               │
│  │                                                           │
│  ├── 2. 产品推荐模块                                        │
│  │     ├── 2.1 需求匹配                                     │
│  │     │     └── 根据用户需求推荐产品                      │
│  │     ├── 2.2 预算规划                                     │
│  │     │     └── 根据预算推荐不同价位产品                   │
│  │     └── 2.3 替代方案                                    │
│  │           └── 推荐性价比替代产品                         │
│  │                                                           │
│  ├── 3. 情感陪伴模块                                        │
│  │     ├── 3.1 日常对话                                     │
│  │     │     ├── 闲聊模式                                   │
│  │     │     └── 情绪倾听                                   │
│  │     ├── 3.2 鼓励支持                                    │
│  │     │     ├── 护肤动力激励                               │
│  │     │     └── 积极心理引导                               │
│  │     └── 3.3 人格设定                                    │
│  │           ├── 预设人格切换                               │
│  │           └── 自定义人格                                 │
│  │                                                           │
│  └── 4. Skill 系统 (扩展模块)                               │
│        ├── 4.1 Skill 注册中心                              │
│        │     └── 动态加载 Skill                             │
│        ├── 4.2 Skill 基类定义                              │
│        │     └── 统一的 Skill 接口                         │
│        ├── 4.3 内置 Skill                                  │
│        │     └── 习惯追踪、产品推荐、情感陪伴               │
│        └── 4.4 用户自定义 Skill                            │
│              └── 教程、技能等可扩展                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心功能详解

#### 3.2.1 习惯追踪模块

**功能描述**：帮助用户建立护肤习惯，记录追踪执行情况。

**子功能1.1：护肤打卡**

- **触发方式**：
  - 用户输入：「打卡」/「晨间护肤打卡」/「晚间打卡」
  - 命令：`/checkin morning` 或 `/checkin evening` 或 `/checkin`
- **交互流程**：
  1. 显示打卡选项或让用户确认
  2. 记录打卡时间和完成项目
  3. 给予鼓励反馈
- **输出示例**：
  ```
  ✅ 晨间护肤打卡完成！

  打卡时间：2026-04-02 08:30

  今日完成项目：
  ☑️ 洁面
  ☑️ 爽肤水
  ☑️ 精华
  ☑️ 面霜
  ☑️ 防晒

  📅 连续打卡：7天
  💪 太棒了！坚持就是胜利！
  ```

**子功能1.2：习惯提醒**

- **功能说明**：非强制推送，而是用户查询时提醒
- **提醒场景**：
  - 用户可设置每日提醒时间
  - 登录时提示「今天是护肤日，别忘了打卡哦」
  - 周期性总结

**子功能1.3：进度统计**

- **数据统计**：
  - 本周打卡天数
  - 本月打卡率
  - 最长连续打卡
- **输出示例**：
  ```
  📊 3月护肤习惯报告

  本月打卡：24/31天 (77%)
  晨间护肤：22次
  晚间护肤：20次

  连续最长：8天
  本周平均：6/7天

  继续保持！4月目标：28天 💪
  ```

**子功能1.4：周期记录**

- **皮肤状态记录**：
  - 用户可记录每日的皮肤状态（油光、痘痘、敏感等）
  - 配合打卡一起记录
- **产品使用记录**：
  - 记录使用的产品
  - 记录使用后的皮肤反应

#### 3.2.2 产品推荐模块

**功能描述**：根据用户需求和预算推荐产品。

**子功能2.1：需求匹配**

- **输入**：用户描述需求（想要美白、想要保湿等）
- **参考**：结合用户肤质和预算
- **输出**：推荐具体产品（可让用户自行购买）

**子功能2.2：预算规划**

- **预设预算档位**：
  - 入门级：100-200元
  - 中端：200-500元
  - 高端：500-1000元
  - 奢华：1000元以上
- **输出**：每个档位推荐1-2款

**子功能2.3：替代方案**

- 用户指定产品，Agent 给出类似效果的平价替代

#### 3.2.3 情感陪伴模块

**功能描述**：提供情感支持，扮演美妆闺蜜/顾问角色。

**子功能3.1：日常对话**

- **功能**：闲聊、倾听、回应
- **风格**：根据用户设定的人格进行对话

**子功能3.2：人格设定**

- **预设人格**：
  | 人格 | 特点 | 适用场景 |
  |------|------|----------|
  | 专业顾问 | 专业、详细、数据导向 | 需要严肃建议时 |
  | 美妆闺蜜 | 活泼、亲切、带emoji | 日常聊天 |
  | 知心大姐姐 | 温柔、倾听、鼓励 | 情绪低落时 |
  | 毒舌达人 | 犀利、直接、有趣 | 轻松氛围 |

- **切换方式**：
  - 输入：「切换人格」/「换一个性格」
  - 命令：`/personality set <人格名称>`
  - 或描述想要的感觉：「换个毒舌一点的风格」

- **自定义人格**：
  - 用户可以设定关键词描述理想人格
  - Agent 根据关键词调整回复风格

**子功能3.3：鼓励支持**

- 护肤动力激励
- 积极心理引导
- 打卡完成鼓励

#### 3.2.4 Skill 系统

**功能描述**：模块化的技能系统，支持动态加载和扩展。

**子功能4.1：Skill 注册中心**

- **功能**：管理所有 Skill 的注册和发现
- **特性**：
  - 自动发现 skills 目录下的 Skill
  - 运行时动态加载/卸载 Skill
  - Skill 版本管理

**子功能4.2：Skill 基类定义**

```python
class BaseSkill(ABC):
    """Skill 基类，所有自定义 Skill 继承此类"""
    
    name: str           # Skill 名称
    description: str    # Skill 描述
    version: str = "1.0.0"  # 版本号
    
    @abstractmethod
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行 Skill"""
        pass
    
    @abstractmethod
    async def should_activate(self, user_input: str, context: SkillContext) -> bool:
        """判断是否应该激活此 Skill"""
        pass
```

**子功能4.3：内置 Skill**

系统自带以下内置 Skill：

| Skill | 说明 |
|-------|------|
| `HabitSkill` | 习惯追踪（打卡、提醒、统计） |
| `ProductSkill` | 产品推荐（需求匹配、预算规划） |
| `CompanionSkill` | 情感陪伴（对话、鼓励、人格） |

**子功能4.4：用户自定义 Skill**

用户可以在 `skills/` 目录下创建自定义 Skill：

```
skills/
├── __init__.py
├── base.py              # Skill 基类
├── registry.py          # Skill 注册中心
├── builtins/           # 内置 Skill
│   ├── habit_skill.py
│   ├── product_skill.py
│   └── companion_skill.py
└── custom/             # 用户自定义 Skill（可选）
    ├── makeup_tutorial.py    # 妆容教程
    ├── skincare_tips.py      # 护肤小技巧
    └── ...
```

**自定义 Skill 示例**：

```python
# skills/custom/makeup_tutorial.py
from skills.base import BaseSkill, SkillContext, SkillResult

class MakeupTutorialSkill(BaseSkill):
    name = "makeup_tutorial"
    description = "妆容教程指导"
    version = "1.0.0"
    
    async def should_activate(self, user_input: str, context: SkillContext) -> bool:
        keywords = ["妆容", "化妆", "教程", "化妆步骤"]
        return any(kw in user_input for kw in keywords)
    
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        # 实现教程逻辑
        tutorial_type = kwargs.get("tutorial_type", "daily")
        # ... 返回教程内容
```

**Skill 加载命令**：

```bash
# 查看已加载的 Skill
/skills list

# 加载自定义 Skill
/skills load skills/custom/my_skill.py

# 卸载 Skill
/skills unload makeup_tutorial
```

---

## 4. 用户交互设计

### 4.1 启动流程

```bash
$ python main.py

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              🌸 Beauty AI Companion 🌸                   ║
║                                                           ║
║           您的私人美妆护肤AI助手                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Loading...
✓ 配置加载完成
✓ 正在连接AI服务...
✓ 连接成功！
✓ 已加载 Skills: habit_skill, product_skill, companion_skill

你好！我是你的美妆护肤AI助手 🌸

我可以帮你：
  • 记录护肤打卡、追踪习惯
  • 推荐护肤品和替代方案
  • 陪你聊天、给你鼓励
  • 更多技能可通过 /skills 查看

有什么我可以帮你的吗？可以直接输入你的问题或需求~

>>
```

### 4.2 命令系统

| 命令 | 说明 | 示例 |
|------|------|------|
| `/help` | 显示帮助 | `/help` |
| `/checkin [morning/evening]` | 护肤打卡 | `/checkin morning` |
| `/stats` | 查看统计 | `/stats` |
| `/log` | 记录皮肤状态 | `/log` |
| `/product` | 产品推荐 | `/product 美白` |
| `/personality set <人格>` | 切换人格 | `/personality set 毒舌` |
| `/personality list` | 查看可用人格 | `/personality list` |
| `/profile` | 查看用户档案 | `/profile` |
| `/skills` | 查看已加载的Skill | `/skills` |
| `/skills list` | 列出所有Skill | `/skills list` |
| `/skills load <path>` | 加载自定义Skill | `/skills load my_skill.py` |
| `/history [数量]` | 查看历史对话 | `/history 10` |
| `/clear` | 清除当前对话 | `/clear` |
| `/exit` / `/quit` | 退出程序 | `/exit` |

### 4.3 对话示例

```
>> 打卡

你好呀！请问是晨间护肤还是晚间护肤呢？

  [1] ☀️ 晨间护肤
  [2] 🌙 晚间护肤
  [3] 📝 自定义打卡


>> 1

✅ 晨间护肤打卡完成！

打卡时间：2026-04-02 08:30

今日完成项目：
☐ 洁面
☐ 爽肤水
☐ 精华
☐ 面霜
☐ 防晒

请回复完成的项目（用逗号分隔），直接回车跳过：
>> 洁面, 爽肤水, 精华, 面霜, 防晒

✅ 打卡完成！

  ☑️ 洁面
  ☑️ 爽肤水
  ☑️ 精华
  ☑️ 面霜
  ☑️ 防晒

📅 连续打卡：7天
💪 太棒了！坚持就是胜利！
```

```
>> 推荐一款美白精华

好的！让我帮你找一款适合的美白精华~

请问你的预算是？
  [1] 💰 100-200元（入门级）
  [2] 💰💰 200-500元（中端）
  [3] 💰💰💰 500-1000元（高端）
  [4] 💰💰💰💰 1000元以上（奢华）

>> 2

给你推荐几款中端价位的美白精华：

🌟 修丽可 CE 精华 (约510元)
   - 15%左旋维C + 1%维E + 0.5%阿魏酸
   - 抗氧化能力强

🌟 OLAY 淡斑小白瓶 (约280元)
   - 烟酰胺 + 酰本胺
   - 淡化斑点、提亮肤色

🌟 倩碧匀净淡斑精华 (约350元)
   - 302黑色素干预科技
   - 适合有色斑困扰的肌肤

需要我帮你详细了解哪一款？或者有其他价位需求？
```

```
>> 今天心情不好

哎呀，怎么啦？😊

不管发生什么，我都在这里陪你~

愿意跟我说说吗？或者我们可以聊聊天分散一下注意力 💭
```

### 4.4 错误处理

- **API 连接失败**：
  ```
  ⚠️ 无法连接到AI服务，请检查网络和配置

  常见解决方法：
  1. 确认 API Key 正确
  2. 确认 BaseURL 可访问
  3. 检查代理设置
  ```
- **请求超时**：
  ```
  ⏳ AI响应较慢，请稍候...
  ```
- **无效命令**：
  ```
  ❌ 未知命令，输入 /help 查看可用命令
  ```
- **Skill 加载失败**：
  ```
  ⚠️ Skill 加载失败: xxx
  请检查文件路径和语法是否正确
  ```

---

## 5. 数据设计

### 5.1 存储策略：Markdown + SQLite 混合方案

| 存储类型 | 格式 | 说明 |
|----------|------|------|
| 用户档案 | Markdown | 需要人工查看/编辑 |
| 配置文件 | Markdown/JSON | 偏好设置 |
| 对话历史 | SQLite | 大量数据、快速查询 |
| 打卡记录 | SQLite | 结构化、统计需求 |
| 皮肤日志 | SQLite | 按日期查询 |
| 产品知识库 | Markdown | 静态推荐知识 |

### 5.2 文件结构

```
data/
├── user_profile.md       # 用户档案（可直接编辑）
├── config.json           # 用户配置
├── products_knowledge.md # 产品知识库（可选）
├── memory.db             # SQLite 数据库
│   ├── conversations     # 对话历史表
│   ├── checkins         # 打卡记录表
│   └── skin_logs        # 皮肤日志表
└── logs/                # 运行日志
```

### 5.3 用户档案 (user_profile.md)

```markdown
# 用户档案

## 基本信息
- user_id: default
- created_at: 2026-04-02

## 肤质信息
- skin_type: 混合性
- skin_concerns: ["痘痘", "毛孔粗大"]
- age_range: 25-35

## 偏好
- budget: 中端
- personality: 美妆闺蜜
- reminder_enabled: false
```

### 5.4 对话历史 (conversations 表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| role | TEXT | user/assistant/system |
| content | TEXT | 对话内容 |
| tool_calls | TEXT | 调用的工具（JSON） |
| timestamp | REAL | 时间戳 |

### 5.5 打卡记录 (checkins 表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| checkin_type | TEXT | morning/evening/custom |
| items | TEXT | 完成的打卡项（JSON） |
| notes | TEXT | 备注 |
| timestamp | REAL | 时间戳 |

### 5.6 产品记录 (products)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | TEXT | 产品名称 |
| brand | TEXT | 品牌 |
| category | TEXT | 类别 |
| ingredients | TEXT | 成分（JSON） |
| skin_type | TEXT | 适用肤质 |
| rating | INTEGER | 用户评分 |
| notes | TEXT | 备注 |
| created_at | REAL | 添加时间 |

### 5.7 皮肤状态记录 (skin_logs)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| date | TEXT | 日期 |
| overall | TEXT | 总体状态 |
| oil_level | INTEGER | 油光程度(1-5) |
| moisture_level | INTEGER | 水分程度(1-5) |
| issues | TEXT | 问题（JSON数组） |
| notes | TEXT | 备注 |

---

## 6. Agent 核心设计

### 6.1 事件系统

参考 Claude Code 的生命周期事件设计：

```python
class EventType(Enum):
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
```

---

#### 6.1.1 钩子（Hook）系统

钩子是一种在特定时机插入自定义逻辑的机制，用于控制 Agent 行为、进行安全审查、对接外部系统等。

##### 钩子类型

| 类型 | 说明 | 可持久化 | 适用场景 |
|------|------|----------|----------|
| **prompt** | LLM 评估 | 是 | 需要"智能判断"的场景 |
| **agent** | Agentic 验证 | 是 | 需要多步验证的场景 |
| **http** | HTTP 调用 | 是 | 需要与外部系统集成的场景 |
| **function** | 运行时回调 | 否 | 需要深度运行时交互的场景 |

##### 触发时机

| 时机 | 说明 |
|------|------|
| **PreToolUse** | 工具执行前触发 |
| **PostToolUse** | 工具执行后触发 |
| **PreMessage** | 消息发送前触发 |
| **PostMessage** | 消息接收后触发 |

##### 钩子类型详解

**1. prompt（LLM 评估）**

使用 LLM 判断输入内容，适用于需要语义理解的场景。

```json
{
  "type": "prompt",
  "model": "MiniMax-M2.5",
  "prompt": "判断以下内容是否涉及敏感信息。输入：$ARGUMENTS"
}
```

适用场景：
- 判断产品推荐是否超出用户预算
- 判断用户输入是否包含敏感内容
- 判断修改是否涉及核心文件

---

**2. agent（Agentic 验证）**

启动子 Agent 进行多步验证，适用于复杂的多阶段检查。

```json
{
  "type": "agent",
  "agent_type": "reviewer",
  "task": "审查代码修改的安全性",
  "max_steps": 5
}
```

适用场景：
- 代码安全审查（多步骤分析）
- 复杂的产品推荐逻辑验证
- 多轮确认的用户意图理解

---

**3. http（HTTP 调用）**

调用外部 HTTP 接口，适用于与外部系统集成。

```json
{
  "type": "http",
  "method": "POST",
  "url": "https://audit.company.com/api/log",
  "headers": {
    "Authorization": "Bearer $TOKEN"
  },
  "payload": {
    "tool": "$TOOL_NAME",
    "arguments": "$ARGUMENTS",
    "timestamp": "$TIMESTAMP"
  }
}
```

适用场景：
- 操作日志上报审计系统
- 敏感操作通知管理员
- 外部知识库查询

---

**4. function（运行时回调）**

在 Python 运行时执行回调函数，适用于需要深度定制的场景。

```json
{
  "type": "function",
  "module": "hooks.custom",
  "function": "validate_skin_type",
  "args": ["$ARGUMENTS"]
}
```

适用场景：
- 自定义验证逻辑
- 实时数据处理
- 与本地系统交互

---

##### 选择钩子类型的决策树

```
需要选择钩子类型？
         │
         ▼
  需要深度运行时交互？
         │
    ┌────┴────┐
   是│         │否
    ▼         ▼
Function   需要与外部系统集成？
                 │
            ┌────┴────┐
           是│         │否
            ▼         ▼
          HTTP    需要智能判断？
                      │
                 ┌────┴────┐
                │         │
                ▼         ▼
             Prompt    Agent
                      (多步验证)
```

| 场景 | 推荐类型 |
|------|----------|
| 判断用户输入是否涉及敏感内容 | prompt |
| 代码修改前进行多步骤安全审查 | agent |
| 记录操作日志到审计系统 | http |
| 实时检查用户肤质数据 | function |

---

##### 美妆 Agent 的钩子配置示例

**示例1：产品推荐预算检查**

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "recommend_product",
      "hooks": [{
        "type": "prompt",
        "prompt": "判断这个产品推荐是否超出用户预算。
                   用户预算：$USER_BUDGET
                   推荐产品：$ARGUMENTS
                   如果超出预算，回复 {\"decision\": \"block\", \"reason\": \"超出预算\"}
                   否则回复 {\"decision\": \"approve\"}"
      }]
    }]
  }
}
```

**示例2：操作日志上报**

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": ".*",
      "hooks": [{
        "type": "http",
        "method": "POST",
        "url": "https://audit.example.com/api/agent-log",
        "payload": {
          "session_id": "$SESSION_ID",
          "tool": "$TOOL_NAME",
          "arguments": "$ARGUMENTS",
          "result": "$RESULT",
          "timestamp": "$TIMESTAMP"
        }
      }]
    }]
  }
}
```

**示例3：敏感内容检测**

```json
{
  "hooks": {
    "PreMessage": [{
      "matcher": ".*",
      "hooks": [{
        "type": "prompt",
        "prompt": "判断用户输入是否涉及以下内容：
                   1. 自杀倾向
                   2. 抑郁症倾向
                   3. 严重心理健康问题
                   如果涉及，回复 {\"alert\": true, \"action\": \"provide_resources\"}
                   否则回复 {\"alert\": false}"
      }]
    }]
  }
}
```

---

##### 钩子配置优先级

```
PreToolUse > PreMessage > PostMessage > PostToolUse
   ↓           ↓           ↓            ↓
  最先执行                 最后执行
```

### 6.2 Skill 系统架构

```python
@dataclass
class SkillContext:
    """Skill 执行上下文"""
    user_input: str
    user_id: str
    profile: UserProfile
    memory: MemorySystem
    llm: LLMAdapter

@dataclass
class SkillResult:
    """Skill 执行结果"""
    success: bool
    content: str
    should_respond: bool = True  # 是否需要Agent生成回复

class BaseSkill(ABC):
    """Skill 基类"""
    
    name: str           # 唯一标识
    description: str    # 功能描述
    version: str = "1.0.0"
    category: str      # 分类
    
    @abstractmethod
    async def should_activate(self, user_input: str, context: SkillContext) -> bool:
        """判断是否应该激活此 Skill"""
        pass
    
    @abstractmethod
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行 Skill"""
        pass

class SkillRegistry:
    """Skill 注册中心"""
    
    def __init__(self):
        self.skills: dict[str, BaseSkill] = {}
    
    def register(self, skill: BaseSkill):
        """注册 Skill"""
        self.skills[skill.name] = skill
    
    def discover(self, skills_dir: str = "skills"):
        """自动发现 Skill"""
        pass
    
    def get_skill(self, name: str) -> BaseSkill:
        return self.skills.get(name)
    
    async def match_skills(self, user_input: str, context: SkillContext) -> list[BaseSkill]:
        """匹配可能激活的 Skills"""
        matched = []
        for skill in self.skills.values():
            if await skill.should_activate(user_input, context):
                matched.append(skill)
        return matched
```

### 6.3 内置 Skill 列表

| Skill | 说明 |
|-------|------|
| `HabitSkill` | 习惯追踪 - 打卡、提醒、统计、皮肤记录 |
| `ProductSkill` | 产品推荐 - 需求匹配、预算规划、替代方案 |
| `CompanionSkill` | 情感陪伴 - 闲聊、情绪支持、人格管理 |

### 6.4 推理流程

```
用户输入
    ↓
Skill 匹配（所有已加载的 Skill 判断是否激活）
    ↓
┌──────────────────────────────────────┐
│  遍历匹配的 Skills                   │
│  执行 should_activate -> execute    │
└──────────────────────────────────────┘
    ↓
如果没有 Skill 匹配 → 通用对话（CompanionSkill）
    ↓
生成回复
    ↓
存储记忆
    ↓
返回结果
```

### 6.5 上下文管理（记忆分层策略）

当对话上下文接近模型限制时，采用四级渐进压缩方案：

```
┌─────────────────────────────────────────────────────────────┐
│                    上下文窗口构成                            │
├─────────────────────────────────────────────────────────────┤
│  1. 核心档案（固定不变）                                     │
│     - 用户肤质、预算、人格                                  │
│     - 来自 user_profile.md                                  │
│                                                             │
│  2. 长期记忆（多重机制）                                      │
│     ┌─────────────────────────────────────────────────────┐ │
│     │ a) 自动提取的用户记忆                               │ │
│     │    - 护肤习惯: "早晚都用珂润，晚上加敷面膜"          │ │
│     │    - 产品经验: "用过Olay小白瓶效果不错"               │ │
│     │    - 皮肤问题历史: "之前痘痘严重，用A醇好了"         │ │
│     │    - 偏好约定: "喜欢清爽质地，不要太香的"            │ │
│     │                                                     │ │
│     │ b) 重要交互记录                                     │ │
│     │    - 推荐过的产品及用户反馈                         │ │
│     │    - 打卡坚持情况                                   │ │
│     │    - 肤质变化记录                                   │ │
│     │                                                     │ │
│     │ c) 定期总结压缩                                    │ │
│     │    - 由 LLM 提取关键信息                            │ │
│     └─────────────────────────────────────────────────────┘ │
│                                                             │
│  3. 近期对话（滑动窗口）                                     │
│     - 最近 10-20 轮对话                                     │
│     - 保存在 SQLite                                         │
│                                                             │
│  4. 本次会话（实时）                                         │
│     - 当前会话的对话                                        │
└─────────────────────────────────────────────────────────────┘
```

---

#### 6.5.1 四级渐进压缩策略

参考 Claude Code 的压缩架构，采用四级渐进压缩机制：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        四级压缩升级路径                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Snip (裁剪)  ──→  MicroCompact (微压缩)  ──→  Collapse (折叠)  ──→  │
│                                                                         │
│   用户主动标记清除    时间触发自动清理          LLM摘要压缩              │
│   不需要的内容        缓存过期前预清理          保留关键信息              │
│                                                                         │
│                                                     ↓                   │
│                                              AutoCompact              │
│                                              (自动压缩)                │
│                                              最终兜底方案               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

**触发条件对比表**：

| 级别 | 触发方式 | 触发条件 | 压缩成本 | 信息损失 |
|------|----------|----------|----------|----------|
| **Snip** | 用户/命令 | 手动指定清除 | 0 (纯字符串) | 完全丢失 |
| **MicroCompact** | 自动 | 时间阈值（默认30分钟） | 0 (纯字符串) | 完全丢失 |
| **Collapse** | 自动 | token 阈值（剩余<30%） | LLM调用 | 转换为摘要 |
| **AutoCompact** | 自动 | token 阈值（剩余<15%） | LLM调用 | 激进压缩 |

---

##### Level 1: Snip（裁剪）

**功能**：用户主动标记不需要的工具结果，直接替换为标记文本。

**触发方式**：
- 用户输入命令：`/snip` 或 `清空工具结果`
- 用户切换话题（如"换个话题聊聊"）

**压缩方式**：
```
原始：tool result: (用户过去30天的皮肤日志，5000 tokens)
压缩：tool result: [Old tool result content cleared]
```

**保留内容**：
- 工具调用的 ID 保留（保持消息链完整）
- 仅清除结果内容

**适用场景**：
- 查完产品信息后，不需要再保留原始记录
- 分析完皮肤数据后，原始日志不再需要
- 用户明确表示"这个不需要了"

**为什么保留结构而非删除**：
- 后续消息可能引用了 tool_call_id
- 删除会导致消息链断裂

---

##### Level 2: MicroCompact（微压缩）

**功能**：基于时间触发的大规模工具结果清理。当检测到距离上一次助手消息的时间间隔超过配置阈值时，自动清除旧的工具结果。

**触发条件**：
- 距离上次助手消息 > 30分钟（可配置）
- 检测到用户长时间未操作

**触发原因**：API 提示缓存（Prompt Caching）过期
- 如果连续请求的前缀相同，缓存命中的部分可大幅降低成本
- 随着时间推移，缓存会过期
- 缓存过期时，旧的工具结果无论是否保留都需要重新发送
- 不如在请求之前主动清除，减小重写负载

**压缩方式**：
- 保留最近 N 个工具结果（config.keepRecent，默认2个）
- 其余工具结果内容全部替换为 `[Old tool result content cleared]`

**可压缩的工具类型**：
- Read（读取文件/记录）
- Bash（执行命令）
- Grep/Glob（搜索）
- WebSearch/WebFetch（网页查询）
- Edit/Write（写入操作）

**美妆场景示例**：

```
用户："推荐一款美白精华"
Agent → 查皮肤记录（tool_call_1）→ 查产品记录（tool_call_2）→ 推荐修丽可CE

（用户去吃饭，1小时没回来）

系统检测：距上次助手消息超过30分钟
         ↓
缓存可能已过期，旧的查询结果需要重新发送
         ↓
MicroCompact 触发：
- 保留 tool_call_2（最近1个）
- 清除 tool_call_1
         ↓
用户回来问："那个多少钱？"
Agent → 重新查一下价格 → 回答
```

---

##### Level 3: Collapse（折叠）

**功能**：调用 LLM 将旧的对话内容压缩为精简摘要，保留关键信息。

**触发条件**：
- 上下文 token 剩余 < 30%
- 或手动触发

**压缩方式**：
```
原始对话（5000 tokens）：
- 用户：我皮肤有点油
- Agent：建议用控油产品
- 用户：之前用过XX觉得干
- Agent：可能需要补水
- 用户：有痘痘怎么办
- ...

压缩后（200 tokens）：
用户混合肌，有痘痘困扰，之前用XX控油产品过干，
建议先补水再考虑控油，当前关注痘痘问题。
```

**保留内容**：
- 用户肤质和护肤目标
- 产品偏好和过敏信息
- 关键交互历史
- 打卡记录摘要

**与 Snip/MicroCompact 的区别**：
- Snip/MicroCompact：完全删除
- Collapse：LLM 提取关键信息，用摘要保留

---

##### Level 4: AutoCompact（自动压缩）

**功能**：四级压缩的最终兜底方案，当上下文即将耗尽时的激进压缩。

**触发条件**：
- 上下文 token 剩余 < 15%
- 前面三级压缩已无法满足需求

**压缩策略**：
- 保留：核心用户档案 + 最近3轮对话 + 长期记忆摘要
- 压缩：更早的对话内容
- 极端情况下可能需要省略部分对话历史

**降级原则**：
```
如果 Collapse 压缩后仍不足：
  → 保留核心档案 + 最近1轮对话
  → 丢弃所有工具结果
  → 仅保留长期记忆摘要
```

---

##### 压缩级别选择建议

| 会话类型 | 推荐的压缩策略 | 原因 |
|----------|----------------|------|
| **代码审查** | Snip + MicroCompact | 切换目标时清理旧文件记录 |
| **CI/CD 任务** | Collapse（每步后） | 线性流程，需保留关键链路 |
| **教学会话** | 禁用或极度保守 | 需要精确引用早期内容 |
| **美妆陪伴** | 四级渐进 | 日常对话，灵活压缩 |

**美妆场景的最佳实践**：
- 日常闲聊：MicroCompact（30分钟无操作后）
- 产品推荐后：Collapse（提取关键偏好）
- 长时间对话：AutoCompact（最终兜底）
- 用户切换话题：Snip（主动清理）

---

#### 6.5.2 用户记忆提取机制

LLM 会自动从用户输入中识别并提取以下类型的记忆：

| 类型 | 识别关键词 | 存储位置 |
|------|------------|----------|
| 护肤习惯 | "我习惯用"、"一直用"、"每天" | `data/memory/habits.md` |
| 产品经验 | "用过"、"用了半年"、"效果" | `data/memory/products.md` |
| 皮肤问题历史 | "之前"、"以前"、"后来" | `data/memory/skin_history.md` |
| 偏好约定 | "我喜欢"、"不要"、"讨厌" | `data/memory/preferences.md` |

**提取示例**：

```
用户输入: "我之前用Olay小白瓶美白效果不错，但后来皮肤有点敏感"

→ 自动提取：
# 产品经验记录

## Olay 美白精华
- 用户评价: 美白效果不错
- 问题: 后来有点敏感
- 时间: 2026年
```

---

#### 6.5.2 记忆类型体系（4类）

参考 Claude Code 的记忆架构，将记忆分为 4 种类型：

| 类型 | 回答什么问题 | 存储位置 | 示例 |
|------|--------------|----------|------|
| **user** | "用户是谁？" | `data/memory/user/` | 肤质、年龄、职业、背景 |
| **feedback** | "用户喜欢/讨厌什么？" | `data/memory/feedback/` | 偏好、不喜欢的产品、纠正 |
| **project** | "用户在做什么？" | `data/memory/project/` | 护肤目标、当前关注的肌肤问题 |
| **reference** | "东西在哪找？" | `data/memory/reference/` | 产品知识、护肤教程链接 |

**文件结构**：

```
data/
├── memory/
│   ├── user/                    # 用户画像
│   │   ├── user_profile.md      # 用户基本信息（肤质、预算、人格）
│   │   └── skin_type.md         # 肤质详细信息
│   ├── feedback/                # 用户偏好/纠正
│   │   ├── preferences.md       # 偏好约定（喜欢清爽质地等）
│   │   └── corrections.md       # 纠正记录（不要推荐XX品牌等）
│   ├── project/                 # 项目状态
│   │   ├── current_goal.md      # 当前护肤目标
│   │   └── session_summary.md   # 会话目标摘要
│   └── reference/               # 外部参考
│       ├── products.md          # 产品知识库
│       └── skincare_tips.md     # 护肤知识
└── memory_index.md              # 记忆索引文件
```

**各类型详解**：

1. **user（用户画像）**
   - 来源：用户主动填写（初始配置）+ 对话中自动补充
   - 用途：回答时调整语气和内容深度
   - 示例：用户是"成分党"→ 推荐时多讲成分；用户是"护肤小白"→ 解释基础概念

2. **feedback（行为偏好）**
   - 来源：用户明确表达的偏好或纠正
   - 用途：避免踩雷、投其所好
   - 示例：
     - "我不喜欢太香的" → 以后跳过浓香型产品
     - "上次用的XX过敏了" → 以后不推荐含相同成分的产品

3. **project（项目状态）**
   - 来源：当前会话目标 + 长期护肤目标
   - 用途：聚焦当前任务，不偏离目标
   - 示例：
     - 近期目标："正在祛痘"
     - 长期目标："抗衰老"

4. **reference（外部参考）**
   - 来源：产品知识库、护肤知识文档
   - 用途：检索相关信息
   - 示例：
     - 美白成分科普 → 烟酰胺、维C、377 等
     - 品牌评价记录 → 用户反馈过的产品

**记忆索引文件（memory_index.md）**：

```markdown
# 记忆索引

## user
- [用户基本信息](memory/user/user_profile.md)
- [肤质详情](memory/user/skin_type.md)

## feedback
- [偏好约定](memory/feedback/preferences.md)
- [产品纠正](memory/feedback/corrections.md)

## project
- [当前目标](memory/project/current_goal.md)
- [会话摘要](memory/project/session_summary.md)

## reference
- [产品知识库](memory/reference/products.md)
- [护肤知识](memory/reference/skincare_tips.md)
```

**检索机制**：
- 在构建上下文时，根据当前话题检索相关记忆
- 例如：推荐美白产品 → 自动加载 `reference/products.md` + `feedback/preferences.md`（过滤不喜欢的成分）
- 例如：用户提到"想祛痘" → 加载 `project/current_goal.md`（聚焦祛痘相关建议）

**检索机制**：
- 在构建上下文时，根据当前话题检索相关用户记忆
- 例如：推荐美白产品 → 自动加载用户用过的美白产品和反馈

**触发机制**：
- 当上下文剩余 < 20% 时，自动触发总结
- 总结后的内容存储为"长期记忆摘要"
- 保留核心档案不变

**总结示例**：
```
原始对话（100+轮）→ 压缩为：
"用户混合肌，有痘痘困扰，推荐过OLAY小白瓶和修丽可CE，
  已连续打卡7天，今晚想换美白精华，偏好活泼人格"
```

### 6.6 提示词策略

**系统提示词结构**：

```
你是[人格设定]，一位温暖的美妆护肤陪伴助手。

用户信息：
- 预算：[budget]
- 打卡习惯：[habit_summary]

回复要求：
- [人格对应的回复风格]
- 适当使用emoji
- 温暖亲切
- 根据用户习惯给出鼓励

可用 Skills：
- [列出当前加载的 Skills]
```

---

## 7. 配置文件格式

### 7.1 环境配置 (.env)

```bash
# OpenAI 配置（必需）
OPENAI_API_KEY=sk-xxxxx
OPENAI_BASE_URL=https://api.xxxx.com/v1
OPENAI_MODEL=gpt-4

# 可选配置
TEMPERATURE=0.7
MAX_TOKENS=2000

# 日志
LOG_LEVEL=INFO
```

### 7.2 用户配置 (config.json)

```json
{
  "user": {
    "user_id": "default",
    "skin_type": null,
    "skin_concerns": [],
    "age_range": null,
    "budget": "中端",
    "personality": "美妆闺蜜"
  },
  "preferences": {
    "reminder_enabled": false,
    "reminder_time": "20:00",
    "language": "zh-CN"
  }
}
```

---

## 8. 非功能需求

### 8.1 性能要求

- 首次响应时间：< 5秒（网络正常情况下）
- 命令执行：< 1秒
- 内存占用：< 200MB

### 8.2 可靠性

- 网络断开时给出友好提示
- 本地数据定期备份（SQLite文件）
- 异常操作有错误提示

### 8.3 扩展性

- 模块化设计，易于添加新功能
- Skill 系统支持动态加载
- 提示词可自定义修改

---

## 9. 开发计划

### Phase 1：核心框架

- [ ] 项目结构搭建
- [ ] 基础配置系统
- [ ] LLM 适配器（支持自定义BaseURL）
- [ ] 基础对话循环
- [ ] 事件系统

### Phase 2：Skill 系统

- [ ] Skill 基类定义
- [ ] Skill 注册中心
- [ ] Skill 自动发现机制
- [ ] Skill 动态加载/卸载

### Phase 3：内置 Skills

- [ ] HabitSkill - 习惯追踪
- [ ] ProductSkill - 产品推荐
- [ ] CompanionSkill - 情感陪伴

### Phase 4：记忆系统

- [ ] SQLite 数据库设计
- [ ] 用户档案管理
- [ ] 对话历史存储

### Phase 5：完善优化

- [ ] 错误处理优化
- [ ] 输出格式美化
- [ ] 文档完善

---

## 10. 附录

### 10.1 术语表

| 术语 | 说明 |
|------|------|
| Agent | AI代理/智能体 |
| Skill | 技能模块，可独立加载的功能单元 |
| ReAct | 推理+行动模式 |
| Tool | 工具，Agent可调用的功能模块 |
| Memory | 记忆系统 |
| Persona | 人格设定 |
| 记忆类型 | 4种：user（用户画像）、feedback（偏好纠正）、project（项目状态）、reference（外部参考） |
| Snip | 裁剪，用户主动标记清除不需要的工具结果 |
| MicroCompact | 微压缩，基于时间触发的自动清理 |
| Collapse | 折叠，LLM摘要压缩 |
| AutoCompact | 自动压缩，最终兜底方案 |
| Hook | 钩子，在特定时机插入的自定义检查/处理逻辑 |
| Prompt Hook | 使用 LLM 评估的钩子类型 |
| Agent Hook | 使用子 Agent 验证的钩子类型 |
| HTTP Hook | 调用外部 HTTP 接口的钩子类型 |
| Function Hook | 运行时回调的钩子类型 |

### 10.2 参考资料

- Claude Code 架构：https://lintsinghua.github.io/
- OpenClaw 项目：https://github.com/openclaw/openclaw
- OpenAI API 文档

### 10.3 常见问题

**Q: 如何获取 API Key？**
A: 用户需要自行注册 OpenAI 账号或在代理平台获取。

**Q: 支持哪些模型？**
A: 支持所有 OpenAI 兼容的模型，如 GPT-4、GPT-3.5-Turbo 等。

**Q: 数据存储在哪里？**
A: 所有数据存储在本地 SQLite 数据库中，不会上传。

**Q: 可以离线使用吗？**
A: 需要联网调用 LLM API，本地数据可离线访问。

**Q: 如何添加自定义 Skill？**
A: 在 `skills/custom/` 目录下创建继承自 `BaseSkill` 的类，Agent 会自动发现并加载。

---

**文档结束**