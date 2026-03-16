from fastapi import APIRouter, HTTPException
from database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from models import *
from fastapi import Depends
# 1. Create the router (the "extension cord")
router = APIRouter()

@router.put("admin/update-password")
async def update_password(email: str, old_password: str,new_password: str, db: AsyncSession = Depends(get_db)):
    # This is a placeholder implementation. In a real app, you'd verify the admin's identity, hash the new password, and update it in the database.
    if email == "" or new_password == "":
        raise HTTPException(status_code=400, detail="Email and new password are required.")
    
    # Here you would add logic to find the admin by email and update their password in the database.
    
    query = select(Admin).where(Admin.email == email)
    result = await db.execute(query)
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    password = admin.password_hash
    
    if old_password != password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    admin.password_hash = new_password # In a real app, you'd hash the new password before storing it
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
        

    return {"message": f"Password for '{email}' updated successfully!"}