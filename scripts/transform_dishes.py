"""
סקריפט המרה - מוציא רק שם מנה וקטגוריה
===============================================

קורא את הקובץ המקורי ומוציא JSON נקי עם:
- שם מנה
- קטגוריה

שימוש:
------
python scripts/transform_dishes.py
"""

import json
from pathlib import Path
from collections import Counter

# ====================================
# הגדרות
# ====================================

# קובץ המקור (הקובץ שלך)
INPUT_FILE = r'c:\Users\97254\Downloads\גיליון מוצרים ל-AI ChatBot.json'

# קובץ הפלט (הקובץ החדש והנקי)
OUTPUT_FILE = 'data/dishes_clean.json'

print("=" * 60)
print("🔄 המרת קובץ מנות")
print("=" * 60)
print()

# ====================================
# שלב 1: קריאת הקובץ המקורי
# ====================================

print("📂 קורא קובץ מקור...")
try:
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    original_dishes = original_data['גיליון1']
    print(f"✅ נמצאו {len(original_dishes)} מנות בקובץ המקור")
except Exception as e:
    print(f"❌ שגיאה בקריאת קובץ: {e}")
    exit(1)

print()

# ====================================
# שלב 2: המרה - מוציאים רק מה שצריך
# ====================================

print("🔄 ממיר נתונים...")
print("   מוציא: שם מנה + קטגוריה")
print()

clean_dishes = []

for dish in original_dishes:
    # מוציאים רק את מה שצריך!
    clean_dish = {
        'name': dish['שם מוצר'],          # שם המנה
        'category': dish['קטגוריה']        # קטגוריה
    }
    clean_dishes.append(clean_dish)

print(f"✅ הומרו {len(clean_dishes)} מנות בהצלחה")
print()

# ====================================
# שלב 3: סטטיסטיקות
# ====================================

print("📊 סטטיסטיקות:")
print("-" * 60)

# ספירת קטגוריות
categories = Counter(dish['category'] for dish in clean_dishes)
print(f"מספר קטגוריות: {len(categories)}")
print()

print("פילוח לפי קטגוריה:")
for category, count in sorted(categories.items()):
    percentage = (count / len(clean_dishes)) * 100
    print(f"  📦 {category:20} : {count:3} מנות ({percentage:.1f}%)")

print()

# ====================================
# שלב 4: שמירת הקובץ החדש
# ====================================

print("💾 שומר קובץ חדש...")

# יצירת המבנה הסופי
output_data = {
    'dishes': clean_dishes
}

# שמירה
try:
    # וידוא שהתיקייה קיימת
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ הקובץ נשמר בהצלחה: {OUTPUT_FILE}")
except Exception as e:
    print(f"❌ שגיאה בשמירת קובץ: {e}")
    exit(1)

print()

# ====================================
# שלב 5: הצגת דוגמאות
# ====================================

print("🍽️  דוגמאות מהקובץ החדש:")
print("-" * 60)

# 5 מנות ראשונות
for i, dish in enumerate(clean_dishes[:5], 1):
    print(f"{i}. {dish['name']:<40} | {dish['category']}")

print("...")

# 5 מנות אחרונות
print()
for i, dish in enumerate(clean_dishes[-5:], len(clean_dishes)-4):
    print(f"{i}. {dish['name']:<40} | {dish['category']}")

print()
print("=" * 60)
print("🎉 סיימנו!")
print("=" * 60)
print()
print(f"📄 הקובץ החדש: {OUTPUT_FILE}")
print(f"📊 סה\"כ מנות: {len(clean_dishes)}")
print()
print("הצעד הבא:")
print("  python scripts/upload_data.py --file data/dishes_clean.json")
print()


