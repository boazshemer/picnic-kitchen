-- ====================================
-- סקריפט יצירת טבלאות למערכת ניהול משימות
-- Database: Supabase (PostgreSQL)
-- ====================================

-- הפעלת הרחבת UUID (אם לא קיימת)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ====================================
-- 1. טבלת טבחים (Cooks)
-- ====================================
CREATE TABLE IF NOT EXISTS cooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    floor INTEGER,  -- קומה בה הטבח עובד
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    specialty VARCHAR(100),  -- התמחות (בשרי, חלבי, אפייה וכו')
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- תגובה על הטבלה
COMMENT ON TABLE cooks IS 'טבלת הטבחים במפעל - 16 טבחים';
COMMENT ON COLUMN cooks.floor IS 'מספר הקומה בה הטבח עובד';
COMMENT ON COLUMN cooks.specialty IS 'התמחות הטבח (בשרי, חלבי, אפייה, סלטים וכו׳)';

-- ====================================
-- 2. טבלת מנות (Dishes)
-- ====================================
CREATE TABLE IF NOT EXISTS dishes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),  -- סוג המנה (עיקרית, תוספת, קינוח וכו')
    default_cook_id UUID REFERENCES cooks(id) ON DELETE SET NULL,  -- טבח ברירת מחדל
    preparation_time INTEGER,  -- זמן הכנה בדקות
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- תגובה על הטבלה
COMMENT ON TABLE dishes IS 'טבלת המנות - כל מנה משויכת לטבח ברירת מחדל';
COMMENT ON COLUMN dishes.default_cook_id IS 'הטבח שאחראי על הכנת המנה כברירת מחדל';
COMMENT ON COLUMN dishes.preparation_time IS 'זמן הכנה משוער בדקות';

-- ====================================
-- 3. טבלת הזמנות יומיות (Daily Orders)
-- ====================================
CREATE TABLE IF NOT EXISTS daily_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_date DATE NOT NULL,
    dish_id UUID REFERENCES dishes(id) ON DELETE CASCADE,
    assigned_cook_id UUID REFERENCES cooks(id) ON DELETE SET NULL,  -- יכול להיות שונה מברירת המחדל
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    notes TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_dish_per_day UNIQUE(order_date, dish_id)  -- מנה אחת ביום
);

-- תגובה על הטבלה
COMMENT ON TABLE daily_orders IS 'הזמנות יומיות - כ-400 מנות ביום';
COMMENT ON COLUMN daily_orders.assigned_cook_id IS 'הטבח שמשויך להזמנה - יכול להיות שונה מברירת המחדל';
COMMENT ON COLUMN daily_orders.status IS 'סטטוס ההזמנה: pending, in_progress, completed, cancelled';

-- ====================================
-- 4. טבלת לוג סנכרון חיצוני (External Sync Log)
-- ====================================
CREATE TABLE IF NOT EXISTS external_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES daily_orders(id) ON DELETE CASCADE,
    sync_status VARCHAR(20) CHECK (sync_status IN ('success', 'failed', 'pending')),
    request_payload JSONB,
    response_payload JSONB,
    error_message TEXT,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- תגובה על הטבלה
COMMENT ON TABLE external_sync_log IS 'לוג סנכרון עם שרת חיצוני של גיא';

-- ====================================
-- אינדקסים לשיפור ביצועים
-- ====================================
CREATE INDEX IF NOT EXISTS idx_daily_orders_date ON daily_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_daily_orders_cook ON daily_orders(assigned_cook_id);
CREATE INDEX IF NOT EXISTS idx_daily_orders_status ON daily_orders(status);
CREATE INDEX IF NOT EXISTS idx_dishes_default_cook ON dishes(default_cook_id);
CREATE INDEX IF NOT EXISTS idx_cooks_floor ON cooks(floor);
CREATE INDEX IF NOT EXISTS idx_external_sync_order ON external_sync_log(order_id);

-- ====================================
-- פונקציה לעדכון אוטומטי של updated_at
-- ====================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- טריגרים לעדכון אוטומטי של updated_at
CREATE TRIGGER update_cooks_updated_at BEFORE UPDATE ON cooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dishes_updated_at BEFORE UPDATE ON dishes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_orders_updated_at BEFORE UPDATE ON daily_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ====================================
-- הצלחה!
-- ====================================
-- כל הטבלאות נוצרו בהצלחה
-- להפעלה ב-Supabase: העתק את הקוד למסך SQL Editor


