from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.poem import Poem


async def get_original_text(session: AsyncSession, poem_id: int) -> str:
    result = await session.execute(select(Poem.content).filter(Poem.id == poem_id))
    return result.scalar()
