from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base


# Определяем возможные роли
class UserRole(PyEnum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    current_poem_id = Column(Integer, ForeignKey('poems.id'), nullable=True)
    current_level = Column(Integer, default=0)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    current_poem = relationship("Poem")
