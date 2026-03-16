# models.py
from datetime import date

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base # Import the Base from your database.py file


class Admin(Base):
    __tablename__ = "admins"
    
    admin_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) # In a real app, you'd store a hashed password, not plain text!


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) # In a real app, you'd store a hashed password, not plain text!


# 1. VENUE
class Venue(Base):
    __tablename__ = "venues"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    places = relationship("Place", back_populates="venue")

# 2. PLACE 
class Place(Base):
    __tablename__ = "places"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # FIXED: This must be a String because Venue.id is a String
    venue_id = Column(String, ForeignKey("venues.id")) 
    
    venue = relationship("Venue", back_populates="places")
    events = relationship("Event", back_populates="place")



# 3. EVENT 
class Event(Base):
    __tablename__ = "events"
    
    event_id = Column(String, primary_key=True, index=True)
    event_name = Column(String, nullable=False)
    event_description = Column(String, nullable=True)
    
    # FIXED: This must be a String because Place.id is a String
    place_id = Column(String, ForeignKey("places.id"))
    


    event_by_user_id = Column(String,ForeignKey("users.id"), nullable=True) # ID of the user who created this event (if it was created by an admin, this can be null)

    Date = Column(DateTime, nullable = False)
    start_time = Column(DateTime, nullable= False) # When the event starts
    end_time = Column(DateTime, nullable=False) # When the event ends

# 4. SEAT 
class Seat(Base):
    __tablename__ = "seats"
    
    id = Column(Integer, primary_key=True, index=True) # Integer is fine here!
    seat_no = Column(String, nullable=False) 
    
    # FIXED: This must be a String because Event.event_id is a String
    event_id = Column(String, ForeignKey("events.event_id"))
    
    locked = Column(Boolean, default=False)
    booked = Column(Boolean, default=False)
    
    user_id = Column(Integer, nullable=True)
    booking_time = Column(DateTime, nullable=True) 
    
    event = relationship("Event", back_populates="seats")



class RequestEvent(Base): # This model is for user-submitted event requests that admins can approve or reject
    __tablename__ = "request_events" 

    event_id = Column(String, primary_key=True, index=True)
    event_name = Column(String, nullable=False)
    event_description = Column(String, nullable=True)
    
    # FIXED: This must be a String because Place.id is a String
    place_id = Column(String, ForeignKey("places.id"))
    

    event_by_user_id = Column(String,ForeignKey("users.id"), nullable=True) # ID of the user who created this event (if it was created by an admin, this can be null)


    start_time = Column(DateTime, nullable=True) # When the event starts
    end_time = Column(DateTime, nullable=True) # When the event ends

    requested_at = Column(DateTime(timezone=True), server_default=func.now()) # Timestamp for when the request was submitted, with timezone support



class RejectedRequestEvent(Base):
    __tablename__ = "rejected_request_events"
    
    id = Column(String, primary_key=True, index=True)
    original_request_id = Column(String, nullable=False)
    rejection_reason = Column(String, nullable=False)  
    
    # We must copy EVERYTHING now, because the original row is getting deleted
    event_name = Column(String, nullable=False)
    event_description = Column(String, nullable=True)
    requested_by_user = Column(String, nullable=True)
    place_id = Column(String, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    rejected_at = Column(DateTime(timezone=True), server_default=func.now())

# class DeleteEvent(Base):
#     __tablename__ = "deleted_events"
    

#     event_id = Column(String, primary_key=True, index=True)
#     event_name = Column(String, nullable=False)
#     event_description = Column(String, nullable=True)
    
#     # FIXED: This must be a String because Place.id is a String
#     place_id = Column(String, ForeignKey("places.id"))
    

#     event_by_user_id = Column(String,ForeignKey("users.id"), nullable=True) # ID of the user who created this event (if it was created by an admin, this can be null)


#     start_time = Column(DateTime, nullable=True) # When the event starts
#     end_time = Column(DateTime, nullable=True) # When the event ends

#     reason = Column(String, nullable=False)



class DeleteRequestEvent(Base): # This model is for logging deleted event REQUESTS (not actual events, but the user-submitted requests that admins can approve or reject)
    __tablename__ = "deleted_request_events"

    event_id = Column(String, primary_key=True, index=True)
    event_name = Column(String, nullable=False)
    event_description = Column(String, nullable=True)
    
    # FIXED: This must be a String because Place.id is a String
    place_id = Column(String, ForeignKey("places.id"))
    

    event_by_user_id = Column(String,ForeignKey("users.id"), nullable=True) # ID of the user who created this event (if it was created by an admin, this can be null)


    start_time = Column(DateTime, nullable=True) # When the event starts
    end_time = Column(DateTime, nullable=True) # When the event ends

    reason = Column(String, nullable=False)

    deleted_at = Column(DateTime(timezone=True), server_default=func.now()) # Timestamp for when the delete action occurred, with timezone support


    

class RequestDeleteEvent(Base): # This model is for user-submitted delete requests for existing events (not event requests, but actual events that have already been approved and exist in the system)
    __tablename__ = "delete_event_requests"

    event_id = Column(String, primary_key=True, index=True)
    event_name = Column(String, nullable=False)
    event_description = Column(String, nullable=True)
    
    # FIXED: This must be a String because Place.id is a String
    place_id = Column(String, ForeignKey("places.id"))
    

    event_by_user_id = Column(String,ForeignKey("users.id"), nullable=True) # ID of the user who created this event (if it was created by an admin, this can be null)


    start_time = Column(DateTime, nullable=True) # When the event starts
    end_time = Column(DateTime, nullable=True) # When the event ends

    reason = Column(String, nullable=False)

    requested_at = Column(DateTime(timezone=True), server_default=func.now()) # Timestamp for when the delete request was submitted, with timezone support