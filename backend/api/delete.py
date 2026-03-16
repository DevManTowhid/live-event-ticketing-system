import uuid

from fastapi import APIRouter, HTTPException
import models 
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from sqlalchemy import select, insert
from fastapi import Depends

# 1. Create the router (the "extension cord")
router = APIRouter()


@router.delete("/user/delete-event-request/{event_id}")
async def delete_event(
    event_id: str, 
    reason: str = "", 
    db: AsyncSession = Depends(get_db)
):
    # 1. FETCH FIRST (This fixes the time-travel crash)
    query = select(models.RequestEvent).where(models.RequestEvent.event_id == event_id)
    result = await db.execute(query)
    event_to_delete = result.scalar_one_or_none()

    # 2. CHECK IF IT EXISTS BEFORE DOING ANYTHING ELSE
    if not event_to_delete:
        raise HTTPException(status_code=404, detail="Event not found.")

    # 3. BUILD THE AUDIT LOG (Using the ORM instead of raw insert strings)
    audit_log = models.DeleteRequestEvent(
        event_id=event_to_delete.event_id,
        reason=reason,
        event_name=event_to_delete.event_name,
        event_description=event_to_delete.event_description,
        place_id=event_to_delete.place_id,
        # Assuming you have these columns in your models:
        event_by_user_id=event_to_delete.event_by_user_id,
        start_time=event_to_delete.start_time,
        end_time=event_to_delete.end_time
    )

    # 4. QUEUE UP BOTH ACTIONS (Add the log, Delete the event)
    db.add(audit_log)
    await db.delete(event_to_delete)
    
    # 5. THE SINGLE COMMIT (All or Nothing)
    # If the delete fails, the log isn't saved. If the log fails, the delete is canceled.
    await db.commit() 

    return {
        "message": f"Event Request'{event_to_delete.event_name}' safely deleted.",
        "reason_logged": audit_log.reason
    }



# This endpoint is for admins to reject pending event requests, which moves them from the waiting room to the graveyard with a rejection reason.
@router.delete("/admin/reject-request/{request_id}")
async def reject_request(
    request_id: str, 
    reason: str="", # FastAPI automatically turns this into a URL query parameter!
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch the pending request from the waiting room
    query = select(models.RequestEvent).where(models.RequestEvent.id == request_id)
    result = await db.execute(query)
    pending_request = result.scalar_one_or_none()
    
    # --- SAFETY CHECKS ---
    if not pending_request:
        raise HTTPException(status_code=404, detail="Event request not found.")

    

    # 2. Stuff the data into the Graveyard (Copying everything!)
    rejection_log = models.RejectedRequestEvent(
        id=str(uuid.uuid4()),
        original_request_id=pending_request.id,
        rejection_reason=reason,
        
        # Copying the full payload
        event_name=pending_request.event_name,
        event_description=pending_request.event_description,
        requested_by_user=pending_request.requested_by_user,
        place_id=pending_request.place_id,
        start_time=pending_request.start_time,
        end_time=pending_request.end_time
    )
    
    # 3. QUEUE BOTH ACTIONS: Insert into Graveyard, Delete from Waiting Room
    db.add(rejection_log)
    await db.delete(pending_request) # The physical destruction
    
    # 4. The ACID Transaction (Execute both at the exact same time)
    await db.commit()

    return {
        "message": f"Event request '{pending_request.event_name}' has been rejected and archived.",
        "request_id": pending_request.id,
        "reason": reason
    }