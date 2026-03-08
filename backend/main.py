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


from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base

# 1. VENUE (e.g., "National Stadium")
class Venue(Base):
    __tablename__ = "venues"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Links Venue down to Places
    places = relationship("Place", back_populates="venue")


# 2. PLACE (e.g., "VIP Lounge" or "Grandstand")
class Place(Base):
    __tablename__ = "places"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    venue_id = Column(Integer, ForeignKey("venues.id"))
    
    venue = relationship("Venue", back_populates="places")
    events = relationship("Event", back_populates="place")


# 3. EVENT (e.g., "Tech Conference 2026")
class Event(Base):
    __tablename__ = "events"
    
    event_id = Column(String, primary_key=True, index=True)
    event_name = Column(String, nullable=False)
    event_description = Column(String, nullable=True)
    
    place_id = Column(Integer, ForeignKey("places.id"))
    
    place = relationship("Place", back_populates="events")
    seats = relationship("Seat", back_populates="event")


# 4. SEAT (e.g., "Seat A-12")
class Seat(Base):
    __tablename__ = "seats"
    
    id = Column(Integer, primary_key=True, index=True)
    seat_no = Column(String, nullable=False) 
    event_id = Column(Integer, ForeignKey("events.event_id"))
    
    # --- Your Boolean Status Logic ---
    locked = Column(Boolean, default=False)
    booked = Column(Boolean, default=False)
    
    # --- The User and Timestamp ---
    user_id = Column(Integer, nullable=True)
    booking_time = Column(DateTime, nullable=True) 
    
    event = relationship("Event", back_populates="seats")