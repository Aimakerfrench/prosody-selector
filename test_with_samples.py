#!/usr/bin/env python3
"""
اختبار شامل للمختار العروضي باستخدام عينات حقيقية
"""

import sys
import time
from pathlib import Path
from data import load_replacements_from_db
from core import PoetryMatcher
from settings import REPLACEMENTS_DB, DB_PATH

def load_sample_poems(count=20):
    """تحميل عينة من الأبيات"""
    sample_file = Path(__file__).parent / "عينة كاملة.txt"
    
    if not sample_file.exists():
        print("❌ ملف العينة غير موجود")
        return []
    
    poems = []
    with open(sample_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= count:
                break
            line = line.strip()
            if line and '***' in line:
                poems.append(line)
    
    return poems

def test_with_samples():
    """اختبار شامل مع عينات"""
    print("=" * 80)
    print("المختار العروضي - اختبار شامل مع عينات حقيقية")
    print("=" * 80)
    print()
    
    # تحميل البيانات
    print("📚 تحميل قواعد البيانات...")
    try:
        reps = load_replacements_from_db(REPLACEMENTS_DB)
        matcher = PoetryMatcher(DB_PATH, reps)
        print(f"✅ تم التحميل بنجاح ({len(reps)} استبدال)\n")
    except Exception as e:
        print(f"❌ خطأ في التحميل: {str(e)}")
        return False
    
    # تحميل العينات
    print("📖 تحميل عينات الأبيات...")
    poems = load_sample_poems(20)
    
    if not poems:
        print("❌ لم يتم العثور على أبيات للاختبار")
        return False
    
    print(f"✅ تم تحميل {len(poems)} بيت\n")
    
    # الإحصائيات
    total = len(poems)
    success = 0
    failed = 0
    total_time = 0
    
    print("=" * 80)
    print("بدء التحليل...")
    print("=" * 80)
    print()
    
    for i, poem in enumerate(poems, 1):
        print(f"البيت {i}/{total}:")
        print(f"{'─' * 80}")
        
        # عرض البيت (أول 70 حرف)
        display_poem = poem if len(poem) <= 70 else poem[:70] + "..."
        print(f"📝 {display_poem}")
        
        # التحليل
        start_time = time.time()
        try:
            processed, full = matcher.process_poem(poem)
            elapsed = time.time() - start_time
            total_time += elapsed
            
            if full:
                success += 1
                print(f"✅ تم تحديد البحر ({elapsed:.3f}s)")
                for sea in full.keys():
                    print(f"   🎵 {sea}")
            else:
                failed += 1
                print(f"⚠️ لم يتم العثور على بحر ({elapsed:.3f}s)")
            
        except Exception as e:
            failed += 1
            print(f"❌ خطأ: {str(e)}")
        
        print()
    
    # النتائج النهائية
    print("=" * 80)
    print("النتائج النهائية")
    print("=" * 80)
    print()
    
    success_rate = (success / total * 100) if total > 0 else 0
    avg_time = (total_time / total) if total > 0 else 0
    
    print(f"📊 الإحصائيات:")
    print(f"   • إجمالي الأبيات: {total}")
    print(f"   • الناجحة: {success} ({success_rate:.1f}%)")
    print(f"   • الفاشلة: {failed}")
    print(f"   • الوقت الإجمالي: {total_time:.2f}s")
    print(f"   • متوسط الوقت: {avg_time:.3f}s/بيت")
    print()
    
    if success_rate >= 80:
        print("✅ الأداء ممتاز!")
    elif success_rate >= 60:
        print("✅ الأداء جيد")
    elif success_rate >= 40:
        print("⚠️ الأداء مقبول")
    else:
        print("❌ يحتاج إلى تحسين")
    
    print()
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_with_samples()
    sys.exit(0 if success else 1)

