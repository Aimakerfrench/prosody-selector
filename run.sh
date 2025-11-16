#!/bin/bash
# ملف تشغيل المختار العروضي لـ macOS/Linux

echo "======================================"
echo "المختار العروضي - نظام التحليل العروضي"
echo "======================================"
echo ""

# التحقق من Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 غير مثبت"
    echo "يرجى تثبيت Python 3.8 أو أحدث"
    exit 1
fi

echo "✅ Python 3 متوفر"

# التحقق من PyQt6
python3 -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ PyQt6 غير مثبت"
    echo "جارٍ التثبيت..."
    pip3 install PyQt6
    if [ $? -ne 0 ]; then
        echo "❌ فشل تثبيت PyQt6"
        exit 1
    fi
fi

echo "✅ PyQt6 متوفر"
echo ""
echo "جارٍ تشغيل البرنامج..."
echo ""

# تشغيل البرنامج
python3 واجهة_عروضية.py

echo ""
echo "تم إغلاق البرنامج"

