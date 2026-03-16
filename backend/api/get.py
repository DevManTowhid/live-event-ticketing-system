from sqlite3 import Date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import models
from sqlalchemy import select
# 1. Create the router (the "extension cord")
router = APIRouter()


@router.get("/admin/view-event-requests")
async def view_event_requests(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time:Optional[str] = None,
    db: AsyncSession = Depends(get_db)): # This endpoint allows admins to view all pending event requests submitted by users
    query = select(models.RequestEvent)
    if status is not None:
        query = query.where(models.RequestEvent.status == status) 
    
    if user_id is not None:
        query = query.where(models.RequestEvent.status == user_id) 

    if start_time is not None:
        query = query.where(models.RequestEvent.status == start_time) 


    if end_time is not None:
        query = query.where(models.RequestEvent.status == end_time) 
    
    # 2. Execute the query
    result = await db.execute(query) # This gives us a Result object that contains the raw results from the database, but we still need to extract the actual Python objects from it
    
    # 3. Extract the clean Python objects
    pending_requests = result.scalars().all()  # scalars() gives us the actual RequestEvent objects instead of SQLAlchemy Row objects, and all() gives us a list of them
    
    # FastAPI automatically converts these Python objects directly into perfect JSON!
    return {"event_requests": pending_requests}




@router.get("/user/view-my-events")
async def view_events(
    user_id: str,
    Date:Optional[Date] = None,
    venue_id: str = None,
    place_id: str = None,
    db: AsyncSession = Depends(get_db)
    ):
    
        
    query = select(models.Event).where(models.Event.event_by_user_id == user_id)

    if Date:
        query = query.where(models.Event.Date == Date)
    if place_id:
        query = query.where(models.Event.place_id == place_id)

    if venue_id:
        query = query.where(models.Event.place_id.venue_id == venue_id)
    
    result = await db.execute(query)
    user_events = result.scalars().all() # Again, we extract the actual Event objects from the Result
    return {"my_events": user_events}



@router.get("/admin/view-events")
async def admin_view_events(
    user_id: Optional[str] = None,
    Date:Optional[Date] = None,
    venue_id: str = None,
    place_id: str = None,
    db: AsyncSession = Depends(get_db)
    ):

    query = select(models.Event)
    if user_id:   
        query = select(models.Event).where(models.Event.event_by_user_id == user_id)

    if Date:
        query = query.where(models.Event.Date == Date)
    if place_id:
        query = query.where(models.Event.place_id == place_id)

    if venue_id:
        query = query.where(models.Event.place_id.venue_id == venue_id)
    
    result = await db.execute(query)
    events = result.scalars().all() # Again, we extract the actual Event objects from the Result
    return {"events": events}







