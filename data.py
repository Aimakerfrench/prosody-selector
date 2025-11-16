import os
import unicodedata
import sqlite3

class ReplacementLoader:
    def __init__(self, path):
        self.path = path
        self.replacements = {}

    def load(self):
        if not os.path.isfile(self.path):
            print(f"ملف الاستبدالات غير موجود: {self.path}")
            return {}
        with open(self.path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip().lstrip('\ufeff')
                if '=' not in line:
                    continue
                orig, repl = line.split('=', 1)
                orig = unicodedata.normalize('NFC', orig.strip())
                repl = unicodedata.normalize('NFC', repl.strip())
                self.replacements[orig] = repl
        return self.replacements

def load_replacements_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT orig, repl FROM replacements;")
    reps = {orig: repl for orig, repl in cursor.fetchall()}
    conn.close()
    return reps
