"""
Configuration - הגדרות האפליקציה
=================================

הסבר למתחילים:
---------------
קובץ זה מרכז את כל ההגדרות במקום אחד:
- כתובת Supabase
- מפתח API
- כתובת השרת של גיא
- וכו'

למה זה טוב?
1. ניהול קל - הכל במקום אחד
2. סביבות שונות - קל להחליף בין פיתוח לייצור
3. אבטחה - משתני הסביבה לא בקוד
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    הגדרות האפליקציה
    
    הסבר:
    ------
    כל הגדרה נקראת אוטומטית מקובץ .env או ממשתני סביבה
    
    לדוגמה:
    אם יש בקובץ .env:
        SUPABASE_URL=https://abc.supabase.co
    
    אז:
        settings.supabase_url → "https://abc.supabase.co"
    """
    
    # ====================================
    # Supabase Configuration
    # ====================================
    supabase_url: str = os.getenv('SUPABASE_URL', '')
    supabase_key: str = os.getenv('SUPABASE_KEY', '')
    
    # ====================================
    # External API (שרת של גיא)
    # ====================================
    external_api_url: str = os.getenv('EXTERNAL_API_URL', '')
    external_api_key: Optional[str] = os.getenv('EXTERNAL_API_KEY', None)
    
    # ====================================
    # Application Settings
    # ====================================
    app_name: str = "מערכת ניהול משימות מפעל מזון"
    app_version: str = "1.0.0"
    environment: str = os.getenv('ENVIRONMENT', 'development')
    
    # FastAPI Settings
    host: str = "0.0.0.0"
    port: int = int(os.getenv('PORT', '8000'))
    debug: bool = environment == 'development'
    
    # ====================================
    # CORS Settings
    # ====================================
    # CORS = Cross-Origin Resource Sharing
    # מאפשר ל-Frontend (דפדפן) לגשת ל-API שלנו
    cors_origins: list = [
        "http://localhost:3000",  # React/Next.js local
        "http://localhost:5173",  # Vite local
        "http://localhost:8080",  # Vue local
        "http://localhost:8001",  # שרת עצמו
        "null",                   # קבצים מקומיים (file://)
        "*",                      # כל מקור (לפיתוח בלבד!)
    ]
    
    # ====================================
    # Logging
    # ====================================
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    
    class Config:
        """קונפיגורציה של Pydantic Settings"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    מחזיר את ההגדרות (singleton pattern)
    
    הסבר:
    ------
    @lru_cache() אומר: "צור את ההגדרות פעם אחת בלבד"
    בפעם הראשונה - יוצר Settings חדש
    בפעמים הבאות - מחזיר את אותו Settings
    
    למה זה טוב?
    - ביצועים: לא קורא את .env כל פעם מחדש
    - עקביות: כולם משתמשים באותן הגדרות
    """
    return Settings()


# ====================================
# דוגמאות שימוש:
# ====================================
# from app.config import get_settings
# 
# settings = get_settings()
# print(settings.supabase_url)
# print(settings.external_api_url)

