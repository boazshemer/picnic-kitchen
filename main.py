"""
Main FastAPI Application
=========================

זהו הקובץ הראשי של השרת!

מה קורה כאן:
1. יוצרים אפליקציית FastAPI
2. מגדירים endpoints (נתיבים)
3. מטפלים בבקשות מהלקוחות

הסבר למתחילים - מה זה API:
-----------------------------
API = ממשק תכנות (Application Programming Interface)

דמיון למסעדה:
- הלקוח (Frontend/דפדפן) = סועד
- המלצר (API/Endpoints) = מקבל הזמנות
- המטבח (Database) = מכין את האוכל

הלקוח אומר למלצר: "אני רוצה לראות תפריט"
המלצר הולך למטבח, מביא את התפריט, ומחזיר ללקוח

בקוד:
הלקוח שולח: GET /dishes
השרת מחזיר: רשימת כל המנות
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import List, Dict, Any
import logging
from pathlib import Path

# ייבוא המודלים שלנו
from app.models import (
    DishResponse,
    OrderCreate,
    OrderResponse,
    SuccessResponse,
    ErrorResponse,
    ExternalOrderPayload,
    ExternalOrderItem,
    AddToOrderRequest
)
from app.database import (
    get_all_dishes_with_cooks,
    get_dish_by_id,
    get_cook_by_id,
    create_daily_order,
    log_external_sync,
    get_today_orders,
    update_order_item,
    delete_order_item,
    upsert_daily_order
)
from app.external_api import get_external_api_client
from app.config import get_settings

# הגדרת logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# טעינת הגדרות
settings = get_settings()

# ====================================
# יצירת אפליקציית FastAPI
# ====================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## 🍽️ מערכת ניהול משימות למפעל מזון
    
    אפליקציה לניהול הזמנות יומיות:
    - שפית מזינה את רשימת המנות
    - כל מנה משויכת לטבח
    - סנכרון אוטומטי עם שרת חיצוני
    
    ### תכונות:
    - 📋 שליפת רשימת מנות
    - 📤 שליחת הזמנות יומיות
    - 👨‍🍳 שיוך אוטומטי של טבחים
    - 🔄 סנכרון עם שרת חיצוני
    """,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# ====================================
# CORS Middleware
# ====================================
# מאפשר לדפדפן (Frontend) לגשת ל-API שלנו

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # אילו אתרים רשאים לגשת
    allow_credentials=True,
    allow_methods=["*"],  # כל סוגי הבקשות (GET, POST, וכו')
    allow_headers=["*"],  # כל הכותרות
)

# ====================================
# Static Files - קבצי HTML/CSS/JS
# ====================================
# מאפשר לדפדפן לגשת לקבצי ה-frontend

frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


# ====================================
# Root Endpoint - מחזיר את ממשק המשתמש
# ====================================

@app.get("/", tags=["General"])
async def root():
    """
    מחזיר את ממשק המשתמש (Frontend)
    """
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return {
            "message": "🍽️ ברוך הבא למערכת ניהול משימות מפעל מזון",
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs"
        }


@app.get("/health", tags=["General"])
async def health_check():
    """
    בדיקת תקינות (Health Check)
    
    שימושי כדי לבדוק שהשרת והשירותים עובדים
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "supabase_configured": bool(settings.supabase_url and settings.supabase_key),
        "external_api_configured": bool(settings.external_api_url)
    }


# ====================================
# GET /dishes - שליפת כל המנות
# ====================================

@app.get(
    "/dishes",
    response_model=List[DishResponse],
    tags=["Dishes"],
    summary="שליפת כל המנות",
    description="""
    מחזיר רשימה של כל המנות הפעילות במערכת,
    כולל פרטי הטבח ברירת המחדל של כל מנה.
    
    **תהליך:**
    1. שואל את Supabase: "תן לי את כל המנות + הטבחים שלהן"
    2. Supabase עושה JOIN בין הטבלאות
    3. מחזיר JSON עם כל המידע
    
    **דוגמת תגובה:**
    ```json
    [
      {
        "id": "abc-123",
        "name": "שניצל",
        "category": "עיקרית",
        "preparation_time": 30,
        "default_cook": {
          "id": "xyz-789",
          "name": "משה כהן",
          "floor": 1,
          "specialty": "בשרי"
        }
      }
    ]
    ```
    """
)
async def get_dishes():
    """
    שליפת כל המנות עם פרטי טבח ברירת המחדל
    
    הסבר צעד-צעד:
    ----------------
    1. קוראים לפונקציה get_all_dishes_with_cooks()
    2. היא עושה שאילתה ל-Supabase
    3. מקבלים רשימה של מנות (list of dicts)
    4. FastAPI אוטומטית ממיר ל-JSON
    5. Pydantic בודק שהתגובה תואמת ל-DishResponse
    6. מחזירים ללקוח
    """
    try:
        logger.info("📋 מבקש רשימת מנות")
        
        # שליפת המנות מהדאטהבייס
        dishes = await get_all_dishes_with_cooks()
        
        logger.info(f"✅ נמצאו {len(dishes)} מנות")
        return dishes
    
    except Exception as e:
        logger.error(f"❌ שגיאה בשליפת מנות: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בשליפת מנות מהמערכת: {str(e)}"
        )


# ====================================
# GET /today-order - שליפת הזמנת היום
# ====================================

@app.get(
    "/today-order",
    tags=["Orders"],
    summary="שליפת הזמנת היום",
    description="""
    מחזיר את כל ההזמנות שנוצרו להיום.
    
    **שימוש:**
    השפית פותחת את המערכת - רואה את מה שכבר הוזמן היום
    יכולה לערוך, למחוק, או להוסיף עוד מנות
    """
)
async def get_today_order(date: str = None):
    """
    שליפת הזמנות היום (או תאריך ספציפי)
    
    Parameters:
    - date: תאריך בפורמט YYYY-MM-DD (אם לא מוזן - לוקח את היום)
    """
    try:
        from datetime import date as date_module
        
        # אם לא הועבר תאריך - קח את היום
        if not date:
            date = str(date_module.today())
        
        logger.info(f"📋 מבקש הזמנות ל-{date}")
        
        orders = await get_today_orders(date)
        
        logger.info(f"✅ נמצאו {len(orders)} פריטים בהזמנת היום")
        
        return {
            "success": True,
            "order_date": date,
            "items": orders,
            "total_items": len(orders)
        }
    
    except Exception as e:
        logger.error(f"❌ שגיאה בשליפת הזמנת היום: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בשליפת הזמנת היום: {str(e)}"
        )


# ====================================
# PUT /order-item/{id} - עדכון פריט
# ====================================

@app.put(
    "/order-item/{order_id}",
    tags=["Orders"],
    summary="עדכון פריט בהזמנה",
    description="""
    מאפשר לשנות כמות, הערות, או טבח משויך
    """
)
async def update_item(order_id: str, quantity: int = None, notes: str = None, assigned_cook_id: str = None):
    """
    עדכון פריט בהזמנה
    """
    try:
        logger.info(f"✏️ מעדכן פריט {order_id}")
        
        update_data = {}
        if quantity is not None:
            update_data['quantity'] = quantity
        if notes is not None:
            update_data['notes'] = notes
        if assigned_cook_id:
            update_data['assigned_cook_id'] = assigned_cook_id
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="לא סופק שום שדה לעדכון"
            )
        
        updated_item = await update_order_item(order_id, update_data)
        
        if not updated_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"פריט {order_id} לא נמצא"
            )
        
        logger.info(f"✅ פריט {order_id} עודכן בהצלחה")
        
        return {
            "success": True,
            "message": "הפריט עודכן בהצלחה",
            "data": updated_item
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ שגיאה בעדכון פריט: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בעדכון פריט: {str(e)}"
        )


# ====================================
# DELETE /order-item/{id} - מחיקת פריט
# ====================================

@app.delete(
    "/order-item/{order_id}",
    tags=["Orders"],
    summary="מחיקת פריט מההזמנה",
    description="""
    מוחק מנה מהזמנת היום
    """
)
async def delete_item(order_id: str):
    """
    מחיקת פריט מההזמנה
    """
    try:
        logger.info(f"🗑️ מוחק פריט {order_id}")
        
        await delete_order_item(order_id)
        
        logger.info(f"✅ פריט {order_id} נמחק בהצלחה")
        
        return {
            "success": True,
            "message": "הפריט נמחק בהצלחה"
        }
    
    except Exception as e:
        logger.error(f"❌ שגיאה במחיקת פריט: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה במחיקת פריט: {str(e)}"
        )


# ====================================
# POST /add-to-order - הוספת מנה להזמנת היום
# ====================================

@app.post(
    "/add-to-order",
    tags=["Orders"],
    summary="הוספת מנה להזמנת היום",
    description="""
    מוסיף מנה להזמנת היום (או מעדכן כמות אם כבר קיימת)
    """
)
async def add_to_order(request: AddToOrderRequest):
    """
    הוספת מנה להזמנת היום
    """
    try:
        logger.info(f"➕ מוסיף מנה {request.dish_id} להזמנת {request.order_date}")
        
        # שליפת פרטי המנה
        dish = await get_dish_by_id(request.dish_id)
        
        if not dish:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"מנה לא נמצאה: {request.dish_id}"
            )
        
        # קביעת טבח
        if request.assigned_cook_id:
            cook_id = request.assigned_cook_id
        elif dish.get('default_cook_id'):
            cook_id = dish['default_cook_id']
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"למנה '{dish['name']}' אין טבח ברירת מחדל"
            )
        
        # יצירת ההזמנה
        order_data = {
            'order_date': request.order_date,
            'dish_id': request.dish_id,
            'assigned_cook_id': cook_id,
            'quantity': request.quantity,
            'status': 'pending',  # סטטוס - ממתין
            'notes': f"{request.notes or ''}\nיחידה: {request.unit}".strip()
        }
        
        created_order = await upsert_daily_order(order_data)
        
        logger.info(f"✅ מנה נוספה להזמנת היום")
        
        return {
            "success": True,
            "message": "המנה נוספה בהצלחה",
            "data": created_order
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ שגיאה בהוספת מנה: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בהוספת מנה: {str(e)}"
        )


# ====================================
# POST /finalize-order - סגירה ושליחה לגיא
# ====================================

@app.post(
    "/finalize-order",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Orders"],
    summary="סגירת הזמנת היום ושליחה לגיא",
    description="""
    **זהו השלב הסופי!**
    
    לוקח את כל ההזמנות של היום (שסטטוס שלהן 'draft')
    ושולח אותן לשרת של גיא.
    
    **תהליך:**
    1. שולף את כל ההזמנות של היום
    2. משנה את הסטטוס ל-'pending'
    3. שולח לשרת של גיא
    4. מעדכן סטטוס ל-'completed' או 'failed'
    """
)
async def finalize_order(order_date: str):
    """
    סגירת הזמנת היום ושליחה לשרת של גיא
    """
    try:
        logger.info(f"🚀 מסיים הזמנה ל-{order_date}")
        
        # שליפת כל ההזמנות של היום
        orders = await get_today_orders(order_date)
        
        if not orders:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"לא נמצאו הזמנות ליום {order_date}"
            )
        
        logger.info(f"   נמצאו {len(orders)} פריטים")
        
        # הכנת הנתונים לשליחה לגיא
        external_items = []
        total_dishes = 0
        
        for order in orders:
            dish = order.get('dish', {})
            cook = order.get('assigned_cook', {})
            
            external_items.append(
                ExternalOrderItem(
                    dish_name=dish.get('name', 'לא ידוע'),
                    quantity=order['quantity'],
                    cook_name=cook.get('name', 'לא ידוע'),
                    preparation_time=dish.get('preparation_time'),
                    notes=order.get('notes')
                )
            )
            
            total_dishes += order['quantity']
        
        # בניית ה-payload
        external_payload = ExternalOrderPayload(
            order_date=order_date,
            total_dishes=total_dishes,
            items=external_items,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"📤 שולח ל שרת חיצוני: {total_dishes} מנות")
        
        # שליחה לשרת של גיא
        external_client = get_external_api_client()
        sync_result = await external_client.send_order(external_payload)
        
        # עדכון סטטוס ההזמנות
        new_status = 'completed' if sync_result.get('success') else 'cancelled'
        
        for order in orders:
            await update_order_item(order['id'], {'status': new_status})
            
            # תיעוד
            log_data = {
                'order_id': order['id'],
                'sync_status': 'success' if sync_result.get('success') else 'failed',
                'request_payload': external_payload.model_dump(),
                'response_payload': sync_result.get('response'),
                'error_message': sync_result.get('error')
            }
            await log_external_sync(log_data)
        
        # תגובה ללקוח
        if sync_result.get('success'):
            logger.info("🎉 ההזמנה נסגרה והועברה לשרת חיצוני בהצלחה")
            message = f"ההזמנה נסגרה בהצלחה! סה״כ {total_dishes} מנות נשלחו לשרת של גיא"
        else:
            logger.warning(f"⚠️ ההזמנה נסגרה אך לא נשלחה לשרת חיצוני: {sync_result.get('error')}")
            message = f"ההזמנה נסגרה ({total_dishes} מנות), אך נכשלה השליחה לשרת חיצוני"
        
        return SuccessResponse(
            success=True,
            message=message,
            data={
                "order_date": order_date,
                "total_dishes": total_dishes,
                "items_count": len(orders),
                "external_sync": sync_result.get('success', False),
                "external_error": sync_result.get('error') if not sync_result.get('success') else None
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ שגיאה בסגירת הזמנה: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בסגירת ההזמנה: {str(e)}"
        )


# ====================================
# POST /submit-order - שליחת הזמנה (DEPRECATED - להתאימות לאחור)
# ====================================

@app.post(
    "/submit-order",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Orders"],
    summary="שליחת הזמנה יומית",
    description="""
    מקבל רשימת מנות שהשפית בחרה להזמנה יומית.
    
    **תהליך:**
    1. מקבל את ההזמנה מהשפית
    2. לכל מנה - קובע מי הטבח (אוטומטי או ידני)
    3. שומר ב-Supabase
    4. שולח ל-API של גיא
    5. מתעד את הסנכרון
    
    **לוגיקת שיוך טבחים (חשוב!):**
    - אם השפית **לא** בחרה טבח → משתמש בטבח ברירת המחדל של המנה
    - אם השפית **כן** בחרה טבח → משתמש בטבח שהיא בחרה (דריסה ידנית)
    
    **דוגמה:**
    ```json
    {
      "order_date": "2025-12-23",
      "items": [
        {
          "dish_id": "abc-123",
          "quantity": 100
          // assigned_cook_id לא צוין → ישתמש בברירת מחדל
        },
        {
          "dish_id": "def-456",
          "quantity": 80,
          "assigned_cook_id": "xyz-999"
          // צוין טבח ספציפי → ידרוס את ברירת המחדל
        }
      ]
    }
    ```
    """
)
async def submit_order(order: OrderCreate):
    """
    מטפל בהזמנה יומית חדשה
    
    הסבר מפורט של הלוגיקה:
    ------------------------
    
    שלב 1: קבלת ההזמנה
    --------------------
    - FastAPI מקבל את ה-JSON מהלקוח
    - Pydantic בודק שהנתונים תקינים (OrderCreate model)
    - אם יש בעיה → מחזיר שגיאה 422 אוטומטית
    
    שלב 2: עיבוד כל מנה
    --------------------
    לכל מנה ברשימה:
    a. שולפים את פרטי המנה מהדאטהבייס
    b. בודקים: האם השפית בחרה טבח?
       - אם לא (assigned_cook_id = None) → לוקחים את default_cook_id
       - אם כן → משתמשים בטבח שהיא בחרה
    c. יוצרים רשומה בטבלת daily_orders
    
    שלב 3: שליחה לשרת של גיא
    ---------------------------
    a. בונים ExternalOrderPayload עם כל המידע
    b. Pydantic בודק שהנתונים תקינים (זה מבטיח שגיא יקבל נתונים תקינים!)
    c. שולחים POST request
    d. מתעדים את התוצאה בטבלת external_sync_log
    
    איך Pydantic מבטיח תקינות:
    ---------------------------
    1. **בכניסה**: OrderCreate בודק שכל הנתונים מהשפית תקינים
       - תאריך לא בעבר ✓
       - כמויות חיוביות ✓
       - יש לפחות מנה אחת ✓
    
    2. **בפנים**: ExternalOrderPayload בודק שהנתונים לגיא תקינים
       - כל השדות הנדרשים קיימים ✓
       - סוגי נתונים נכונים (int, string) ✓
       - פורמטים נכונים (תאריך, timestamp) ✓
    
    3. **אם יש שגיאה**: Pydantic זורק ValidationError לפני השליחה
       → גיא לעולם לא יקבל נתונים לא תקינים!
    """
    try:
        logger.info(f"📥 מקבל הזמנה חדשה לתאריך: {order.order_date}")
        logger.info(f"   מספר מנות: {len(order.items)}")
        
        # רשימה לשמירת ההזמנות שנוצרו
        created_orders = []
        
        # רשימה לשליחה לגיא
        external_items = []
        
        # ====================================
        # שלב 1: עיבוד כל מנה בהזמנה
        # ====================================
        
        for item in order.items:
            logger.info(f"   מעבד מנה: {item.dish_id}")
            
            # שליפת פרטי המנה (כולל הטבח ברירת המחדל)
            dish = await get_dish_by_id(str(item.dish_id))
            
            if not dish:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"מנה לא נמצאה: {item.dish_id}"
                )
            
            # ====================================
            # הלוגיקה המרכזית: בחירת טבח
            # ====================================
            
            # אם השפית בחרה טבח ספציפי
            if item.assigned_cook_id:
                assigned_cook_id = str(item.assigned_cook_id)
                logger.info(f"      ✏️ דריסה ידנית: טבח {assigned_cook_id}")
                
                # וידוא שהטבח קיים
                cook = await get_cook_by_id(assigned_cook_id)
                if not cook:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"טבח לא נמצא: {assigned_cook_id}"
                    )
                cook_name = cook['name']
            
            # אם השפית לא בחרה - משתמשים בברירת מחדל
            else:
                if not dish.get('default_cook_id'):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"למנה '{dish['name']}' אין טבח ברירת מחדל, יש לבחור טבח ידנית"
                    )
                
                assigned_cook_id = dish['default_cook_id']
                cook_name = dish.get('default_cook', {}).get('name', 'לא ידוע')
                logger.info(f"      🔄 שימוש בברירת מחדל: {cook_name}")
            
            # ====================================
            # יצירת רשומה ב-daily_orders
            # ====================================
            
            order_data = {
                'order_date': str(order.order_date),
                'dish_id': str(item.dish_id),
                'assigned_cook_id': assigned_cook_id,
                'quantity': item.quantity,
                'status': 'pending',
                'notes': item.notes
            }
            
            # שמירה בדאטהבייס
            created_order = await create_daily_order(order_data)
            created_orders.append(created_order)
            
            # הכנת הפריט לשליחה לגיא
            external_items.append(
                ExternalOrderItem(
                    dish_name=dish['name'],
                    quantity=item.quantity,
                    cook_name=cook_name,
                    preparation_time=dish.get('preparation_time'),
                    notes=item.notes
                )
            )
        
        logger.info(f"✅ נוצרו {len(created_orders)} הזמנות בהצלחה")
        
        # ====================================
        # שלב 2: שליחה לשרת החיצוני (גיא)
        # ====================================
        
        # חישוב סה"כ מנות
        total_dishes = sum(item.quantity for item in order.items)
        
        # בניית ה-payload
        external_payload = ExternalOrderPayload(
            order_date=str(order.order_date),
            total_dishes=total_dishes,
            items=external_items,
            timestamp=datetime.now().isoformat()
        )
        
        # כאן Pydantic מבטיח תקינות!
        # אם יש שגיאה בנתונים, זה ייכשל כאן ולא יישלח לגיא
        logger.info(f"📤 מכין שליחה לשרת חיצוני")
        
        # שליחה
        external_client = get_external_api_client()
        sync_result = await external_client.send_order(external_payload)
        
        # ====================================
        # שלב 3: תיעוד הסנכרון
        # ====================================
        
        # שמירת לוג לכל הזמנה
        for created_order in created_orders:
            log_data = {
                'order_id': created_order['id'],
                'sync_status': 'success' if sync_result.get('success') else 'failed',
                'request_payload': external_payload.model_dump(),
                'response_payload': sync_result.get('response'),
                'error_message': sync_result.get('error')
            }
            await log_external_sync(log_data)
        
        # ====================================
        # שלב 4: החזרת תגובה ללקוח
        # ====================================
        
        if sync_result.get('success'):
            logger.info("🎉 הזמנה הושלמה והועברה לשרת חיצוני בהצלחה")
            message = f"ההזמנה נוצרה בהצלחה! סה״כ {total_dishes} מנות נשלחו לשרת החיצוני"
        else:
            logger.warning(f"⚠️ הזמנה נוצרה אך לא נשלחה לשרת חיצוני: {sync_result.get('error')}")
            message = f"ההזמנה נוצרה ({total_dishes} מנות), אך נכשלה השליחה לשרת חיצוני"
        
        return SuccessResponse(
            success=True,
            message=message,
            data={
                "order_date": str(order.order_date),
                "total_dishes": total_dishes,
                "items_count": len(created_orders),
                "external_sync": sync_result.get('success', False),
                "external_error": sync_result.get('error') if not sync_result.get('success') else None
            }
        )
    
    except HTTPException:
        # מעביר את ה-HTTPException הלאה
        raise
    
    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד הזמנה: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בעיבוד ההזמנה: {str(e)}"
        )


# ====================================
# Error Handlers - טיפול בשגיאות גלובלי
# ====================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    טיפול בשגיאות לא צפויות
    
    הסבר:
    ------
    אם קורית שגיאה שלא תפסנו, זה יתפוס אותה
    וייתן תגובה מסודרת במקום crash
    """
    logger.error(f"שגיאה לא צפויה: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "שגיאה פנימית בשרת",
            "details": str(exc) if settings.debug else "אנא פנה למנהל המערכת"
        }
    )


# ====================================
# הרצת השרת
# ====================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 מפעיל את השרת...")
    logger.info(f"📍 כתובת: http://{settings.host}:{settings.port}")
    logger.info(f"📚 תיעוד: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,  # reload אוטומטי בפיתוח
        log_level=settings.log_level.lower()