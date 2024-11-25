from sqlalchemy import Column, Integer, String, Text
from .base import Base


class Poem(Base):
    __tablename__ = 'poems'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(255), default='А.С. Пушкин')
