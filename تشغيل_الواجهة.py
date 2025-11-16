#!/usr/bin/env python3
"""
ملف تشغيل مبسط للمختار العروضي
يتحقق من المتطلبات ويشغل الواجهة
"""

import sys
import os

def check_requirements():
    """التحقق من المتطلبات"""
    errors = []
    
    # التحقق من PyQt6
    try:
        import PyQt6
        print("✅ PyQt6 متوفر")
    except ImportError:
        errors.append("PyQt6 غير مثبت. قم بتثبيته: pip install PyQt6")
    
    # التحقق من الملفات الأساسية
    required_files = [
        'core.py',
        'data.py',
        'settings.py',
        'app.py',
        'واجهة_عروضية.py',
        'البحور.db',
        'أوزان البحور.db',
        'الزحافات والعلل.db',
        'استبدالات.db'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            errors.append(f"❌ ملف مفقود: {file}")
    
    return errors

def main():
    """التشغيل الرئيسي"""
    print("=" * 60)
    print("المختار العروضي - نظام التحليل العروضي")
    print("=" * 60)
    print()
    
    # التحقق من المتطلبات
    print("جارٍ التحقق من المتطلبات...")
    errors = check_requirements()
    
    if errors:
        print("\n❌ توجد مشاكل:")
        for error in errors:
            print(f"  • {error}")
        print("\nيرجى حل المشاكل أولاً")
        sys.exit(1)
    
    print("\n✅ جميع المتطلبات متوفرة")
    print("جارٍ تشغيل الواجهة...\n")
    
    # تشغيل الواجهة
    try:
        from واجهة_عروضية import main as run_app
        run_app()
    except Exception as e:
        print(f"\n❌ خطأ في التشغيل: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

