from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. The Connection String (The Map to the Database)
# Notice how this perfectly matches the docker-compose.yml file we wrote earlier!
DATABASE_URL = "postgresql+asyncpg://ticket_user:supersecretpassword@localhost:5432/ticket_db"

# 2. The Engine (The actual bridge between FastAPI and PostgreSQL)
# echo=True means it will print the raw SQL it generates into your terminal so you can learn from it.
engine = create_async_engine(DATABASE_URL, echo=True)

# 3. The Session Factory (The conversation starter)
# Every time a user clicks "Buy", we create a temporary "Session" to talk to the DB, then close it.
async_session = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 4. The Base Model
# This is the master blueprint. All our future database tables will inherit from this.
Base = declarative_base()