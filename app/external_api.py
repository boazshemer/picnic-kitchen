"""
External API Client - תקשורת עם שרת חיצוני (גיא)
=================================================

הסבר למתחילים:
---------------
קובץ זה אחראי על שליחת הנתונים לשרת של גיא.
כשהשפית מזינה הזמנה, אנחנו:
1. שומרים אותה ב-Supabase שלנו
2. שולחים אותה גם לשרת של גיא (HTTP POST)
"""

import httpx
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.config import get_settings
from app.models import ExternalOrderPayload

logger = logging.getLogger(__name__)


class ExternalAPIClient:
    """
    לקוח לתקשורת עם API חיצוני
    
    הסבר:
    ------
    מחלקה זו יודעת איך לדבר עם השרת של גיא:
    - איפה הוא נמצא (URL)
    - איך לשלוח נתונים (POST request)
    - מה לעשות אם יש שגיאה
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.external_api_url
        self.api_key = self.settings.external_api_key
        
        # timeout = כמה זמן לחכות לתשובה (30 שניות)
        self.timeout = 30.0
    
    async def send_order(self, payload: ExternalOrderPayload) -> Dict[str, Any]:
        """
        שולח הזמנה לשרת החיצוני
        
        Args:
            payload: הנתונים לשליחה (Pydantic model)
        
        Returns:
            Dict עם התוצאה
        
        הסבר צעד-צעד:
        ----------------
        1. Pydantic ממיר את payload ל-JSON
        2. httpx שולח POST request לשרת של גיא
        3. מחכים לתשובה (עד 30 שניות)
        4. אם הצליח - מחזירים success
        5. אם נכשל - מחזירים error
        
        איך Pydantic מבטיח תקינות כאן:
        --------------------------------
        לפני שהבקשה יוצאת:
        ✅ payload.model_dump() בודק שכל השדות תקינים
        ✅ ממיר UUID ← string
        ✅ ממיר date ← string בפורמט נכון
        ✅ אם יש שגיאה - exception נזרק לפני השליחה!
        
        תוצאה: גיא תמיד יקבל JSON תקין ומובנה!
        """
        
        # בדיקה שיש URL מוגדר
        if not self.base_url:
            logger.warning("⚠️ לא הוגדר EXTERNAL_API_URL - דילוג על שליחה חיצונית")
            return {
                "success": False,
                "error": "EXTERNAL_API_URL לא הוגדר",
                "skipped": True
            }
        
        # הכנת הנתונים
        # payload.model_dump() ← ממיר את ה-Pydantic model ל-dict רגיל
        data = payload.model_dump()
        
        # הכנת headers (כותרות הבקשה)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # אם יש API Key - נוסיף אותו
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            logger.info(f"📤 שולח הזמנה לשרת חיצוני: {self.base_url}")
            logger.debug(f"נתונים: {data}")
            
            # שליחת הבקשה
            # httpx.AsyncClient = לקוח HTTP אסינכרוני
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url=self.base_url,
                    json=data,  # httpx ממיר אוטומטית ל-JSON
                    headers=headers
                )
                
                # בדיקת סטטוס
                # 200-299 = הצלחה
                # 400-499 = שגיאת לקוח (בעיה בנתונים שלנו)
                # 500-599 = שגיאת שרת (בעיה אצל גיא)
                response.raise_for_status()
                
                # הצלחה!
                logger.info(f"✅ שליחה לשרת חיצוני הצליחה: {response.status_code}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": response.json() if response.text else None,
                    "message": "ההזמנה נשלחה בהצלחה"
                }
        
        except httpx.TimeoutException:
            # חלף הזמן (30 שניות) והשרת לא ענה
            error_msg = "תם הזמן הקצוב לתשובה מהשרת החיצוני"
            logger.error(f"⏱️ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "timeout"
            }
        
        except httpx.HTTPStatusError as e:
            # השרת ענה אבל עם שגיאה (4xx, 5xx)
            error_msg = f"השרת החיצוני החזיר שגיאה: {e.response.status_code}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": e.response.status_code,
                "response": e.response.text,
                "error_type": "http_error"
            }
        
        except httpx.RequestError as e:
            # בעיה בחיבור (אין אינטרנט, השרת לא זמין וכו')
            error_msg = f"שגיאה בשליחה לשרת חיצוני: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "connection_error"
            }
        
        except Exception as e:
            # שגיאה לא צפויה
            error_msg = f"שגיאה בלתי צפויה: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unknown"
            }
    
    async def test_connection(self) -> bool:
        """
        בודק אם השרת החיצוני זמין
        
        שימוש:
        ------
        if await external_client.test_connection():
            print("השרת זמין!")
        """
        if not self.base_url:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # בדיקה פשוטה - האם השרת עונה?
                response = await client.get(self.base_url)
                return response.status_code < 500
        except Exception:
            return False


# ====================================
# פונקציה נוחה לשימוש
# ====================================

def get_external_api_client() -> ExternalAPIClient:
    """
    מחזיר instance של ExternalAPIClient
    
    שימוש:
    ------
    from app.external_api import get_external_api_client
    
    client = get_external_api_client()
    result = await client.send_order(payload)
    """
    return ExternalAPIClient()


# ====================================
# דוגמת שימוש:
# ====================================
# async def example():
#     client = get_external_api_client()
#     
#     payload = ExternalOrderPayload(
#         order_date="2025-12-23",
#         total_dishes=180,
#         items=[...],
#         timestamp=datetime.now().isoformat()
#     )
#     
#     result = await client.send_order(payload)
#     
#     if result["success"]:
#         print("✅ נשלח בהצלחה!")
#     else:
#         print(f"❌ שגיאה: {result['error']}")


