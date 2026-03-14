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

    # event = result.scalar_one_or_none()
    # if event is None:
    #     return {"message": "Event not found."}
    # await db.delete(event)
    # await
    # await db.commit()
    # return {"message": "Event deleted successfully."}