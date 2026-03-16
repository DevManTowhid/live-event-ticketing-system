import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select
from passlib.context import CryptContext

# It is much safer to import models like this so we always know where things come from!
import models 
from database import get_db 

# 1. Create the router (the "extension cord")
router = APIRouter()

# 2. Setup the Password Hashing Engine
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 


# ==========================================
# PYDANTIC SCHEMAS (The Bouncers)
# ==========================================
class AdminLoginData(BaseModel):
    email: str
    password: str

class UserRegisterData(BaseModel):
    email: str
    password: str

class UserLoginData(BaseModel):
    email: str
    password: str

class VenueCreateData(BaseModel):
    name: str

class CreateEventData(BaseModel):
    event_name: str
    place_id: str
    start_time: datetime
    end_time: datetime
    event_description: Optional[str] = None
    event_by_user_id: Optional[str] = None

class UserEventRequestData(BaseModel):
    event_name: str
    event_description: Optional[str] = None
    requested_by_user: Optional[str] = None
    # We need these so the Admin knows WHEN the user wants the event!
    start_time: datetime
    end_time: datetime

class ApproveRequestData(BaseModel):
    request_id: str
    place_id: str


# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@router.post("/admin/login")
async def admin_login(data: AdminLoginData, db: AsyncSession = Depends(get_db)):
    query = select(models.User).where(models.User.email == data.email)
    result = await db.execute(query)
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if admin_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Admin privileges required.")
        
    is_password_correct = pwd_context.verify(data.password, admin_user.password_hash)
    if not is_password_correct:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    return {
        "message": "Login successful",
        "user_id": admin_user.id,
        "email": admin_user.email,
        "role": admin_user.role,
        "access_token": "mock_jwt_token_for_now",
        "token_type": "bearer"
    }

@router.post("/user/register")
async def user_register(data: UserRegisterData, db: AsyncSession = Depends(get_db)):
    query = select(models.User).where(models.User.email == data.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered.")
    
    new_user_id = str(uuid.uuid4())
    # Hash the password before saving!
    hashed_password = pwd_context.hash(data.password) 
    
    new_user = models.User(
        id=new_user_id, 
        email=data.email, 
        password_hash=hashed_password,
        role="user" # Default role
    ) 
    
    db.add(new_user)
    await db.commit()
    
    return {
        "message": f"User '{new_user.email}' registered successfully!", 
        "user_id": new_user.id
    }

@router.post("/user/login")
async def user_login(data: UserLoginData, db: AsyncSession = Depends(get_db)):  
    query = select(models.User).where(models.User.email == data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
    # Cryptographically verify the hash!
    is_password_correct = pwd_context.verify(data.password, user.password_hash)
    if not is_password_correct:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    return {
        "message": f"User '{user.email}' logged in successfully!", 
        "user_id": user.id
    }


# ==========================================
# VENUE & EVENT MANAGEMENT ENDPOINTS
# ==========================================

@router.post("/admin/create-venue")
async def create_venue(data: VenueCreateData, db: AsyncSession = Depends(get_db)):
    new_venue_id = str(uuid.uuid4())
    new_venue = models.Venue(id=new_venue_id, name=data.name)
    
    db.add(new_venue)
    await db.commit()
    
    return {
        "message": f"Venue '{new_venue.name}' created successfully!",
        "venue_id": new_venue.id
    }

@router.post("/admin/create-event")
async def create_event(data: CreateEventData, db: AsyncSession = Depends(get_db)):
    new_event_id = str(uuid.uuid4())
    new_event = models.Event(
        event_id=new_event_id, # Fixed bug: Was previously event_id=new_event
        place_id=data.place_id,
        event_name=data.event_name,
        event_description=data.event_description,
        start_time=data.start_time,
        end_time=data.end_time,
        event_by_user_id=data.event_by_user_id 
    )
    
    db.add(new_event)
    await db.commit()
    
    return {
        "message": f"Event '{new_event.event_name}' created successfully!",
        "event_id": new_event.event_id,
    }


# ==========================================
# REQUEST & APPROVAL ENDPOINTS
# ==========================================

@router.post("/user/request-event")
async def request_event(data: UserEventRequestData, db: AsyncSession = Depends(get_db)):
    new_request_id = str(uuid.uuid4())
    new_request = models.RequestEvent(
        id=new_request_id,
        event_name=data.event_name,
        event_description=data.event_description,
        requested_by_user_id=data.requested_by_user,
        start_time=data.start_time,
        end_time=data.end_time,
        status="pending"
    )
    
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request) # We refresh here to grab the database-generated properties
    
    return {
        "message": f"Event '{new_request.event_name}' pushed to request queue successfully!",
        "request_id": new_request.id,
        "status": new_request.status
    }

# Fixed missing slash!
@router.post("/admin/approve-event-request")
async def approve_event_request(data: ApproveRequestData, db: AsyncSession = Depends(get_db)):
    query = select(models.RequestEvent).where(models.RequestEvent.id == data.request_id)
    result = await db.execute(query)
    pending_request = result.scalar_one_or_none()
    
    if not pending_request:
        raise HTTPException(status_code=404, detail="Event request not found.")
    if pending_request.status != "pending":
        raise HTTPException(status_code=400, detail=f"Event request is already {pending_request.status}.")

    new_event_id = str(uuid.uuid4())
    new_event = models.Event(
        event_id=new_event_id,
        event_name=pending_request.event_name,
        event_description=pending_request.event_description,
        place_id=data.place_id,
        start_time=pending_request.start_time,
        end_time=pending_request.end_time,
        event_by_user_id=pending_request.requested_by_user_id
    )

    pending_request.status = "approved"

    db.add(new_event)
    # SQLAlchemy already tracks pending_request, no need to db.add() it again
    
    await db.commit() 

    return {
        "message": f"Event Request '{pending_request.event_name}' approved and event created successfully!",
        "event_id": new_event.event_id
    }