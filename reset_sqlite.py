import sqlite3
import random
from datetime import datetime
from pathlib import Path


# ===== 配置部分 =====
# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# SQLite 数据库路径（如有不同，请修改为你的实际路径/文件名）
DB_PATH = BASE_DIR / "db.sqlite3"

# 每个团的旅客/全陪问卷数量（可按需调整）
TRAVELERS_PER_GROUP = 5
FULL_ESCORTS_PER_GROUP = 2

# 要生成多少个团
GROUP_COUNT = 5
# ==================


def clear_all_tables(conn: sqlite3.Connection):
    """清空业务相关表数据（保留表结构）"""
    cur = conn.cursor()

    # 关闭外键约束，避免删除顺序受限
    cur.execute("PRAGMA foreign_keys = OFF;")

    tables = [
        "questionnaire_traveler",
        "questionnaire_full_escort",
        "questionnaire_group",
        "supplier_guide",
        "supplier_agency",
    ]

    for t in tables:
        print(f"清空表: {t}")
        cur.execute(f"DELETE FROM {t};")

    conn.commit()


def create_supplier_agency_data(conn: sqlite3.Connection):
    """插入地接社供应商纯文本数据"""
    cur = conn.cursor()
    sample = [
        ("阳光国际旅行社", "华东", "yggjlxs"),
        ("丝路之旅地接社", "西北", "slzldjs"),
        ("山海假期地接社", "华南", "shjq"),
        ("云上之旅地接社", "西南", "yszl"),
        ("锦绣中华地接社", "华北", "jxzh"),
    ]
    print("向表 supplier_agency 插入供应商数据")
    cur.executemany(
        "INSERT INTO supplier_agency (name, region, name_initials) VALUES (?, ?, ?)",
        sample,
    )
    conn.commit()


def create_supplier_guide_data(conn: sqlite3.Connection):
    """插入导游供应商纯文本数据"""
    cur = conn.cursor()
    sample = [
        ("local", "张伟", "Zhang Wei", "中文", "华东", "zw"),
        ("local", "李娜", "Li Na", "中文", "华南", "ln"),
        ("full", "王凯", "Wang Kai", "中文/English", "全国", "wk"),
        ("full", "陈晨", "Chen Chen", "中文/日本語", "华东", "cc"),
        ("local", "刘洋", "Liu Yang", "中文", "西北", "ly"),
    ]
    print("向表 supplier_guide 插入导游数据")
    cur.executemany(
        """
        INSERT INTO supplier_guide
        (guide_type, name_cn, name_en, language, region, name_initials)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        sample,
    )
    conn.commit()


def create_group_data(conn: sqlite3.Connection):
    """插入团数据，返回所有新建团的 id 列表"""
    cur = conn.cursor()
    now = datetime.now()
    ym = now.strftime("%Y-%m")

    group_ids = []
    print("向表 questionnaire_group 插入团数据")
    for i in range(1, GROUP_COUNT + 1):
        group_no = f"T{now.strftime('%Y%m')}-{i:03d}"
        people_count = random.randint(10, 40)
        feedback_count = random.randint(0, people_count)
        feedback_rate = f"{int(feedback_count / people_count * 100)}%"

        cur.execute(
            """
            INSERT INTO questionnaire_group
            (group_no, people_count, feedback_count, feedback_rate, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (group_no, people_count, feedback_count, feedback_rate, ym),
        )
        group_ids.append(cur.lastrowid)

    conn.commit()
    return group_ids


def random_score() -> float:
    """生成 4.0 - 5.0 之间的一位小数评分"""
    return round(random.uniform(4.0, 5.0), 1)


def create_traveler_data(conn: sqlite3.Connection, group_ids):
    """为每个团插入旅客问卷数据"""
    cur = conn.cursor()

    agencies = ["阳光国际旅行社", "丝路之旅地接社", "山海假期地接社"]
    guides = ["张伟", "李娜", "王凯", "陈晨"]
    hotels = ["天际大酒店", "星河湾酒店", "云海国际酒店"]
    regions = ["上海", "北京", "西安", "广州", "成都"]

    print("向表 questionnaire_traveler 插入旅客问卷数据")
    for gid in group_ids:
        for _ in range(TRAVELERS_PER_GROUP):
            cur.execute(
                """
                INSERT INTO questionnaire_traveler
                (group_id, agency, guide, hotel, region,
                 guide_language, guide_service,
                 vehicle_comfort, vehicle_clean, driver_service,
                 food_quality, restaurant_environment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    gid,
                    random.choice(agencies),
                    random.choice(guides),
                    random.choice(hotels),
                    random.choice(regions),
                    random_score(),
                    random_score(),
                    random_score(),
                    random_score(),
                    random_score(),
                    random_score(),
                    random_score(),
                ),
            )

    conn.commit()


def create_full_escort_data(conn: sqlite3.Connection, group_ids):
    """为每个团插入全陪问卷数据"""
    cur = conn.cursor()

    agencies = ["阳光国际旅行社", "丝路之旅地接社", "山海假期地接社"]
    guides = ["王凯", "陈晨", "刘洋"]
    hotels = ["天际大酒店", "星河湾酒店", "云海国际酒店"]
    regions = ["华东", "华南", "西北", "西南"]

    print("向表 questionnaire_full_escort 插入全陪问卷数据")
    for gid in group_ids:
        for _ in range(FULL_ESCORTS_PER_GROUP):
            pace = random_score()
            explanation = random_score()
            service = random_score()
            design = random_score()
            expectation = random_score()
            recommendation = random_score()
            overall = round(
                (pace + explanation + service + design + expectation + recommendation)
                / 6,
                1,
            )

            cur.execute(
                """
                INSERT INTO questionnaire_full_escort
                (group_id, agency, guide, hotel, region,
                 pace, explanation, service, design,
                 expectation, recommendation, overall)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    gid,
                    random.choice(agencies),
                    random.choice(guides),
                    random.choice(hotels),
                    random.choice(regions),
                    pace,
                    explanation,
                    service,
                    design,
                    expectation,
                    recommendation,
                    overall,
                ),
            )

    conn.commit()


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"数据库文件不存在: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    try:
        print("开始清空所有表数据...")
        clear_all_tables(conn)
        print("清空完成。")

        print("开始插入纯文本随机测试数据...")

        # 1. 供应商相关
        create_supplier_agency_data(conn)
        create_supplier_guide_data(conn)

        # 2. 团及其问卷
        group_ids = create_group_data(conn)
        create_traveler_data(conn, group_ids)
        create_full_escort_data(conn, group_ids)

        print("随机数据插入完成。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

