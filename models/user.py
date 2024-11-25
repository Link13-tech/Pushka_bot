from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    current_poem_id = Column(Integer, ForeignKey('poems.id'), nullable=True)
    current_level = Column(Integer, default=0)

    current_poem = relationship("Poem")
