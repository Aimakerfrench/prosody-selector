#!/usr/bin/env python3
"""
اختبار المكونات الأساسية للمختار العروضي
"""

import sys
from data import load_replacements_from_db
from core import PoetryMatcher
from settings import REPLACEMENTS_DB, DB_PATH, WEIGHTS_DB, TAFEELAT_DB
from app import ResultProcessor

def test_basic_functionality():
    """اختبار الوظائف الأساسية"""
    print("=" * 70)
    print("اختبار المختار العروضي")
    print("=" * 70)
    print()
    
    # 1. تحميل البيانات
    print("1️⃣ تحميل قواعد البيانات...")
    try:
        reps = load_replacements_from_db(REPLACEMENTS_DB)
        print(f"   ✅ تم تحميل {len(reps)} استبدال")
    except Exception as e:
        print(f"   ❌ خطأ: {str(e)}")
        return False
    
    # 2. إنشاء المطابق
    print("\n2️⃣ إنشاء المطابق...")
    try:
        matcher = PoetryMatcher(DB_PATH, reps)
        print("   ✅ تم إنشاء المطابق بنجاح")
    except Exception as e:
        print(f"   ❌ خطأ: {str(e)}")
        return False
    
    # 3. إنشاء معالج النتائج
    print("\n3️⃣ إنشاء معالج النتائج...")
    try:
        processor = ResultProcessor(WEIGHTS_DB, TAFEELAT_DB, "test_output.html")
        print("   ✅ تم إنشاء معالج النتائج")
    except Exception as e:
        print(f"   ❌ خطأ: {str(e)}")
        return False
    
    # 4. اختبار أبيات
    print("\n4️⃣ اختبار تحليل الأبيات...")
    
    test_poems = [
        "قِفَا نَبْكِ مِنْ ذِكْرَى حَبِيبٍ وَمَنْزِلِ *** بِسِقْطِ اللِّوَى بَيْنَ الدَّخُولِ فَحَوْمَلِ",
        "أَرَاكَ عَصِيَّ الدَّمْعِ شِيمَتُكَ الصَّبْرُ *** أَمَا لِلْهَوَى نَهْيٌ عَلَيْكَ وَلَا أَمْرُ",
        "لِكُلِّ شَيْءٍ إِذَا مَا تَمَّ نُقْصَانُ *** فَلَا يُغَرُّ بِطِيبِ العَيْشِ إِنْسَانُ"
    ]
    
    for i, poem in enumerate(test_poems, 1):
        print(f"\n   البيت {i}:")
        print(f"   {poem[:60]}...")
        
        try:
            processed, full = matcher.process_poem(poem)
            
            print(f"   📝 البيت المعالج: {processed[:60]}...")
            
            if full:
                print(f"   ✅ تم العثور على {len(full)} بحر:")
                for sea in full.keys():
                    print(f"      • {sea}")
            else:
                print("   ⚠️ لم يتم العثور على بحر مطابق")
                
        except Exception as e:
            print(f"   ❌ خطأ في التحليل: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ اكتمل الاختبار بنجاح")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)

