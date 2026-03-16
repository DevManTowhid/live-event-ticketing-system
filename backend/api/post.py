import uuid

from click import DateTime
from database import get_db 
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession 

from models import *
from sqlalchemy import select, insert

# 1. Create the router (the "extension cord")
router = APIRouter()

from typing import Optional

class UserEventRequest(BaseModel): # This is a Pydantic model to represent the data structure of an event request from a user
    
    event_name: str
    event_description: Optional[str] = None
    requested_by_user: Optional[str] = None


class ApproveRequestData(BaseModel):
    request_id: str
    place_id: str  # The physical room the admin is assigning this event to

class CreateEventData(BaseModel):
    event_id: Optional[str] = None # This will be generated automatically if not provided
    event_name: str
    event_description: Optional[str] = None
    place_id: str
    start_time: DateTime
    end_time: DateTime
    event_by_user_id: Optional[str] = None


class AdminLoginData(BaseModel):
    email: str
    password: str

class UserRegisterData(BaseModel):
    email: str
    password: str


@router.post("/admin/login")
async def admin_login(email: str = "", password: str = ""):
    # proper real app implementation 
    if email == "" or password == "":
        raise HTTPException(status_code=400, detail="Email and password are required.")
    
    query = select(Admin).where(Admin.email == email)
    result = await db.execute(query)
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    # In a real app, you'd verify the password hash here instead of comparing plain text
    if password != admin.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    return {"message": f"Admin '{admin.email}' logged in successfully!"}


@router.post("/user/register")
async def user_register(email: str = "", password: str = "", db: AsyncSession = Depends(get_db)):
    if email == "" or password == "":
        raise HTTPException(status_code=400, detail="Email and password are required.")
    
    # Check if the email is already registered
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered.")
    
    new_user_id = str(uuid.uuid4())
    new_user = User(user_id=new_user_id, email=email, password_hash=password) # In a real app, you'd hash the password before storing it
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {"message": f"User '{new_user.email}' registered successfully!", "user_id": new_user.user_id}
    
    


    


@router.post("/admin/create-venue")
async def create_venue(name: str = "", db: AsyncSession = Depends(get_db)):
    new_venue_id = str(uuid.uuid4()) # Generate a unique ID for the new venue
    new_venue = Venue(id=new_venue_id, name=name)
    db.add(new_venue)
    await db.commit()
    await db.refresh(new_venue)
    return {
        "message": f"Venue '{new_venue.name}' created successfully!",
        "venue_id": new_venue.id
    }
            


@router.post("/admin/create-event")
async def create_event(event_name: str, place_id: str, start_time:DateTime, end_time:DateTime,event_by_user_id:str, event_description: str = "", db: AsyncSession = Depends(get_db)):

    new_event_id = str(uuid.uuid4()) # Generate a unique ID for the new event
    new_event = Event(
        event_id=new_event,
        place_id=place_id,
        event_name=event_name,
        event_description=event_description,
        start_time = start_time,
        end_time = end_time,
        event_by_user_id = event_by_user_id # Since this is created by an admin, we can set the creator to None or a special admin ID
    )
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return {
        "message": f"Event '{new_event.event_name}' created successfully!",
        "event_id": new_event.event_id,
        
    }

    




@router.post("/user/request-event")
async def request_event(event_request: UserEventRequest, db: AsyncSession = Depends(get_db)):
    new_request_id  = str(uuid.uuid4()) # Generate a unique ID for the new event request
    new_request = RequestEvent(
        id=new_request_id,
        event_name=event_request.event_name,
        event_description=event_request.event_description,
        requested_by_user_id=event_request.requested_by_user
    )
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)
    return {
        "message": f"Event '{new_request.event_name}' pushed to request queue successfully!",
        "request_id": new_request.id,
        "status": new_request.status
    }

                        
    
    
    







@router.post("admin/approve-event-request/{request_id}")

async def approve_event_request(request_id: str, place_id: str,db: AsyncSession = Depends(get_db)):
    # 1. Fetch the pending request from the waiting room
    query = select(models.RequestEvent).where(models.RequestEvent.id == request_id)
    result = await db.execute(query)
    pending_request = result.scalar_one_or_none()
    
    # --- SAFETY CHECKS ---
    if not pending_request:
        raise HTTPException(status_code=404, detail="Event request not found.")
    
    if pending_request.status != "pending":
        raise HTTPException(status_code=400, detail=f"Event request is already {pending_request.status}.")

    # 2. Create a new Event based on the request data
    new_event_id = str(uuid.uuid4())
    new_event = Event(
        event_id=new_event_id,
        event_name=pending_request.event_name,
        event_description=pending_request.event_description,
        place_id=place_id,
        start_time=pending_request.start_time,
        end_time=pending_request.end_time,
        event_by_user_id=pending_request.requested_by_user_id
    )

    # 3. Update the request status to "approved"
    pending_request.status = "approved"

    # 4. QUEUE UP BOTH ACTIONS (Add the new event, Update the request status)
    db.add(new_event)
    db.add(pending_request)
    
    # 5. THE SINGLE COMMIT (All or Nothing)
    # If adding the event fails, the request status won't be updated. If updating the status fails, the event won't be added.
    await db.commit() 

    return {
        "message": f"Event Request '{pending_request.event_name}' approved and event created successfully!",
        "event_id": new_event.event_id
    }