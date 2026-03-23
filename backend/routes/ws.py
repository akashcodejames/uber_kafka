import asyncio
import json
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from auth import ALGORITHM, SECRET_KEY, get_current_user
from core.kafka_producer import publish_rider_location
from core.redis_client import get_redis_client
from database import get_db
import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])


async def get_user_from_token(token: str, db) -> models.User:
    """Helper to authenticate a WebSocket connection using a JWT token query parameter."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return db.query(models.User).filter(models.User.id == int(user_id)).first()
    except JWTError:
        return None


@router.websocket("/rider")
async def websocket_rider(websocket: WebSocket, token: str):
    """
    Rider Endpoint: Receives periodic GPS coordinates from an active rider
    and publishes them to Kafka.
    """
    await websocket.accept()
    
    # Authenticate
    from database import SessionLocal
    db = SessionLocal()
    user = await get_user_from_token(token, db)
    db.close()
    
    if not user:
        await websocket.close(code=1008, reason="Invalid token")
        return
        
    logger.info(f"Rider {user.id} ({user.name}) connected to GPS ingestion WS")

    try:
        while True:
            # Expecting JSON: {"lat": 12.34, "lng": 56.78}
            data = await websocket.receive_json()
            lat = data.get("lat")
            lng = data.get("lng")
            
            if lat and lng:
                await publish_rider_location(rider_id=str(user.id), lat=float(lat), lng=float(lng))
                
    except WebSocketDisconnect:
        logger.info(f"Rider {user.id} disconnected")
    except Exception as e:
        logger.error(f"Rider WS error: {e}")
        await websocket.close()


@router.websocket("/user")
async def websocket_user(websocket: WebSocket, token: str):
    """
    User Endpoint: Subscribes to Redis Pub/Sub and pushes real-time rider 
    location updates to the connected user's browser.
    """
    await websocket.accept()
    
    # Authenticate
    from database import SessionLocal
    db = SessionLocal()
    user = await get_user_from_token(token, db)
    db.close()
    
    if not user:
        await websocket.close(code=1008, reason="Invalid token")
        return

    logger.info(f"User {user.id} ({user.name}) connected to listen for riders")
    
    redis_client = await get_redis_client()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("rider_updates")

    async def reader_task():
        """Continuously reads from Redis Pub/Sub and forwards to WebSocket"""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = message["data"]
                    # Forward the JSON string directly to the React client
                    await websocket.send_text(payload)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error reading from pubsub: {e}")

    # Run the Redis reader in the background
    task = asyncio.create_task(reader_task())

    try:
        # Keep connection alive; optionally handle incoming pings
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"User {user.id} disconnected")
    finally:
        task.cancel()
        await pubsub.unsubscribe("rider_updates")
