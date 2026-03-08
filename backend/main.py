from fastapi import FastAPI
from database import engine, Base
from contextlib import asynccontextmanager

# 1. Initialize the FastAPI application
app = FastAPI(
    title="Fair-Queue Ticketing API",
    description="A high-concurrency backend to prevent race conditions."
)

# --- 1. THE LIFESPAN MANAGER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Everything BEFORE the 'yield' happens on STARTUP
    print("Starting up... building the database tables!")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield # This is where the FastAPI app actually runs and listens for users
    
    # Everything AFTER the 'yield' happens on SHUTDOWN
    print("Shutting down... cleaning up resources!")
    await engine.dispose() # Safely close the database connections

# 2. Create your very first endpoint (the front door)
@app.get("/")
async def root():
    return {"message": "The Ticketing Engine is live and ready!"}


# main.py
from fastapi import FastAPI

# 1. Import the specific extension cords from your folders
from api.post import router as post_router
from api.get import router as get_router
from api.put import router as put_router
from api.delete import router as delete_router

# 2. Plug the extension cords into the main Engine
app.include_router(post_router)
app.include_router(get_router)
app.include_router(put_router)
app.include_router(delete_router)

import models
