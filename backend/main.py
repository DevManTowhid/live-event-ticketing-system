from fastapi import FastAPI

# 1. Initialize the FastAPI application
app = FastAPI(
    title="Fair-Queue Ticketing API",
    description="A high-concurrency backend to prevent race conditions."
)

# 2. Create your very first endpoint (the front door)
@app.get("/")
async def root():
    return {"message": "The Ticketing Engine is live and ready!"}