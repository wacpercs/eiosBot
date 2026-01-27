"""
API интеграция с порталом ЭИОС для отправки уведомлений в Telegram
"""
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EIOSIntegration:
    """
    Класс для интеграции с API портала ЭИОС
    """
    
    def __init__(self, eios_api_url: str, bot_api_url: str):
        self.eios_api_url = eios_api_url
        self.bot_api_url = bot_api_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Аутентификация пользователя в ЭИОС
        
        Args:
            username: Логин пользователя
            password: Пароль пользователя
            
        Returns:
            Данные студента или None при ошибке
        """
        try:
            async with self.session.post(
                f"{self.eios_api_url}/auth",
                json={"username": username, "password": password}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"User {username} authenticated successfully")
                    return data
                else:
                    logger.error(f"Authentication failed for {username}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def link_telegram_account(self, student_id: int, telegram_id: int) -> bool:
        """
        Привязка Telegram аккаунта к профилю студента
        
        Args:
            student_id: ID студента в ЭИОС
            telegram_id: Telegram ID пользователя
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            async with self.session.post(
                f"{self.eios_api_url}/students/{student_id}/link_telegram",
                json={"telegram_id": telegram_id}
            ) as response:
                if response.status == 200:
                    logger.info(f"Telegram account {telegram_id} linked to student {student_id}")
                    return True
                else:
                    logger.error(f"Failed to link Telegram account: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error linking Telegram account: {e}")
            return False
    
    async def get_student_grades(self, student_id: int) -> List[Dict]:
        """
        Получение оценок студента
        
        Args:
            student_id: ID студента
            
        Returns:
            Список оценок
        """
        try:
            async with self.session.get(
                f"{self.eios_api_url}/students/{student_id}/grades"
            ) as response:
                if response.status == 200:
                    grades = await response.json()
                    return grades
                else:
                    logger.error(f"Failed to get grades: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting grades: {e}")
            return []
    
    async def get_new_grades_since(self, student_id: int, since_datetime: datetime) -> List[Dict]:
        """
        Получение новых оценок с определенной даты
        
        Args:
            student_id: ID студента
            since_datetime: Дата, начиная с которой искать оценки
            
        Returns:
            Список новых оценок
        """
        try:
            async with self.session.get(
                f"{self.eios_api_url}/students/{student_id}/grades",
                params={"since": since_datetime.isoformat()}
            ) as response:
                if response.status == 200:
                    grades = await response.json()
                    return grades
                else:
                    return []
        except Exception as e:
            logger.error(f"Error getting new grades: {e}")
            return []
    
    async def send_notification_to_bot(self, telegram_id: int, grade_data: Dict) -> bool:
        """
        Отправка уведомления в бот
        
        Args:
            telegram_id: Telegram ID пользователя
            grade_data: Данные об оценке
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            async with self.session.post(
                f"{self.bot_api_url}/send_notification",
                json={
                    "telegram_id": telegram_id,
                    "notification_type": "new_grade",
                    "data": grade_data
                }
            ) as response:
                if response.status == 200:
                    logger.info(f"Notification sent to {telegram_id}")
                    return True
                else:
                    logger.error(f"Failed to send notification: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False


class GradeMonitor:
    """
    Мониторинг новых оценок и отправка уведомлений
    """
    
    def __init__(self, eios_integration: EIOSIntegration):
        self.integration = eios_integration
        self.last_check = {}
    
    async def monitor_student_grades(self, student_id: int, telegram_id: int):
        """
        Мониторинг оценок конкретного студента
        
        Args:
            student_id: ID студента
            telegram_id: Telegram ID для отправки уведомлений
        """
        if student_id not in self.last_check:
            self.last_check[student_id] = datetime.now()
        
        while True:
            try:
                # Получаем новые оценки
                new_grades = await self.integration.get_new_grades_since(
                    student_id,
                    self.last_check[student_id]
                )
                
                # Отправляем уведомления
                for grade in new_grades:
                    await self.integration.send_notification_to_bot(
                        telegram_id,
                        grade
                    )
                
                # Обновляем время последней проверки
                if new_grades:
                    self.last_check[student_id] = datetime.now()
                
                # Ждем 5 минут до следующей проверки
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error monitoring student {student_id}: {e}")
                await asyncio.sleep(60)


# Пример webhook endpoint для портала ЭИОС
class WebhookHandler:
    """
    Обработчик webhook'ов от портала ЭИОС
    
    Этот класс можно использовать вместо постоянного polling'а
    Портал ЭИОС будет отправлять POST запросы при появлении новой оценки
    """
    
    def __init__(self, bot_api_url: str):
        self.bot_api_url = bot_api_url
    
    async def handle_new_grade_webhook(self, webhook_data: Dict):
        """
        Обработка webhook о новой оценке
        
        Пример webhook_data:
        {
            "student_id": 12345,
            "telegram_id": 987654321,
            "subject": "Математика",
            "assignment": "Контрольная работа",
            "grade": 5,
            "comment": "Отлично!",
            "date": "2026-01-25T10:30:00"
        }
        """
        try:
            telegram_id = webhook_data.get("telegram_id")
            
            if not telegram_id:
                # Если telegram_id нет, получаем его по student_id
                # Здесь должен быть запрос к БД
                logger.warning(f"No telegram_id for student {webhook_data.get('student_id')}")
                return
            
            grade_data = {
                "subject": webhook_data.get("subject"),
                "assignment": webhook_data.get("assignment"),
                "grade": webhook_data.get("grade"),
                "comment": webhook_data.get("comment"),
                "date": webhook_data.get("date")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.bot_api_url}/send_notification",
                    json={
                        "telegram_id": telegram_id,
                        "notification_type": "new_grade",
                        "data": grade_data
                    }
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent successfully")
                    else:
                        logger.error(f"Webhook notification failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")


# Пример использования
async def example_usage():
    """Пример использования интеграции"""
    
    async with EIOSIntegration(
        eios_api_url="https://eios.kemsu.ru/api",
        bot_api_url="http://localhost:8080/api"
    ) as integration:
        
        # 1. Авторизация студента
        student_data = await integration.authenticate("student123", "password")
        
        if student_data:
            student_id = student_data["id"]
            telegram_id = 123456789  # Получено от Telegram
            
            # 2. Привязка Telegram аккаунта
            await integration.link_telegram_account(student_id, telegram_id)
            
            # 3. Получение оценок
            grades = await integration.get_student_grades(student_id)
            print(f"Оценок получено: {len(grades)}")
            
            # 4. Запуск мониторинга новых оценок
            monitor = GradeMonitor(integration)
            await monitor.monitor_student_grades(student_id, telegram_id)


if __name__ == "__main__":
    asyncio.run(example_usage())
