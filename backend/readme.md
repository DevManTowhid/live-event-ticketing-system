## What are we installing?

-- fastapi: The web framework itself.

-- uvicorn: The lightning-fast server that actually runs your FastAPI code.

-- sqlalchemy & asyncpg: The tools to talk to your PostgreSQL database asynchronously (so it doesn't block other users while waiting for the database).

-- redis & rq: rq (Redis Queue) is a super clean, simple Python library to handle our 5-minute delayed background jobs using Redis.