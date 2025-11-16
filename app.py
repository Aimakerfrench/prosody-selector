import os
import subprocess
import pandas as pd
from data import load_replacements_from_db
from core import PoetryMatcher
from settings import REPLACEMENTS_DB, DB_PATH, WEIGHTS_DB, TAFEELAT_DB, OUTPUT_FILE
from core import PoetryMatcher
from settings import REPLACEMENTS_DB, DB_PATH, WEIGHTS_DB, TAFEELAT_DB, OUTPUT_FILE
import sqlite3

class ResultProcessor:
    def __init__(self, weights_db, tafeelat_db, output_file):
        self.weights_db    = weights_db
        self.tafeelat_db   = tafeelat_db
        self.output_file   = output_file
        self.html = (
            "<html><head><meta charset='UTF-8'><title>نتائج وزن البيت</title>"
            "<style>"
            "@font-face {font-family:'Sakkal Majalla';src:local('Sakkal Majalla'),url('SakkalMajalla.ttf')format('truetype');}"
            "body{font-family:'Sakkal Majalla',Arial,sans-serif;direction:rtl;text-align:right;background:#f2f2f2;}"
            ".container{width:80%;margin:auto;background:#fff;padding:30px;box-shadow:0 0 10px rgba(0,0,0,0.1);}"
            "h2{color:#2c3e50;margin-bottom:20px;}h3{color:#8e44ad;margin-bottom:15px;}"
            ".meter{color:#c0392b;font-size:24px;}.original{color:#2980b9;font-size:22px;}"
            ".processed{color:#27ae60;font-size:20px;}.tafeelat{color:#d35400;font-size:18px;"
            "background:#fcf8e3;padding:10px;border-radius:5px;}.result{margin-bottom:40px;}"
            ".separator{border-bottom:2px solid #ecf0f1;margin:30px 0;}ul{list-style:none;padding:0;}"
            "li{background:#ecf0f1;margin:5px 0;padding:10px;border-radius:5px;}"
            "</style></head><body><div class='container'>"
        )

    def get_weights(self, sea):
        conn = sqlite3.connect(self.weights_db)
        cur  = conn.cursor()
        cur.execute(
            "SELECT pattern FROM weights WHERE bahr_name = ?;",
            (sea,)
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else ""

    def compare(self, sea, res):
        w = self.get_weights(sea)
        wl = w.split(" *** ")
        rl = res.split(" *** ")
        if len(wl) == 2 and len(rl) == 2:
            wp = wl[0].split() + wl[1].split()
            rp = rl[0].split() + rl[1].split()
        else:
            wp = wl[0].split(); rp = rl[0].split()
        comps = list(zip(wp, rp))
        fmt = (
            f"تفعيلة بحر [{sea}]:<br><strong>{w}</strong><br>"
            f"تفاعيل البحر:<br><strong>{res}</strong>"
        )
        return fmt, comps

    def process_comps(self, comps):
        conn = sqlite3.connect(self.tafeelat_db)
        cur  = conn.cursor()
        out  = []
        for wt, rt in comps:
            # حاول التطابق على lamh_asl
            cur.execute(
                "SELECT type FROM tafeelat WHERE asal = ? AND lamh_asl = ?;",
                (wt, rt)
            )
            row = cur.fetchone()
            if row:
                typ = row[0]
            else:
                # حاول التطابق على image
                cur.execute(
                    "SELECT type FROM tafeelat WHERE asal = ? AND image = ?;",
                    (wt, rt)
                )
                r2 = cur.fetchone()
                typ = r2[0] if r2 else f"{wt}\tبقيت على الأصل"
            out.append(f"{wt} = {rt} : {typ}")
        conn.close()
        return out

    def write(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(self.html + "</div></body></html>")
        try:
            os.startfile(self.output_file)
        except:
            subprocess.call(['open', self.output_file])
        print(f"تم حفظ النتائج في: {self.output_file}")

    def process(self, orig, proc, full):
        self.html += (
            f"<div class='result'>"
            f"<p class='original'><strong>البيت الأصلي:</strong> {orig}</p>"
            f"<p class='processed'><strong>البيت المعالج:</strong> {proc}</p>"
        )
        if full:
            self.html += "<h2>مطابقة تامة للشطرين:</h2>"
            for sea, line in full.items():
                fmt, comps = self.compare(sea, line)
                frs = self.process_comps(comps)
                self.html += f"<h3 class='meter'>بحر {sea}</h3><p class='tafeelat'>{fmt}</p><ul>"
                for r in frs:
                    self.html += f"<li>{r}</li>"
                self.html += "</ul>"
        else:
            self.html += "<p>لا توجد مطابقة تامة للشطرين.</p>"
        self.html += "<div class='separator'></div></div>"
        self.write()

def main():
    reps      = load_replacements_from_db(REPLACEMENTS_DB)
    matcher   = PoetryMatcher(DB_PATH, reps)
    processor = ResultProcessor(WEIGHTS_DB, TAFEELAT_DB, OUTPUT_FILE)

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    while True:
        poem = input("أدخل البيت الشعري (*** بين الشطرين) أو 'خروج':\n")
        if poem.strip().lower() == 'خروج':
            break
        processed, full = matcher.process_poem(poem.strip())
        processor.process(poem.strip(), processed, full)

    print("انتهت المعالجة.")

if __name__ == "__main__":
    main()
