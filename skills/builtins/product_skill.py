"""产品推荐Skill"""
from skills.base import BaseSkill, SkillContext, SkillResult
from memory import get_memory


class ProductSkill(BaseSkill):
    """产品推荐Skill - 需求匹配、预算规划、替代方案"""

    name = "product_skill"
    description = "产品推荐 - 根据需求推荐护肤品"
    version = "1.0.0"
    category = "product"

    # 产品知识库
    PRODUCTS = {
        "美白": {
            "入门级": [
                {"name": "OLAY淡斑小白瓶", "price": "约280元", "highlights": "烟酰胺+酰本胺，淡化斑点"},
                {"name": "The Ordinary维C精华", "price": "约100元", "highlights": "23%左旋维C悬浮液"},
            ],
            "中端": [
                {"name": "修丽可CE精华", "price": "约510元", "highlights": "15%左旋维C+维E+阿魏酸"},
                {"name": "倩碧匀净淡斑精华", "price": "约350元", "highlights": "302黑色素干预科技"},
            ],
            "高端": [
                {"name": "修丽可RBE精华", "price": "约800元", "highlights": "白藜芦醇+维E"},
                {"name": "赫莲娜绿宝瓶", "price": "约980元", "highlights": "海洋堇原生细胞"},
            ],
            "奢华": [
                {"name": "赫莲娜镭射精华", "price": "约1500元", "highlights": "超精准淡斑"},
                {"name": "莱伯妮鱼子酱精华", "price": "约2000元", "highlights": "鱼子酱科技"},
            ],
        },
        "保湿": {
            "入门级": [
                {"name": "珂润面霜", "price": "约150元", "highlights": "神经酰胺保湿"},
                {"name": "丝塔芙保湿霜", "price": "约120元", "highlights": "温和保湿"},
            ],
            "中端": [
                {"name": "修丽可B5精华", "price": "约380元", "highlights": "透明质酸+维B5"},
                {"name": "雅诗兰黛小棕瓶", "price": "约590元", "highlights": " Chronolux™科技"},
            ],
            "高端": [
                {"name": "海蓝之谜经典面霜", "price": "约1700元", "highlights": "神奇活性精粹"},
                {"name": "莱伯妮鱼子酱面霜", "price": "约2800元", "highlights": "鱼子酱紧致"},
            ],
        },
        "防晒": {
            "入门级": [
                {"name": "碧柔防晒", "price": "约80元", "highlights": "清爽不油腻"},
                {"name": "曼秀雷敦新碧", "price": "约70元", "highlights": "防晒保湿"},
            ],
            "中端": [
                {"name": "资生堂安耐晒", "price": "约200元", "highlights": "防水防汗"},
                {"name": "芳珂防晒", "price": "约180元", "highlights": "物理防晒，温和"},
            ],
            "高端": [
                {"name": "修丽可防晒", "price": "约400元", "highlights": "物化结合"},
                {"name": "兰蔻防晒", "price": "约480元", "highlights": "轻薄养肤"},
            ],
        },
        "抗衰老": {
            "入门级": [
                {"name": "露得清A醇晚霜", "price": "约150元", "highlights": "视黄醇抗皱"},
                {"name": "The Ordinary Buffet", "price": "约150元", "highlights": "多肽抗衰老"},
            ],
            "中端": [
                {"name": "修丽可紫米精华", "price": "约380元", "highlights": "10%玻尿酸胜肽"},
                {"name": "倩碧智慧修护精华", "price": "约450元", "highlights": "黄金配方"},
            ],
            "高端": [
                {"name": "修丽可AGE面霜", "price": "约700元", "highlights": "30%玻色因"},
                {"name": "赫莲娜黑绷带", "price": "约3000元", "highlights": "30%玻色因"},
            ],
        },
    }

    async def should_activate(self, user_input: str, context: SkillContext) -> bool:
        """判断是否应该激活"""
        input_lower = user_input.lower()

        # 产品推荐相关关键词
        keywords = [
            "推荐", "产品", "精华", "面霜", "防晒",
            "美白", "保湿", "抗老", "祛痘", "控油",
            "哪个好", "有什么", "买什么"
        ]
        return any(kw in input_lower for kw in keywords)

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行产品推荐"""
        user_input = context.user_input

        # 提取需求类型
        category = self._extract_category(user_input)

        if not category:
            # 无法识别类别，询问用户
            content = """你想了解哪类护肤品呢？

  [1] 💡 美白提亮
  [2] 💧 保湿补水
  [3] ☀️ 防晒隔离
  [4] ⏰ 抗衰老
  [5] 🧴 祛痘控油
  [6] ❓ 其他/推荐

可以直接回复选项或输入你想要的功效 ~
"""
            return SkillResult(
                success=True,
                content=content,
                should_respond=False,
                action="awaiting_category",
            )

        # 获取用户预算
        budget = kwargs.get("budget")
        if not budget:
            # 询问预算
            content = f"你想了解{category}产品，请选择你的预算：\n\n"
            budget_levels = [
                "💰 100-200元（入门级）",
                "💰💰 200-500元（中端）",
                "💰💰💰 500-1000元（高端）",
                "💰💰💰💰 1000元以上（奢华）",
            ]
            content += "\n".join([f"  [{i+1}] {b}" for i, b in enumerate(budget_levels)])
            content += "\n\n请回复选项或直接输入预算范围"

            return SkillResult(
                success=True,
                content=content,
                should_respond=False,
                action="awaiting_budget",
            )

        # 推荐产品
        content = self._recommend_products(category, budget)
        return SkillResult(success=True, content=content)

    def _extract_category(self, user_input: str) -> str:
        """提取产品类别"""
        user_input_lower = user_input.lower()

        category_keywords = {
            "美白": ["美白", "提亮", "淡斑", "去黄"],
            "保湿": ["保湿", "补水", "润肤"],
            "防晒": ["防晒", "隔离", "防紫外线"],
            "抗衰老": ["抗老", "抗皱", "紧致", "提拉"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in user_input_lower for kw in keywords):
                return category

        return None

    def _recommend_products(self, category: str, budget: str) -> str:
        """推荐产品"""
        # 解析预算
        budget_map = {
            "1": "入门级",
            "2": "中端",
            "3": "高端",
            "4": "奢华",
        }

        if budget in budget_map:
            budget_level = budget_map[budget]
        elif "入门" in budget or "100" in budget:
            budget_level = "入门级"
        elif "中端" in budget or "200" in budget:
            budget_level = "中端"
        elif "高端" in budget or "500" in budget:
            budget_level = "高端"
        elif "奢华" in budget or "1000" in budget:
            budget_level = "奢华"
        else:
            budget_level = "中端"

        products = self.PRODUCTS.get(category, {}).get(budget_level, [])

        if not products:
            return f"抱歉，暂未找到{category}的{budget_level}产品推荐~"

        # 构建回复
        content = f"给你推荐几款{category}{budget_level}价位的产品：\n\n"

        for i, p in enumerate(products, 1):
            content += f"🌟 {p['name']} ({p['price']})\n"
            content += f"   {p['highlights']}\n\n"

        content += "需要我帮你详细了解哪一款？或者有其他价位需求？"
        return content