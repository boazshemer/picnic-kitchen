"""
Pydantic Models - מודלים לולידציה
===================================

מה זה Pydantic?
---------------
זו ספריה שבודקת שהנתונים תקינים לפני שאנחנו משתמשים בהם.

דמיון: זה כמו שומר בכניסה למועדון שבודק:
- יש לך תעודה מזהה? ✓
- אתה מעל גיל 18? ✓
- השם שלך בעברית? ✓

אם משהו לא בסדר - השומר לא מכניס אותך!

למה זה חשוב?
-------------
1. מונע שגיאות: אם מישהו שולח "מחיר: בננה" במקום מספר - נתפוס את זה!
2. תיעוד אוטומטי: FastAPI יודע איזה נתונים אנחנו מצפים לקבל
3. בטיחות: נתונים שנשלחים לגיא תמיד יהיו תקינים
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


# ====================================
# מודלים בסיסיים - Cook (טבח)
# ====================================

class CookBase(BaseModel):
    """
    מידע בסיסי על טבח
    
    הסבר למתחילים:
    ----------------
    BaseModel של Pydantic = תבנית שמגדירה איך הנתונים צריכים להיראות
    """
    name: str = Field(..., min_length=2, max_length=100, description="שם הטבח")
    floor: Optional[int] = Field(None, ge=1, le=10, description="מספר קומה (1-10)")
    specialty: Optional[str] = Field(None, max_length=100, description="התמחות הטבח")
    
    class Config:
        # מאפשר המרה מ-ORM objects (מסד נתונים) לנתונים רגילים
        from_attributes = True


class CookResponse(CookBase):
    """
    מידע מלא על טבח (כולל ID) - מוחזר מ-API
    
    הסבר:
    ------
    כשאנחנו מחזירים טבח מהשרת, נכלול גם את ה-ID שלו
    """
    id: UUID
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True


# ====================================
# מודלים בסיסיים - Dish (מנה)
# ====================================

class DishBase(BaseModel):
    """מידע בסיסי על מנה"""
    name: str = Field(..., min_length=2, max_length=200, description="שם המנה")
    description: Optional[str] = Field(None, description="תיאור המנה")
    category: Optional[str] = Field(None, max_length=50, description="קטגוריה (עיקרית, תוספת, קינוח)")
    preparation_time: Optional[int] = Field(None, ge=1, le=600, description="זמן הכנה בדקות")
    
    class Config:
        from_attributes = True


class DishResponse(DishBase):
    """
    מנה עם פרטי הטבח ברירת המחדל
    
    זה מה שנחזיר ב-GET /dishes
    """
    id: UUID
    default_cook_id: Optional[UUID] = None
    default_cook: Optional[CookResponse] = None  # פרטי הטבח המלאים!
    is_active: bool = True
    
    class Config:
        from_attributes = True


# ====================================
# מודלים להזמנה (Order)
# ====================================

class OrderItemCreate(BaseModel):
    """
    פריט בהזמנה - מה השפית בחרה
    
    הסבר למתחילים:
    ----------------
    השפית בוחרת מנה ואומרת "אני רוצה 50 מנות שניצל"
    
    הלוגיקה החשובה:
    - אם השפית לא בחרה טבח ספציפי (assigned_cook_id = None)
      → המערכת תשתמש בטבח ברירת המחדל של המנה
    - אם השפית בחרה טבח ספציפי (assigned_cook_id = UUID)
      → המערכת תשתמש בטבח הזה (דריסה ידנית!)
    """
    dish_id: UUID = Field(..., description="ID של המנה")
    quantity: int = Field(..., ge=1, le=500, description="כמות (1-500)")
    assigned_cook_id: Optional[UUID] = Field(
        None, 
        description="ID טבח ספציפי (אופציונלי - אם None, ישתמש בברירת מחדל)"
    )
    notes: Optional[str] = Field(None, max_length=500, description="הערות")
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        """
        ולידטור מותאם אישית
        
        הסבר:
        ------
        פונקציה זו רצה אוטומטית כשמישהו שולח quantity
        אם הערך לא בסדר - נזרוק שגיאה
        """
        if v <= 0:
            raise ValueError('כמות חייבת להיות חיובית')
        if v > 500:
            raise ValueError('כמות מקסימלית: 500 מנות')
        return v


class OrderCreate(BaseModel):
    """
    הזמנה שלמה - רשימת מנות שהשפית בחרה
    
    דוגמה:
    -------
    {
      "order_date": "2025-12-23",
      "items": [
        {"dish_id": "abc-123", "quantity": 100},
        {"dish_id": "def-456", "quantity": 80, "assigned_cook_id": "xyz-789"}
      ]
    }
    """
    order_date: date = Field(..., description="תאריך ההזמנה")
    items: List[OrderItemCreate] = Field(
        ..., 
        min_length=1,
        description="רשימת המנות שנבחרו (לפחות מנה אחת)"
    )
    
    @field_validator('order_date')
    @classmethod
    def validate_order_date(cls, v):
        """וודא שהתאריך לא בעבר"""
        if v < date.today():
            raise ValueError('לא ניתן ליצור הזמנה לתאריך שעבר')
        return v
    
    @field_validator('items')
    @classmethod
    def validate_items_not_empty(cls, v):
        """וודא שיש לפחות מנה אחת"""
        if not v:
            raise ValueError('חייבת להיות לפחות מנה אחת בהזמנה')
        return v


class OrderItemResponse(BaseModel):
    """פריט בהזמנה - תגובה מהשרת"""
    id: UUID
    dish_id: UUID
    dish: Optional[DishResponse] = None  # פרטי המנה
    assigned_cook_id: UUID
    assigned_cook: Optional[CookResponse] = None  # פרטי הטבח
    quantity: int
    status: str = "pending"
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """הזמנה שלמה - תגובה מהשרת"""
    id: UUID
    order_date: date
    items: List[OrderItemResponse]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ====================================
# מודל לשליחה לשרת חיצוני (גיא)
# ====================================

class ExternalOrderItem(BaseModel):
    """
    פריט בהזמנה - פורמט לשרת של גיא
    
    הסבר חשוב - למה Pydantic מבטיח תקינות:
    ------------------------------------------
    1. סוגי נתונים: dish_name חייב להיות string, quantity חייב int
    2. ולידציה: אם נשלח quantity = -5, זה ייכשל
    3. סריאליזציה: Pydantic ממיר אוטומטית ל-JSON תקין
    4. תיעוד: המודל הזה גם מתעד מה אנחנו שולחים
    
    אם יש שגיאה - נדע עליה לפני ששולחים לגיא!
    """
    dish_name: str = Field(..., description="שם המנה")
    quantity: int = Field(..., ge=1, description="כמות")
    cook_name: str = Field(..., description="שם הטבח")
    preparation_time: Optional[int] = Field(None, description="זמן הכנה בדקות")
    notes: Optional[str] = None


class ExternalOrderPayload(BaseModel):
    """
    המבנה המלא שנשלח לשרת של גיא
    
    איך Pydantic מבטיח תקינות:
    ----------------------------
    ✅ הכל מוקלד (typed): order_date תמיד יהיה תאריך
    ✅ ולידציה: אם items ריק, זה ייכשל
    ✅ המרה אוטומטית: תאריך ← string בפורמט נכון
    ✅ שגיאות ברורות: אם משהו לא תקין, נקבל הודעה מפורטת
    
    לפני שהבקשה יוצאת לגיא:
    1. Pydantic בודק שהכל תקין
    2. ממיר ל-JSON נקי
    3. אם יש בעיה - נזרוק exception לפני השליחה
    
    תוצאה: גיא תמיד יקבל נתונים תקינים! 🎯
    """
    order_date: str = Field(..., description="תאריך בפורמט YYYY-MM-DD")
    total_dishes: int = Field(..., ge=1, description="סה״כ מספר מנות")
    items: List[ExternalOrderItem] = Field(..., min_length=1, description="רשימת המנות")
    timestamp: str = Field(..., description="חותמת זמן")
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_date": "2025-12-23",
                "total_dishes": 180,
                "items": [
                    {
                        "dish_name": "שניצל",
                        "quantity": 100,
                        "cook_name": "משה כהן",
                        "preparation_time": 30,
                        "notes": ""
                    },
                    {
                        "dish_name": "פסטה",
                        "quantity": 80,
                        "cook_name": "שרה לוי",
                        "preparation_time": 25
                    }
                ],
                "timestamp": "2025-12-23T08:30:00"
            }
        }


# ====================================
# מודל לתיעוד סנכרון
# ====================================

class SyncLogCreate(BaseModel):
    """תיעוד ניסיון סנכרון עם שרת חיצוני"""
    order_id: UUID
    sync_status: str = Field(..., pattern="^(success|failed|pending)$")
    request_payload: dict
    response_payload: Optional[dict] = None
    error_message: Optional[str] = None


# ====================================
# תגובות כלליות
# ====================================

class SuccessResponse(BaseModel):
    """תגובת הצלחה כללית"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """תגובת שגיאה"""
    success: bool = False
    error: str
    details: Optional[dict] = None


# ====================================
# מודל להוספת מנה להזמנת היום
# ====================================

class AddToOrderRequest(BaseModel):
    """
    בקשה להוספת מנה להזמנת היום
    """
    order_date: str = Field(..., description="תאריך בפורמט YYYY-MM-DD")
    dish_id: str = Field(..., description="ID של המנה")
    quantity: int = Field(..., ge=1, le=500, description="כמות")
    unit: str = Field(default="יח׳", description="יחידת מידה")
    notes: Optional[str] = Field(None, max_length=500, description="הערות")
    assigned_cook_id: Optional[str] = Field(None, description="ID טבח ספציפי")

