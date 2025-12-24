"""
סקריפט לניתוח קובץ המנות
"""
import json
from collections import Counter

# קריאת הקובץ
file_path = r'c:\Users\97254\Downloads\גיליון מוצרים ל-AI ChatBot.json'

with open(file_path, encoding='utf-8') as f:
    data = json.load(f)

dishes = data['גיליון1']

print(f"📊 סטטיסטיקות קובץ המנות")
print("=" * 50)
print(f"סה\"כ מנות: {len(dishes)}")
print()

# ספירת קטגוריות
categories = Counter(dish['קטגוריה'] for dish in dishes)
print("📋 קטגוריות:")
for cat, count in categories.most_common():
    print(f"  - {cat}: {count} מנות")
print()

# דוגמת מנה
print("🍽️ דוגמה למנה:")
print(json.dumps(dishes[0], indent=2, ensure_ascii=False))
print()

# שדות בכל מנה
print("🔑 שדות בכל מנה:")
for key in dishes[0].keys():
    print(f"  - {key}")



