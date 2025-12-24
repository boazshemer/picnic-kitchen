# מדריך: Environment Variables (משתני סביבה)

## מה זה Environment Variables?

**Environment Variables** (משתני סביבה) הם הגדרות שמאוחסנות **מחוץ לקוד** שלך.

### למה זה נחוץ?

#### ❌ בעיה - קוד עם סיסמאות:
```python
# זה מסוכן! הסיסמה בקוד!
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

אם תעלה את זה ל-GitHub, כולם יראו את הסיסמה! 😱

#### ✅ פתרון - משתני סביבה:
```python
# זה בטוח! הסיסמה בקובץ נפרד
import os
supabase_key = os.getenv('SUPABASE_KEY')
```

## איך זה עובד?

### שלב 1: יצירת קובץ `.env`

צור קובץ בשם `.env` (עם נקודה בהתחלה!) בתיקיית הפרויקט:

```bash
SUPABASE_URL=https://abcdefgh.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### שלב 2: הוספה ל-`.gitignore`

כך הקובץ לא יעלה ל-Git:

```
# .gitignore
.env
```

### שלב 3: טעינה בקוד

```python
from dotenv import load_dotenv
import os

# טוען את קובץ .env
load_dotenv()

# קורא את הערכים
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print(f"URL: {url}")  # https://abcdefgh.supabase.co
```

## דוגמה מלאה: חיבור ל-Supabase

### קובץ `.env`:
```bash
SUPABASE_URL=https://xyzproject.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh5enByb2plY3QiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY0MjUwMDAwMCwiZXhwIjoxOTU4MDc2MDAwfQ.abcdef123456
```

### קובץ `connect.py`:
```python
import os
from dotenv import load_dotenv
from supabase import create_client

# 1. טוען את ההגדרות מ-.env
load_dotenv()

# 2. קורא את הערכים
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

# 3. בדיקה שהערכים קיימים
if not url or not key:
    print("❌ חסרים SUPABASE_URL או SUPABASE_KEY בקובץ .env")
    exit(1)

# 4. יצירת חיבור
supabase = create_client(url, key)

# 5. שימוש במסד הנתונים
result = supabase.table('cooks').select('*').execute()
print(result.data)
```

## איפה למצוא את הערכים ב-Supabase?

1. **היכנס ל-[Supabase.com](https://supabase.com)**
2. **בחר את הפרויקט שלך**
3. **Settings > API**
4. **העתק:**
   - **Project URL** → `SUPABASE_URL`
   - **anon/public key** → `SUPABASE_KEY` (לפיתוח)
   - **service_role key** → `SUPABASE_KEY` (לייצור - זהירות!)

## יתרונות

✅ **אבטחה**: סיסמאות לא בקוד  
✅ **גמישות**: החלפת הגדרות בקלות  
✅ **סביבות שונות**: הגדרות שונות לפיתוח/ייצור  
✅ **עבודת צוות**: כל מפתח עם הגדרות משלו  

## טיפים

### 💡 טיפ 1: קובץ דוגמה
צור `env.example` עם ערכים מזויפים:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key-here
```

### 💡 טיפ 2: בדיקת תקינות
תמיד בדוק שהערכים קיימים:
```python
if not os.getenv('SUPABASE_KEY'):
    raise ValueError("חסר SUPABASE_KEY בקובץ .env")
```

### 💡 טיפ 3: ערכי ברירת מחדל
```python
port = os.getenv('PORT', '8000')  # 8000 אם לא מוגדר
```

## שגיאות נפוצות

### ❌ "None" במקום הערך
**בעיה:** `os.getenv('SUPABASE_URL')` מחזיר `None`

**פתרון:**
1. וודא שקראת ל-`load_dotenv()` **לפני** `os.getenv()`
2. בדוק שהקובץ נקרא `.env` (עם נקודה!)
3. בדוק שהמשתנה נכתב נכון (case-sensitive!)

### ❌ הקובץ עלה ל-Git בטעות
**פתרון:**
```bash
# הסר מ-Git (אבל לא מהדיסק)
git rm --cached .env

# וודא ש-.gitignore מעודכן
echo ".env" >> .gitignore

# commit
git add .gitignore
git commit -m "הסרת .env מ-Git"
```

## סיכום

```
📁 הפרויקט שלך
├── .env                  ← הגדרות אמיתיות (לא ב-Git!)
├── env.example           ← דוגמה (כן ב-Git)
├── .gitignore            ← חוסם את .env
└── connect.py            ← הקוד שלך
```

זה הכל! עכשיו אתה יודע איך להשתמש ב-Environment Variables בצורה בטוחה 🔒


