from fastapi import APIRouter
from pydantic import BaseModel

# 1. Create the router (the "extension cord")
router = APIRouter()

from typing import Optional

class UserEventRequest(BaseModel): # This is a Pydantic model to represent the data structure of an event request from a user
    
    event_name: str
    event_description: Optional[str] = None
    requested_by_user: Optional[str] = None

@router.post("/admin/login")
async def admin_login(email: str = "", password: str = ""):
    # dummy check for admin credentials (in a real app, you'd check against a database)
    if email != "" and password != "":
        return {"message": "Admin login successful!"}
    else:
        return {"message": "Invalid credentials"}

# @router.post("/admin/create-venue")
# async def create_venue(name: str = ""):
#     if name != "":
#         return {"message": f"Venue '{name}' created successfully!"}
#     else:
#         return {"message": "Venue name cannot be empty."}

# @router.post("/admin/create-place")
# async def create_place(name: str = "", venue_id: str = ""):
#     if name != "" and venue_id != "":
#         return {"message": f"Place '{name}' created successfully under Venue ID {venue_id}!"}
#     else:
#         return {"message": "Place name and Venue ID cannot be empty."}

@router.post("/admin/create-event")
async def create_event(event_name: str = "", event_description: str = "", place_id: str = ""):
    if event_name != "" and place_id != "":
        return {"message": f"Event '{event_name}' created successfully under Place ID {place_id}!"}
    else:
        return {"message": "Event name and Place ID cannot be empty."}
    
@router.post("/user/request-event")
async def request_event(event_name: str = "", event_id = None):
    if event_name != "" and even_id:
        return {"message": f"Event '{event_name}' requested successfully!"}
    else:
        return {"message": "Event name cannot be empty."}
    
@router.post("/admin/approve-event")
async def approve_event(event_name: str = "", event_id : str = ""):
    if event_name != "":
        return {"message": f"Event '{event_name}' approved successfully!"}
    else:
        return {"message": "Event name cannot be empty."}


