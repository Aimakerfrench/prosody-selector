# ملف: convert_tafeelat.py
import os
import sqlite3
import pandas as pd

# مسار ملف الإكسل
INPUT_FILE = r"E:\03 - المختار العروضيّ\0.3 المختار العروضيّ\الزحافات والعلل.xlsx"
# اسم قاعدة البيانات الناتجة
DB_FILE    = os.path.join(os.path.dirname(INPUT_FILE), "الزحافات_العلل.db")

def main():
    # إذا كانت قاعدة قديمة، احذفها
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    # افتح اتصال sqlite وأنشئ جدول tafeelat
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()
    cur.execute("""
    CREATE TABLE tafeelat (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        asal         TEXT NOT NULL,   -- أصل التفعيلة
        lamh_asl     TEXT NOT NULL,   -- لمح الأصل
        image        TEXT NOT NULL,   -- صورة محسنة
        type         TEXT NOT NULL,   -- النوع
        notes        TEXT            -- ملاحظات
    );
    """)

    # اقرأ ورقة الإكسل
    df = pd.read_excel(INPUT_FILE, engine="openpyxl")
    for _, row in df.iterrows():
        cur.execute(
            "INSERT INTO tafeelat (asal, lamh_asl, image, type, notes) VALUES (?, ?, ?, ?, ?);",
            (
                str(row["أصل التفعيلة"]).strip(),
                str(row["لمح الأصل"]).strip(),
                str(row["صورة محسنة"]).strip(),
                str(row["النوع"]).strip(),
                str(row.get("ملاحظات", "")).strip()
            )
        )

    conn.commit()
    conn.close()
    print(f"تم إنشاء قاعدة البيانات: {DB_FILE}")

if __name__ == "__main__":
    main()
