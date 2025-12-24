@echo off
REM הפעלת השרת FastAPI
REM שימוש: לחץ פעמיים על הקובץ או הרץ מהטרמינל

echo ===========================================
echo      מפעיל את שרת ניהול משימות מפעל מזון
echo ===========================================
echo.

REM הפעלת הסביבה הוירטואלית
call venv\Scripts\activate.bat

REM בדיקה שהקובץ .env קיים
if not exist .env (
    echo ⚠️  אזהרה: קובץ .env לא נמצא!
    echo יש להעתיק את env.example ל-.env ולמלא את הפרטים
    echo.
    pause
    exit /b 1
)

echo ✅ סביבה וירטואלית הופעלה
echo 🚀 מפעיל את השרת...
echo.
echo 📍 כתובת: http://localhost:8000
echo 📚 תיעוד: http://localhost:8000/docs
echo.
echo לעצירת השרת: לחץ Ctrl+C
echo ===========================================
echo.

REM הרצת השרת
python main.py

pause


