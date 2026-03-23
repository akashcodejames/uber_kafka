import logging
import os

import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

logger = logging.getLogger(__name__)

# Global redis pool
_redis_client: redis.Redis = None


async def get_redis_client() -> redis.Redis:
    """Get or create the global async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        logger.info("Connected to Redis")
    return _redis_client


async def close_redis_client():
    """Close the global Redis client."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        logger.info("Redis connection closed")
        _redis_client = None


async def update_rider_location(rider_id: str, lat: float, lng: float):
    """
    Store the rider's latest location in a Redis Geo structure.
    We'll store all active riders under a single key 'active_riders'.
    """
    client = await get_redis_client()
    # GeoAdd: key, lng, lat, member
    await client.geoadd("active_riders", (lng, lat, str(rider_id)))


async def get_nearby_riders(lat: float, lng: float, radius_km: float = 5.0) -> list:
    """
    Retrieve riders near a specific coordinate.
    """
    client = await get_redis_client()
    # GEORADIUS is deprecated in modern Redis in favor of GEOSEARCH, but we can use geosearch.
    # geosearch(key, longitude, latitude, radius, unit)
    results = await client.geosearch(
        "active_riders",
        longitude=lng,
        latitude=lat,
        radius=radius_km,
        unit="km",
        withcoord=True,
    )
    
    # Format results
    riders = []
    for member_id, (member_lng, member_lat) in results:
        riders.append({
            "rider_id": member_id,
            "lat": member_lat,
            "lng": member_lng
        })
    return riders


async def publish_rider_update(rider_id: str, lat: float, lng: float):
    """
    Publish a fast update via Redis Pub/Sub.
    Users connected via WebSockets will be subscribed to 'rider_updates'.
    """
    # Simply broadcast to a global 'rider_updates' channel for now
    # (In production, you'd shard this by city or geohash sector to limit fan-out)
    client = await get_redis_client()
    import json
    payload = json.dumps({"rider_id": rider_id, "lat": lat, "lng": lng})
    await client.publish("rider_updates", payload)
