# 🍽️ אפליקציית ניהול משימות למפעל מזון

אפליקציית Web לניהול משימות יומיות במפעל מזון - 400 מנות, 16 טבחים, אינטגרציה עם שרת חיצוני.

## 📋 תיאור

מערכת לניהול הכנת מנות במפעל מזון:
- שפית ראשית מזינה את רשימת המנות היומית
- כל מנה משויכת אוטומטית לטבח ברירת מחדל
- טבחים יכולים לצפות במשימות ולעדכן סטטוס
- סנכרון אוטומטי עם שרת חיצוני

## 🛠️ טכנולוגיות

- **Backend**: Python + FastAPI
- **Database**: Supabase (PostgreSQL)
- **ORM/Client**: supabase-py
- **Environment**: python-dotenv

## 📁 מבנה הפרויקט

```
פרוייקט יהודה/
├── docs/                          # תיעוד
│   ├── prd.md                     # דרישות מוצר
│   ├── schema.md                  # תכנון מסד נתונים
│   ├── roadmap.md                 # מפת דרכים
│   └── environment_variables_guide.md  # מדריך משתני סביבה
├── database/                      # סקריפטים של מסד נתונים
│   └── create_tables.sql          # יצירת טבלאות
├── scripts/                       # סקריפטים חד-פעמיים
│   └── upload_data.py             # העלאת נתונים
├── data/                          # נתוני דוגמה
│   └── sample_data.json           # נתונים לדוגמה
├── venv/                          # סביבה וירטואלית (לא ב-Git)
├── .env                           # הגדרות סביבה (לא ב-Git!)
├── env.example                    # דוגמת הגדרות
├── .gitignore                     # קבצים להתעלמות
├── requirements.txt               # חבילות Python
└── README.md                      # הקובץ הזה
```

## 🚀 התקנה

### 1. שכפול הפרויקט
```bash
cd "פרוייקט יהודה"
```

### 2. יצירת סביבה וירטואלית
```bash
python -m venv venv
```

### 3. הפעלת הסביבה הוירטואלית

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 4. התקנת חבילות
```bash
pip install -r requirements.txt
```

### 5. הגדרת Environment Variables

העתק את `env.example` ל-`.env`:
```bash
# Windows
copy env.example .env

# Mac/Linux
cp env.example .env
```

ערוך את `.env` והזן את הערכים האמיתיים:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

📖 **למדריך מפורט**: ראה `docs/environment_variables_guide.md`

## 🗄️ הקמת מסד הנתונים

### 1. צור פרויקט Supabase
1. היכנס ל-[Supabase.com](https://supabase.com)
2. צור פרויקט חדש
3. העתק את ה-URL וה-Key

### 2. צור את הטבלאות
1. בממשק Supabase, לחץ על **SQL Editor**
2. העתק את התוכן מ-`database/create_tables.sql`
3. הדבק ולחץ **RUN**

### 3. העלה נתוני דוגמה (אופציונלי)
```bash
python scripts/upload_data.py --file data/sample_data.json
```

## 📊 מבנה מסד הנתונים

### טבלאות עיקריות:

- **cooks** (טבחים): שם, קומה, התמחות
- **dishes** (מנות): שם, טבח ברירת מחדל, זמן הכנה
- **daily_orders** (הזמנות יומיות): תאריך, מנה, טבח, סטטוס
- **external_sync_log** (לוג סנכרון): מעקב אחר שליחה לשרת חיצוני

📖 **תכנון מפורט**: ראה `docs/schema.md`

## 🔧 שימוש

### העלאת נתונים מקובץ JSON
```bash
python scripts/upload_data.py --file data/my_data.json
```

### העלאת נתונים מקובץ Excel
```bash
python scripts/upload_data.py --file data/my_data.xlsx
```

**פורמט קובץ JSON:**
```json
{
  "cooks": [
    {
      "name": "משה כהן",
      "floor": 1,
      "email": "moshe@factory.com",
      "specialty": "בשרי"
    }
  ],
  "dishes": [
    {
      "name": "שניצל",
      "category": "עיקרית",
      "default_cook_name": "משה כהן",
      "preparation_time": 30
    }
  ]
}
```

## 📚 למידה

### מושגים חשובים למתחילים:

- **Virtual Environment (venv)**: בידוד חבילות הפרויקט
- **Environment Variables**: שמירת הגדרות מחוץ לקוד
- **Supabase**: מסד נתונים בענן (PostgreSQL)
- **FastAPI**: framework לבניית API
- **ORM**: תקשורת עם מסד הנתונים

📖 **מדריך Environment Variables**: `docs/environment_variables_guide.md`

## 🗺️ תכנון פיתוח

ראה את מפת הדרכים המלאה ב-`docs/roadmap.md`

### שלבים עיקריים:
- [x] שלב 1: הקמת תשתית
- [ ] שלב 2: Backend API
- [ ] שלב 3: לוגיקה עסקית
- [ ] שלב 4: אינטגרציה חיצונית
- [ ] שלב 5: Frontend
- [ ] שלב 6: בדיקות
- [ ] שלב 7: Deploy

## 📝 תיעוד נוסף

- `docs/prd.md` - דרישות מוצר מפורטות
- `docs/schema.md` - תכנון מסד הנתונים
- `docs/roadmap.md` - מפת דרכים מפורטת
- `docs/environment_variables_guide.md` - מדריך משתני סביבה

## 🤝 תרומה

פרויקט זה מיועד למפעל מזון פנימי.
למידע נוסף, פנה למנהל הפרויקט.

## 📧 יצירת קשר

- **מפתח**: בועז
- **מטרה**: למידת Python ופיתוח אפליקציית Web

---

**הערה**: זכור תמיד לשמור את קובץ `.env` בסוד ולא להעלות אותו ל-Git! 🔒


