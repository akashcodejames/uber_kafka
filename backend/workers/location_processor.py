import asyncio
import json
import logging
from typing import Optional

from aiokafka import AIOKafkaConsumer

from core.kafka_producer import KAFKA_BOOTSTRAP_SERVERS, RIDER_LOCATION_TOPIC
from core.redis_client import publish_rider_update, update_rider_location

logger = logging.getLogger(__name__)

_consumer_task: Optional[asyncio.Task] = None


async def consume_rider_locations():
    """
    Background loop that reads from Kafka 'rider-locations' topic.
    Updates Redis Geo records and publishes to Redis Pub/Sub.
    """
    consumer = AIOKafkaConsumer(
        RIDER_LOCATION_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="rider-locations-processor",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
    )
    
    await consumer.start()
    logger.info("Kafka Consumer started for rider locations")

    try:
        # Listen indefinitely
        async for msg in consumer:
            data = msg.value
            rider_id = data.get("rider_id")
            lat = data.get("lat")
            lng = data.get("lng")

            if not all([rider_id, lat, lng]):
                continue

            try:
                # 1. Update the Geohash index in Redis
                await update_rider_location(rider_id, lat, lng)
                # 2. Fan-out to connected WebSockets via Redis Pub/Sub
                await publish_rider_update(rider_id, lat, lng)
            except Exception as e:
                logger.error(f"Error processing location for rider {rider_id}: {e}")
                
    except asyncio.CancelledError:
        logger.info("Kafka consumer cancelled via shutdown signal")
    finally:
        await consumer.stop()
        logger.info("Kafka Consumer stopped")


def start_location_processor():
    """Starts the Kafka consumer in an asyncio task."""
    global _consumer_task
    _consumer_task = asyncio.create_task(consume_rider_locations())


async def stop_location_processor():
    """Cancels and awaits the Kafka consumer task."""
    global _consumer_task
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
        _consumer_task = None
