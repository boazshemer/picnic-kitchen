"""
Database Connection - חיבור למסד הנתונים
==========================================

הסבר למתחילים:
---------------
קובץ זה אחראי על החיבור ל-Supabase.
כל פעם שנרצה לדבר עם מסד הנתונים, נשתמש בפונקציות פה.
"""

from supabase import create_client, Client
from app.config import get_settings
from typing import Optional
import logging

# הגדרת logger (מערכת לוגים)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    מחלקה לניהול החיבור ל-Supabase
    
    הסבר:
    ------
    במקום ליצור חיבור חדש כל פעם, נשתמש באובייקט אחד שנוכל לעשות איתו:
    - supabase.table('dishes').select('*')
    - supabase.table('cooks').insert({...})
    """
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """
        מחזיר את ה-client של Supabase (singleton)
        
        הסבר:
        ------
        אם זה הפעם הראשונה - יוצר חיבור חדש
        אם כבר יצרנו - מחזיר את החיבור הקיים
        
        למה? ביצועים! לא צריך להתחבר כל פעם מחדש.
        """
        if cls._instance is None:
            settings = get_settings()
            
            # בדיקה שיש לנו את הפרטים
            if not settings.supabase_url or not settings.supabase_key:
                logger.error("חסרים SUPABASE_URL או SUPABASE_KEY")
                raise ValueError("חובה להגדיר SUPABASE_URL ו-SUPABASE_KEY בקובץ .env")
            
            try:
                # יצירת החיבור
                cls._instance = create_client(
                    settings.supabase_url,
                    settings.supabase_key
                )
                logger.info("✅ התחברות ל-Supabase הצליחה")
            except Exception as e:
                logger.error(f"❌ שגיאה בהתחברות ל-Supabase: {e}")
                raise
        
        return cls._instance
    
    @classmethod
    def reset_connection(cls):
        """מאפס את החיבור (שימושי לבדיקות)"""
        cls._instance = None


# ====================================
# פונקציה נוחה לשימוש
# ====================================

def get_supabase() -> Client:
    """
    מחזיר את ה-Supabase client
    
    שימוש:
    ------
    from app.database import get_supabase
    
    supabase = get_supabase()
    dishes = supabase.table('dishes').select('*').execute()
    """
    return DatabaseConnection.get_client()


# ====================================
# פונקציות עזר לשאילתות נפוצות
# ====================================

async def get_all_dishes_with_cooks():
    """
    מחזיר את כל המנות עם פרטי הטבח ברירת המחדל
    
    הסבר SQL:
    ---------
    במקום לעשות 2 שאילתות (מנות + טבחים),
    Supabase מאפשר לנו לעשות JOIN אוטומטי!
    
    הפקודה:
    .select('*, default_cook:cooks(*)')
    
    משמעותה:
    - תן לי את כל שדות המנה (*)
    - גם תן לי את הטבח (default_cook)
    - מטבלת cooks
    - עם כל השדות שלו (*)
    """
    logger.info("📋 מבקש רשימת מנות מ-Supabase")
    supabase = get_supabase()
    
    try:
        response = supabase.table('dishes').select(
            '*, default_cook:cooks!dishes_default_cook_id_fkey(*)'
        ).eq('is_active', True).execute()
        
        logger.info(f"✅ נמצאו {len(response.data)} מנות פעילות")
        return response.data
    except Exception as e:
        logger.error(f"❌ שגיאה בשליפת מנות מ-Supabase: {e}", exc_info=True)
        raise


async def get_cook_by_id(cook_id: str):
    """מחזיר טבח לפי ID"""
    logger.debug(f"🔍 מחפש טבח: {cook_id}")
    supabase = get_supabase()
    
    try:
        response = supabase.table('cooks').select('*').eq('id', cook_id).single().execute()
        if response.data:
            logger.debug(f"✅ נמצא טבח: {response.data.get('name', 'לא ידוע')}")
        else:
            logger.warning(f"⚠️ טבח {cook_id} לא נמצא")
        return response.data
    except Exception as e:
        logger.error(f"❌ שגיאה בשליפת טבח {cook_id}: {e}", exc_info=True)
        return None


async def get_dish_by_id(dish_id: str):
    """מחזיר מנה לפי ID (עם פרטי הטבח)"""
    logger.debug(f"🔍 מחפש מנה: {dish_id}")
    supabase = get_supabase()
    
    try:
        response = supabase.table('dishes').select(
            '*, default_cook:cooks!dishes_default_cook_id_fkey(*)'
        ).eq('id', dish_id).single().execute()
        if response.data:
            logger.debug(f"✅ נמצאה מנה: {response.data.get('name', 'לא ידוע')}")
        else:
            logger.warning(f"⚠️ מנה {dish_id} לא נמצאה")
        return response.data
    except Exception as e:
        logger.error(f"❌ שגיאה בשליפת מנה {dish_id}: {e}", exc_info=True)
        return None


async def create_daily_order(order_data: dict):
    """
    יוצר הזמנה יומית
    
    הסבר:
    ------
    מקבל dict עם:
    - order_date
    - dish_id
    - assigned_cook_id
    - quantity
    - notes
    
    מחזיר את ההזמנה שנוצרה (כולל ID)
    """
    logger.info(f"➕ יוצר הזמנה יומית: מנה {order_data.get('dish_id')} × {order_data.get('quantity')}")
    supabase = get_supabase()
    
    try:
        response = supabase.table('daily_orders').insert(order_data).execute()
        created = response.data[0] if response.data else None
        if created:
            logger.info(f"✅ הזמנה נוצרה בהצלחה: ID {created.get('id')}")
        return created
    except Exception as e:
        logger.error(f"❌ שגיאה ביצירת הזמנה: {e}", exc_info=True)
        raise


async def log_external_sync(log_data: dict):
    """
    שומר לוג של סנכרון עם שרת חיצוני
    
    הסבר:
    ------
    כל פעם ששולחים נתונים לגיא, נתעד:
    - מה שלחנו
    - מה קיבלנו בחזרה
    - האם הצליח או נכשל
    """
    logger.debug(f"📝 שומר לוג סנכרון: {log_data.get('sync_status', 'unknown')}")
    supabase = get_supabase()
    
    try:
        response = supabase.table('external_sync_log').insert(log_data).execute()
        if response.data:
            logger.debug(f"✅ לוג סנכרון נשמר בהצלחה")
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"❌ שגיאה בשמירת לוג סנכרון: {e}", exc_info=True)
        # לא נזרוק exception - הלוג הוא משני, לא נרצה לעצור את התהליך
        return None


# ====================================
# פונקציות לניהול הזמנות יומיות
# ====================================

async def get_today_orders(order_date: str):
    """
    מחזיר את כל ההזמנות של תאריך מסוים
    
    הסבר:
    ------
    כולל את פרטי המנה והטבח המשויך
    """
    logger.info(f"📅 מבקש הזמנות ליום {order_date}")
    supabase = get_supabase()
    
    try:
        response = supabase.table('daily_orders').select(
            '*, dish:dishes(id, name, category), assigned_cook:cooks(id, name, floor)'
        ).eq('order_date', order_date).execute()
        
        logger.info(f"✅ נמצאו {len(response.data)} פריטים בהזמנת {order_date}")
        return response.data
    except Exception as e:
        logger.error(f"❌ שגיאה בשליפת הזמנות של {order_date}: {e}", exc_info=True)
        raise


async def update_order_item(order_id: str, update_data: dict):
    """
    מעדכן פריט בהזמנה
    
    הסבר:
    ------
    מאפשר לשנות כמות, הערות, וכו'
    """
    logger.info(f"✏️ מעדכן פריט {order_id}: {list(update_data.keys())}")
    supabase = get_supabase()
    
    try:
        response = supabase.table('daily_orders').update(
            update_data
        ).eq('id', order_id).execute()
        
        updated = response.data[0] if response.data else None
        if updated:
            logger.info(f"✅ פריט {order_id} עודכן בהצלחה")
        return updated
    except Exception as e:
        logger.error(f"❌ שגיאה בעדכון הזמנה {order_id}: {e}", exc_info=True)
        raise


async def delete_order_item(order_id: str):
    """
    מוחק פריט מההזמנה
    
    הסבר:
    ------
    למקרה שהשפית רוצה להסיר מנה
    """
    logger.info(f"🗑️ מוחק פריט {order_id}")
    supabase = get_supabase()
    
    try:
        response = supabase.table('daily_orders').delete().eq('id', order_id).execute()
        logger.info(f"✅ פריט {order_id} נמחק בהצלחה")
        return True
    except Exception as e:
        logger.error(f"❌ שגיאה במחיקת הזמנה {order_id}: {e}", exc_info=True)
        raise


async def upsert_daily_order(order_data: dict):
    """
    יוצר או מעדכן הזמנה (אם כבר קיימת לאותו תאריך+מנה)
    
    הסבר:
    ------
    אם יש כבר הזמנה לאותו תאריך ומנה - מעדכן את הכמות
    אם לא - יוצר חדש
    """
    logger.info(f"🔄 Upsert הזמנה: {order_data.get('dish_id')} ב-{order_data.get('order_date')}")
    supabase = get_supabase()
    
    try:
        # בדיקה אם קיים
        existing = supabase.table('daily_orders').select('id, quantity').eq(
            'order_date', order_data['order_date']
        ).eq('dish_id', order_data['dish_id']).execute()
        
        if existing.data:
            # עדכון הכמות (מוסיף לכמות הקיימת)
            order_id = existing.data[0]['id']
            old_quantity = existing.data[0]['quantity']
            new_quantity = old_quantity + order_data['quantity']
            logger.info(f"📝 מעדכן הזמנה קיימת: כמות {old_quantity} → {new_quantity}")
            
            response = supabase.table('daily_orders').update({
                'quantity': new_quantity,
                'notes': order_data.get('notes')
            }).eq('id', order_id).execute()
            
            logger.info(f"✅ הזמנה עודכנה בהצלחה")
            return response.data[0] if response.data else None
        else:
            # יצירה חדשה
            logger.info(f"➕ יוצר הזמנה חדשה")
            return await create_daily_order(order_data)
            
    except Exception as e:
        logger.error(f"שגיאה ב-upsert הזמנה: {e}")
        raise

