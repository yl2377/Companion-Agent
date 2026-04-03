"""存储层 - SQLite数据库管理"""
import sqlite3
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import asdict


class Database:
    """SQLite数据库管理类"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "memory.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()

        # 对话历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                timestamp REAL NOT NULL
            )
        """)

        # 打卡记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkin_type TEXT NOT NULL,
                items TEXT NOT NULL,
                notes TEXT,
                timestamp REAL NOT NULL
            )
        """)

        # 皮肤日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                overall TEXT,
                oil_level INTEGER,
                moisture_level INTEGER,
                issues TEXT,
                notes TEXT,
                timestamp REAL NOT NULL
            )
        """)

        # 产品记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                brand TEXT,
                category TEXT,
                ingredients TEXT,
                skin_type TEXT,
                rating INTEGER,
                notes TEXT,
                created_at REAL NOT NULL
            )
        """)

        self.conn.commit()

    # ========== 对话历史 ==========

    def add_conversation(self, role: str, content: str, tool_calls: str = None):
        """添加对话记录"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (role, content, tool_calls, timestamp) VALUES (?, ?, ?, ?)",
            (role, content, tool_calls, time.time())
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_conversations(self, limit: int = 50) -> List[Dict]:
        """获取最近的对话历史"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_conversations_for_context(self, limit: int = 20) -> List[Dict[str, str]]:
        """获取用于上下文的对话历史（简化格式）"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT role, content FROM conversations ORDER BY timestamp ASC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]

    def clear_conversations(self):
        """清除对话历史"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM conversations")
        self.conn.commit()

    # ========== 打卡记录 ==========

    def add_checkin(self, checkin_type: str, items: List[str], notes: str = None):
        """添加打卡记录"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO checkins (checkin_type, items, notes, timestamp) VALUES (?, ?, ?, ?)",
            (checkin_type, json.dumps(items), notes, time.time())
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_checkins(self, limit: int = 30) -> List[Dict]:
        """获取打卡记录"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM checkins ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            r = dict(row)
            r["items"] = json.loads(row["items"])
            result.append(r)
        return result

    def get_checkin_stats(self) -> Dict:
        """获取打卡统计"""
        cursor = self.conn.cursor()

        # 总打卡次数
        cursor.execute("SELECT COUNT(*) as total FROM checkins")
        total = cursor.fetchone()["total"]

        # 晨间/晚间打卡次数
        cursor.execute("SELECT checkin_type, COUNT(*) as count FROM checkins GROUP BY checkin_type")
        type_counts = {row["checkin_type"]: row["count"] for row in cursor.fetchall()}

        # 连续打卡计算（简单实现）
        checkins = self.get_checkins(limit=100)
        streak = 0
        if checkins:
            last_date = None
            for c in checkins:
                import datetime
                dt = datetime.datetime.fromtimestamp(c["timestamp"])
                date_str = dt.strftime("%Y-%m-%d")
                if last_date is None or date_str != last_date:
                    streak += 1
                    last_date = date_str
                else:
                    break

        return {
            "total": total,
            "morning": type_counts.get("morning", 0),
            "evening": type_counts.get("evening", 0),
            "streak": streak,
        }

    # ========== 皮肤日志 ==========

    def add_skin_log(
        self,
        date: str,
        overall: str = None,
        oil_level: int = None,
        moisture_level: int = None,
        issues: List[str] = None,
        notes: str = None,
    ):
        """添加皮肤日志"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO skin_logs (date, overall, oil_level, moisture_level, issues, notes, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date, overall, oil_level, moisture_level, json.dumps(issues or []), notes, time.time())
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_skin_logs(self, limit: int = 30) -> List[Dict]:
        """获取皮肤日志"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM skin_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            r = dict(row)
            r["issues"] = json.loads(row["issues"]) if row["issues"] else []
            result.append(r)
        return result

    # ========== 产品记录 ==========

    def add_product(
        self,
        name: str,
        brand: str = None,
        category: str = None,
        ingredients: List[str] = None,
        skin_type: str = None,
        rating: int = None,
        notes: str = None,
    ):
        """添加产品记录"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, brand, category, ingredients, skin_type, rating, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, brand, category, json.dumps(ingredients or []), skin_type, rating, notes, time.time())
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_products(self, limit: int = 50) -> List[Dict]:
        """获取产品记录"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM products ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            r = dict(row)
            r["ingredients"] = json.loads(row["ingredients"]) if row["ingredients"] else []
            result.append(r)
        return result

    def close(self):
        """关闭数据库连接"""
        self.conn.close()


# 全局数据库实例
_db: Optional[Database] = None


def get_database() -> Database:
    """获取全局数据库实例"""
    global _db
    if _db is None:
        _db = Database()
    return _db