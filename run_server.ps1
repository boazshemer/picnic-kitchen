# הפעלת השרת FastAPI (PowerShell)
# שימוש: .\run_server.ps1

Write-Host "==========================================="
Write-Host "     מפעיל את שרת ניהול משימות מפעל מזון"
Write-Host "==========================================="
Write-Host ""

# הפעלת הסביבה הוירטואלית
& .\venv\Scripts\Activate.ps1

# בדיקה שהקובץ .env קיים
if (-not (Test-Path .env)) {
    Write-Host "⚠️  אזהרה: קובץ .env לא נמצא!" -ForegroundColor Yellow
    Write-Host "יש להעתיק את env.example ל-.env ולמלא את הפרטים"
    Write-Host ""
    Read-Host "לחץ Enter לסגירה"
    exit 1
}

Write-Host "✅ סביבה וירטואלית הופעלה" -ForegroundColor Green
Write-Host "🚀 מפעיל את השרת..." -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 כתובת: http://localhost:8000"
Write-Host "📚 תיעוד: http://localhost:8000/docs"
Write-Host ""
Write-Host "לעצירת השרת: לחץ Ctrl+C"
Write-Host "==========================================="
Write-Host ""

# הרצת השרת
python main.py


