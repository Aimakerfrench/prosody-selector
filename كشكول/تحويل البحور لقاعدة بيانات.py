import os
import sqlite3

meters_dir = r"E:\03 - المختار العروضيّ\موقع المختار العروضي\البحور"
db_path = r"E:\03 - المختار العروضيّ\المختار.db"

# إنشاء الاتصال بقاعدة البيانات
conn = sqlite3.connect(db_path)
c = conn.cursor()

# إنشاء الجدول
c.execute('''
CREATE TABLE IF NOT EXISTS meters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bahr_name TEXT NOT NULL,
    line_text TEXT NOT NULL
)
''')

# قراءة الملفات وإدخالها
for filename in os.listdir(meters_dir):
    if filename.endswith('.txt'):
        bahr_name = filename[:-4]  # إزالة الامتداد
        filepath = os.path.join(meters_dir, filename)
        with open(filepath, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # تجاهل السطور الفارغة
                    c.execute('INSERT INTO meters (bahr_name, line_text) VALUES (?, ?)', (bahr_name, line))

# حفظ وإغلاق
conn.commit()
conn.close()

print("تم جمع الملفات في قاعدة البيانات:", db_path)
