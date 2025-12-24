"""
סקריפט חד-פעמי להעלאת נתונים ל-Supabase
===========================================

סקריפט זה קורא רשימת טבחים ומנות מקובץ JSON או Excel
ומעלה אותם למסד הנתונים ב-Supabase.

שימוש:
------
python scripts/upload_data.py --file data/dishes.json
python scripts/upload_data.py --file data/cooks.xlsx

דרישות:
--------
1. קובץ .env עם SUPABASE_URL ו-SUPABASE_KEY
2. קובץ נתונים (JSON או Excel)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

# ייבוא ספריות חיצוניות
try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
    import pandas as pd
except ImportError as e:
    print(f"❌ שגיאה בייבוא ספריות: {e}")
    print("הרץ: pip install supabase python-dotenv pandas openpyxl")
    sys.exit(1)


# ====================================
# הסבר למתחילים - Environment Variables
# ====================================
"""
מה זה Environment Variables (משתני סביבה)?
-------------------------------------------
אלו הגדרות שמאוחסנות מחוץ לקוד שלך, למשל:
- סיסמאות
- מפתחות API
- כתובות שרתים

למה זה חשוב?
1. אבטחה: לא שומרים סיסמאות בקוד
2. גמישות: אפשר להחליף הגדרות בלי לשנות קוד
3. סביבות שונות: הגדרות שונות לפיתוח ולייצור

איך זה עובד?
1. יוצרים קובץ .env (לא עולה ל-Git!)
2. כותבים בו: SUPABASE_URL=https://...
3. הקוד קורא את זה עם load_dotenv()
4. משתמשים בזה: os.getenv('SUPABASE_URL')
"""
# ====================================


def load_environment() -> Dict[str, str]:
    """
    טוען משתני סביבה מקובץ .env
    
    Returns:
        Dict עם ההגדרות הנדרשות
        
    הסבר למתחילים:
    ----------------
    פונקציה זו:
    1. טוענת את קובץ .env (בעזרת load_dotenv)
    2. קוראת את הערכים של SUPABASE_URL ו-SUPABASE_KEY
    3. בודקת שהם קיימים (אם לא - זורקת שגיאה)
    """
    # טוען את קובץ .env לזיכרון
    load_dotenv()
    
    # קורא את הערכים
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    # בדיקת תקינות
    if not supabase_url or not supabase_key:
        print("❌ שגיאה: לא נמצאו SUPABASE_URL או SUPABASE_KEY")
        print("יש ליצור קובץ .env על בסיס .env.example")
        sys.exit(1)
    
    return {
        'url': supabase_url,
        'key': supabase_key
    }


def create_supabase_client() -> Client:
    """
    יוצר חיבור ל-Supabase
    
    Returns:
        אובייקט Client מחובר
        
    הסבר למתחילים:
    ----------------
    פונקציה זו מתחברת ל-Supabase:
    1. קוראת את פרטי החיבור (URL + Key)
    2. יוצרת אובייקט Client
    3. מחזירה אותו כדי שנוכל לעבוד איתו
    """
    config = load_environment()
    
    try:
        # create_client() מתחבר ל-Supabase
        supabase: Client = create_client(config['url'], config['key'])
        print("✅ התחברות ל-Supabase הצליחה")
        return supabase
    except Exception as e:
        print(f"❌ שגיאה בהתחברות ל-Supabase: {e}")
        sys.exit(1)


def read_json_file(file_path: str) -> Dict[str, List[Dict]]:
    """קורא קובץ JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ קריאת קובץ JSON: {file_path}")
        return data
    except Exception as e:
        print(f"❌ שגיאה בקריאת JSON: {e}")
        sys.exit(1)


def read_excel_file(file_path: str) -> Dict[str, List[Dict]]:
    """
    קורא קובץ Excel
    
    מצפה לשני גיליונות (sheets):
    - 'cooks' עם עמודות: name, floor, email, phone, specialty
    - 'dishes' עם עמודות: name, description, category, default_cook_name, preparation_time
    """
    try:
        # קריאת כל הגיליונות
        excel_file = pd.ExcelFile(file_path)
        data = {}
        
        # עובר על כל גיליון
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            # ממיר ל-dict והופך NaN ל-None
            data[sheet_name] = df.where(pd.notnull(df), None).to_dict('records')
        
        print(f"✅ קריאת קובץ Excel: {file_path}")
        print(f"   גיליונות שנמצאו: {list(data.keys())}")
        return data
    except Exception as e:
        print(f"❌ שגיאה בקריאת Excel: {e}")
        sys.exit(1)


def upload_cooks(supabase: Client, cooks_data: List[Dict]) -> Dict[str, str]:
    """
    מעלה טבחים ל-Supabase
    
    Args:
        supabase: אובייקט החיבור
        cooks_data: רשימת טבחים
        
    Returns:
        Dict שממפה שם טבח ל-UUID שלו (לשימוש במנות)
        
    הסבר למתחילים:
    ----------------
    1. עובר על כל טבח ברשימה
    2. מעלה אותו לטבלה 'cooks' ב-Supabase
    3. שומר את ה-ID שחזר כדי לקשר אותו למנות
    """
    cook_id_map = {}  # מיפוי: שם -> UUID
    
    print(f"\n📤 מעלה {len(cooks_data)} טבחים...")
    
    for cook in cooks_data:
        try:
            # הכנת הנתונים
            cook_record = {
                'name': cook.get('name'),
                'floor': cook.get('floor'),
                'email': cook.get('email'),
                'phone': cook.get('phone'),
                'specialty': cook.get('specialty'),
                'is_active': cook.get('is_active', True)
            }
            
            # העלאה ל-Supabase
            # .insert() מוסיף רשומה חדשה
            # .execute() מבצע את הפעולה
            response = supabase.table('cooks').insert(cook_record).execute()
            
            # שמירת ה-ID שחזר
            if response.data:
                cook_id = response.data[0]['id']
                cook_id_map[cook['name']] = cook_id
                print(f"   ✓ {cook['name']} (ID: {cook_id})")
        
        except Exception as e:
            print(f"   ✗ שגיאה בהעלאת {cook.get('name')}: {e}")
    
    print(f"✅ הועלו {len(cook_id_map)} טבחים בהצלחה")
    return cook_id_map


def upload_dishes(supabase: Client, dishes_data: List[Dict], cook_id_map: Dict[str, str]):
    """
    מעלה מנות ל-Supabase
    
    Args:
        supabase: אובייקט החיבור
        dishes_data: רשימת מנות
        cook_id_map: מיפוי שם טבח ל-UUID (מהשלב הקודם)
        
    הסבר למתחילים:
    ----------------
    1. עובר על כל מנה
    2. מחפש את ה-ID של הטבח ברירת המחדל (לפי השם)
    3. מעלה את המנה עם ה-ID הנכון
    """
    print(f"\n📤 מעלה {len(dishes_data)} מנות...")
    
    for dish in dishes_data:
        try:
            # מציאת ID של הטבח ברירת המחדל
            default_cook_name = dish.get('default_cook_name')
            default_cook_id = cook_id_map.get(default_cook_name) if default_cook_name else None
            
            # הכנת הנתונים
            dish_record = {
                'name': dish.get('name'),
                'description': dish.get('description'),
                'category': dish.get('category'),
                'default_cook_id': default_cook_id,
                'preparation_time': dish.get('preparation_time'),
                'is_active': dish.get('is_active', True)
            }
            
            # העלאה ל-Supabase
            response = supabase.table('dishes').insert(dish_record).execute()
            
            if response.data:
                print(f"   ✓ {dish['name']} (טבח: {default_cook_name or 'לא מוגדר'})")
        
        except Exception as e:
            print(f"   ✗ שגיאה בהעלאת {dish.get('name')}: {e}")
    
    print(f"✅ הועלו המנות בהצלחה")


def main():
    """פונקציה ראשית"""
    # פרסור ארגומנטים מהטרמינל
    parser = argparse.ArgumentParser(description='העלאת נתונים ל-Supabase')
    parser.add_argument('--file', required=True, help='נתיב לקובץ נתונים (JSON או Excel)')
    args = parser.parse_args()
    
    # בדיקת קיום הקובץ
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ הקובץ לא נמצא: {file_path}")
        sys.exit(1)
    
    # קריאת הנתונים
    file_extension = file_path.suffix.lower()
    if file_extension == '.json':
        data = read_json_file(str(file_path))
    elif file_extension in ['.xlsx', '.xls']:
        data = read_excel_file(str(file_path))
    else:
        print(f"❌ פורמט קובץ לא נתמך: {file_extension}")
        print("נתמכים: .json, .xlsx, .xls")
        sys.exit(1)
    
    # חיבור ל-Supabase
    supabase = create_supabase_client()
    
    # העלאת טבחים (אם יש)
    cook_id_map = {}
    if 'cooks' in data:
        cook_id_map = upload_cooks(supabase, data['cooks'])
    
    # העלאת מנות (אם יש)
    if 'dishes' in data:
        upload_dishes(supabase, data['dishes'], cook_id_map)
    
    print("\n🎉 סיימנו! כל הנתונים הועלו בהצלחה")


if __name__ == '__main__':
    main()


