@echo off
REM ملف تشغيل المختار العروضي لـ Windows
chcp 65001 >nul

echo ======================================
echo المختار العروضي - نظام التحليل العروضي
echo ======================================
echo.

REM التحقق من Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python غير مثبت
    echo يرجى تثبيت Python 3.8 أو أحدث من python.org
    pause
    exit /b 1
)

echo ✅ Python متوفر

REM التحقق من PyQt6
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ PyQt6 غير مثبت
    echo جارٍ التثبيت...
    pip install PyQt6
    if errorlevel 1 (
        echo ❌ فشل تثبيت PyQt6
        pause
        exit /b 1
    )
)

echo ✅ PyQt6 متوفر
echo.
echo جارٍ تشغيل البرنامج...
echo.

REM تشغيل البرنامج
python واجهة_عروضية.py

echo.
echo تم إغلاق البرنامج
pause

