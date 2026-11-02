from sqlalchemy.ext.asyncio import async_sessionmaker,create_async_engine,AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

setting = get_settings()

engine = create_async_engine(url=setting.DATABASE_URL,echo=True)

AsuncLocalSession = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

class Base(AsyncAttrs,DeclarativeBase):
    pass


async def get_db():
    async with AsuncLocalSession() as Session:
        yield Session