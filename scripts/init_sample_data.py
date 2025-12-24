"""
סקריפט להוספת דאטה לדוגמה
============================

יוצר:
- 5 טבחים
- 30 מנות ראשונות מהקובץ
- שיוך מנות לטבחים לפי קטגוריה
"""

import json
import sys
from pathlib import Path

# הוספת נתיב הפרויקט
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import get_supabase

print("=" * 60)
print("הוספת דאטה לדוגמה ל-Supabase")
print("=" * 60)
print()

# התחברות
print("[1/4] מתחבר ל-Supabase...")
try:
    supabase = get_supabase()
    print("✅ התחברות הצליחה")
except Exception as e:
    print(f"❌ שגיאה בהתחברות: {e}")
    print("\nוודא ש:")
    print("  1. יש קובץ .env")
    print("  2. SUPABASE_URL ו-SUPABASE_KEY מוגדרים")
    exit(1)

print()

# ====================================
# יצירת 5 טבחים
# ====================================

print("[2/4] יוצר 5 טבחים...")

cooks_data = [
    {
        "name": "משה כהן",
        "floor": 1,
        "email": "moshe@factory.com",
        "phone": "050-1234567",
        "specialty": "בשר",
        "is_active": True
    },
    {
        "name": "שרה לוי",
        "floor": 1,
        "email": "sarah@factory.com",
        "phone": "050-2345678",
        "specialty": "חלבי",
        "is_active": True
    },
    {
        "name": "דוד ישראלי",
        "floor": 2,
        "email": "david@factory.com",
        "phone": "050-3456789",
        "specialty": "פרווה",
        "is_active": True
    },
    {
        "name": "רחל אברהם",
        "floor": 2,
        "email": "rachel@factory.com",
        "phone": "050-4567890",
        "specialty": "קינוחים",
        "is_active": True
    },
    {
        "name": "יוסי מזרחי",
        "floor": 3,
        "email": "yossi@factory.com",
        "phone": "050-5678901",
        "specialty": "דגים",
        "is_active": True
    }
]

cook_ids = {}

for cook in cooks_data:
    try:
        response = supabase.table('cooks').insert(cook).execute()
        cook_id = response.data[0]['id']
        cook_ids[cook['specialty']] = cook_id
        print(f"  ✓ {cook['name']} ({cook['specialty']})")
    except Exception as e:
        print(f"  ✗ שגיאה ב-{cook['name']}: {e}")

print(f"✅ נוצרו {len(cook_ids)} טבחים")
print()

# ====================================
# טעינת מנות מהקובץ
# ====================================

print("[3/4] טוען מנות מהקובץ...")

dishes_file = r'c:\Users\97254\Downloads\dishes_clean.json'

try:
    with open(dishes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_dishes = data['dishes']
    # לוקחים רק 30 ראשונות
    sample_dishes = all_dishes[:30]
    
    print(f"✅ נטענו {len(sample_dishes)} מנות (מתוך {len(all_dishes)})")
except Exception as e:
    print(f"❌ שגיאה בטעינת קובץ: {e}")
    exit(1)

print()

# ====================================
# מיפוי קטגוריות לטבחים
# ====================================

# מיפוי לוגי של קטגוריות מנות לטבחים
category_to_specialty = {
    'בשר': 'בשר',
    'חלבי': 'חלבי',
    'פרווה': 'פרווה',
    'קינוחים': 'קינוחים',
    'דגים': 'דגים',
    # ברירת מחדל לקטגוריות אחרות
}

def get_cook_for_category(category):
    """מחזיר cook_id לפי קטגוריה"""
    specialty = category_to_specialty.get(category, 'פרווה')
    return cook_ids.get(specialty, list(cook_ids.values())[0])

# ====================================
# הוספת מנות
# ====================================

print("[4/4] מוסיף מנות ל-Supabase...")

added = 0
for dish in sample_dishes:
    try:
        # קביעת טבח ברירת מחדל לפי קטגוריה
        default_cook_id = get_cook_for_category(dish['category'])
        
        dish_record = {
            'name': dish['name'],
            'description': None,
            'category': dish['category'],
            'default_cook_id': default_cook_id,
            'preparation_time': 30,  # ברירת מחדל
            'is_active': True
        }
        
        response = supabase.table('dishes').insert(dish_record).execute()
        added += 1
        
        if added <= 5:  # הצג 5 ראשונות
            print(f"  ✓ {dish['name'][:40]:40} | {dish['category']}")
    
    except Exception as e:
        print(f"  ✗ שגיאה ב-{dish['name']}: {e}")

if added > 5:
    print(f"  ... ועוד {added - 5} מנות")

print(f"✅ נוספו {added} מנות בהצלחה")
print()

# ====================================
# סיכום
# ====================================

print("=" * 60)
print("🎉 סיימנו בהצלחה!")
print("=" * 60)
print()
print(f"✅ {len(cook_ids)} טבחים")
print(f"✅ {added} מנות")
print()
print("הצעד הבא:")
print("  python main.py")
print()
print("ואז בדוק:")
print("  http://localhost:8000/dishes")
print()


