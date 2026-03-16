from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

import models
from database import get_db

# 1. Create the router
router = APIRouter()

# 2. Setup the Password Hashing Engine
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==========================================
# PYDANTIC SCHEMAS (The Data Shields)
# ==========================================

class UpdatePasswordData(BaseModel):
    email: str
    old_password: str
    new_password: str

class UpdateUserProfileData(BaseModel):
    # We don't let them update their user_id or email here for security reasons!
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None

class UpdateEventData(BaseModel):
    event_name: Optional[str] = None
    event_description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    # Notice we do NOT let them update the place_id. If a venue changes, 
    # that usually requires canceling and recreating the event for ticket holders.


# ==========================================
# AUTHENTICATION UPDATE ENDPOINTS
# ==========================================

@router.put("/admin/update-password")
async def update_admin_password(data: UpdatePasswordData, db: AsyncSession = Depends(get_db)):
    # 1. Fetch the admin
    query = select(models.User).where(models.User.email == data.email)
    result = await db.execute(query)
    admin = result.scalar_one_or_none()
    
    # 2. Safety Checks
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
    # 3. Cryptographic Verification
    if not pwd_context.verify(data.old_password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
    # 4. Hash and Update
    admin.password_hash = pwd_context.hash(data.new_password)
    
    db.add(admin)
    await db.commit()

    return {"message": "Admin password updated successfully!"}


@router.put("/user/update-password")
async def update_user_password(data: UpdatePasswordData, db: AsyncSession = Depends(get_db)):
    # Same exact logic as admin, but ensuring the role is "user"
    query = select(models.User).where(models.User.email == data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or user.role != "user":
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
    if not pwd_context.verify(data.old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
    user.password_hash = pwd_context.hash(data.new_password)
    
    db.add(user)
    await db.commit()

    return {"message": "User password updated successfully!"}


# ==========================================
# RESOURCE UPDATE ENDPOINTS
# ==========================================



@router.put("/user/update-profile/{user_id}")
async def update_user_profile(
    user_id: str, 
    data: UpdateUserProfileData, 
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch the user
    query = select(models.User).where(models.User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # 2. Update only the fields that were provided (Dynamic Update)
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.phone_number is not None:
        user.phone_number = data.phone_number
        
    db.add(user)
    await db.commit()
    
    return {"message": "Profile updated successfully!"}


@router.put("/admin/update-event/{event_id}")
async def update_event_details(
    event_id: str, 
    data: UpdateEventData, 
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch the official event
    query = select(models.Event).where(models.Event.event_id == event_id)
    result = await db.execute(query)
    event_to_update = result.scalar_one_or_none()
    
    if not event_to_update:
        raise HTTPException(status_code=404, detail="Event not found.")

    # 2. Determine the proposed new times (Fallback to existing if not updated)
    proposed_start = data.start_time if data.start_time else event_to_update.start_time
    proposed_end = data.end_time if data.end_time else event_to_update.end_time

    # 3. THE COLLISION SHIELD (Check for overlaps)
    # Only run this expensive check if they are actually changing the times
    if data.start_time or data.end_time:
        
        # Make sure the end time is actually after the start time!
        if proposed_end <= proposed_start:
            raise HTTPException(status_code=400, detail="End time must be after start time.")

        collision_query = select(models.Event).where(
            and_(
                models.Event.place_id == event_to_update.place_id, # Must be the same venue
                models.Event.event_id != event_id,                 # Don't check the event against itself!
                models.Event.start_time < proposed_end,            # Math overlap rule 1
                models.Event.end_time > proposed_start             # Math overlap rule 2
            )
        )
        collision_result = await db.execute(collision_query)
        conflicting_event = collision_result.scalar_one_or_none()
        
        if conflicting_event:
            raise HTTPException(
                status_code=409, # 409 Conflict is the perfect REST status code here
                detail=f"Time collision! Venue is already booked for '{conflicting_event.event_name}' from {conflicting_event.start_time} to {conflicting_event.end_time}."
            )

    # 4. Safe to Update
    if data.event_name is not None:
        event_to_update.event_name = data.event_name
    if data.event_description is not None:
        event_to_update.event_description = data.event_description
    if data.start_time is not None:
        event_to_update.start_time = data.start_time
    if data.end_time is not None:
        event_to_update.end_time = data.end_time
        
    db.add(event_to_update)
    await db.commit()
    
    return {
        "message": f"Event '{event_to_update.event_name}' updated successfully!",
        "event_id": event_to_update.event_id
    }
