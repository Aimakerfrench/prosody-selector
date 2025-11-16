import os
from pathlib import Path

# تحديد المسار الأساسي تلقائياً (مجلد البرنامج الحالي)
BASE_PATH = Path(__file__).parent.resolve()

# مسارات قواعد البيانات
REPLACEMENTS_DB = BASE_PATH / "استبدالات.db"
DB_PATH = BASE_PATH / "البحور.db"
WEIGHTS_DB = BASE_PATH / "أوزان البحور.db"
TAFEELAT_DB = BASE_PATH / "الزحافات والعلل.db"
OUTPUT_FILE = BASE_PATH / "وزن_البيت.html"

# تحويل إلى نصوص للتوافق مع الكود القديم
REPLACEMENTS_DB = str(REPLACEMENTS_DB)
DB_PATH = str(DB_PATH)
WEIGHTS_DB = str(WEIGHTS_DB)
TAFEELAT_DB = str(TAFEELAT_DB)
OUTPUT_FILE = str(OUTPUT_FILE)
