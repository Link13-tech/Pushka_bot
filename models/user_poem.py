from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class UserPoem(Base):
    __tablename__ = 'user_poems'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    poem_id = Column(Integer, ForeignKey('poems.id'), primary_key=True)
    status = Column(String(50), default='in_progress')

    user = relationship("User")
    poem = relationship("Poem")
