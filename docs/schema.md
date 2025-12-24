# Schema - מבנה מסד הנתונים
## תכנון טבלאות Supabase

### טבלה: cooks (טבחים)
```sql
CREATE TABLE cooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    specialty VARCHAR(100),  -- התמחות (בשרי, חלבי, אפייה וכו')
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### טבלה: dishes (מנות)
```sql
CREATE TABLE dishes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),  -- סוג המנה (עיקרית, תוספת, קינוח וכו')
    default_cook_id UUID REFERENCES cooks(id),  -- טבח ברירת מחדל
    preparation_time INTEGER,  -- זמן הכנה בדקות
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### טבלה: daily_orders (הזמנות יומיות)
```sql
CREATE TABLE daily_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_date DATE NOT NULL,
    dish_id UUID REFERENCES dishes(id),
    assigned_cook_id UUID REFERENCES cooks(id),  -- יכול להיות שונה מברירת המחדל
    quantity INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, cancelled
    notes TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(order_date, dish_id)  -- מנה אחת ביום
);
```

### טבלה: external_sync_log (לוג סנכרון חיצוני)
```sql
CREATE TABLE external_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES daily_orders(id),
    sync_status VARCHAR(20),  -- success, failed, pending
    request_payload JSONB,
    response_payload JSONB,
    error_message TEXT,
    synced_at TIMESTAMP DEFAULT NOW()
);
```

### אינדקסים
```sql
CREATE INDEX idx_daily_orders_date ON daily_orders(order_date);
CREATE INDEX idx_daily_orders_cook ON daily_orders(assigned_cook_id);
CREATE INDEX idx_daily_orders_status ON daily_orders(status);
CREATE INDEX idx_dishes_default_cook ON dishes(default_cook_id);
```

### Row Level Security (RLS)
יש להגדיר מדיניות אבטחה ב-Supabase:
- שפית: גישה מלאה לכל הטבלאות
- טבחים: קריאה למנות שלהם, עדכון סטטוס בלבד


