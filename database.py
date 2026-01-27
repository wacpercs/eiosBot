"""
Модели базы данных для Telegram бота ЭИОС
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, 
    ForeignKey, Float, Text, BigInteger, Index
)
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


class User(Base):
    """Модель пользователя Telegram"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Связь с ЭИОС
    student_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    eios_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Настройки
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str] = mapped_column(String(10), default="ru")
    
    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    grades: Mapped[List["Grade"]] = relationship("Grade", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, student_id={self.student_id})>"


class Grade(Base):
    """Модель оценки"""
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Информация об оценке
    eios_grade_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, unique=True)
    subject: Mapped[str] = mapped_column(String(500))
    assignment: Mapped[str] = mapped_column(String(500))
    grade_value: Mapped[int] = mapped_column(Integer)
    max_grade: Mapped[int] = mapped_column(Integer, default=5)
    
    # Дополнительная информация
    teacher_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Даты
    grade_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Статус уведомления
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="grades")

    def __repr__(self):
        return f"<Grade(subject={self.subject}, grade={self.grade_value})>"

    __table_args__ = (
        Index('idx_user_grade_date', 'user_id', 'grade_date'),
    )


class Notification(Base):
    """Модель уведомления"""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Тип и содержание уведомления
    notification_type: Mapped[str] = mapped_column(String(50))  # new_grade, deadline, announcement
    title: Mapped[str] = mapped_column(String(500))
    message: Mapped[str] = mapped_column(Text)
    
    # Связанная оценка (если применимо)
    grade_id: Mapped[Optional[int]] = mapped_column(ForeignKey("grades.id"), nullable=True)
    
    # Статус
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(type={self.notification_type}, user_id={self.user_id})>"

    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_user_type', 'user_id', 'notification_type'),
    )


class Subject(Base):
    """Модель предмета"""
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500), unique=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    teacher_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Subject(name={self.name})>"


class Session(Base):
    """Модель сессии пользователя (для аутентификации)"""
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_token: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # IP и user agent для безопасности
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self):
        return f"<Session(user_id={self.user_id}, expires_at={self.expires_at})>"


# Функции для работы с БД
class Database:
    """Класс для управления подключением к БД"""
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Включить для отладки SQL запросов
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self.async_session = async_sessionmaker(
            self.engine,
            expire_on_commit=False
        )
    
    async def create_tables(self):
        """Создание всех таблиц"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        """Удаление всех таблиц (ОСТОРОЖНО!)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def get_session(self):
        """Получение сессии БД"""
        async with self.async_session() as session:
            yield session
    
    async def close(self):
        """Закрытие соединения"""
        await self.engine.dispose()


# Пример использования
async def example_usage():
    """Пример работы с базой данных"""
    from sqlalchemy import select
    
    # Инициализация БД
    db = Database("sqlite+aiosqlite:///./test.db")
    await db.create_tables()
    
    # Создание пользователя
    async with db.async_session() as session:
        user = User(
            telegram_id=123456789,
            username="student123",
            first_name="Иван",
            last_name="Иванов",
            student_id=12345
        )
        session.add(user)
        await session.commit()
        
        # Создание оценки
        grade = Grade(
            user_id=user.id,
            eios_grade_id=1001,
            subject="Высшая математика",
            assignment="Контрольная работа №1",
            grade_value=5,
            grade_date=datetime.now(),
            teacher_name="Петров П.П.",
            comment="Отличная работа!"
        )
        session.add(grade)
        await session.commit()
        
        # Запрос оценок пользователя
        result = await session.execute(
            select(Grade).where(Grade.user_id == user.id)
        )
        grades = result.scalars().all()
        
        for g in grades:
            print(f"{g.subject}: {g.grade_value}")
    
    await db.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
