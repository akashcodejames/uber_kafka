import json
import logging
import os

from aiokafka import AIOKafkaProducer
from dotenv import load_dotenv

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
RIDER_LOCATION_TOPIC = "rider-locations"

logger = logging.getLogger(__name__)

# Global producer instance
_producer = None


async def get_kafka_producer() -> AIOKafkaProducer:
    """Get or create the global AIOKafkaProducer instance."""
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await _producer.start()
        logger.info("Kafka Producer started")
    return _producer


async def close_kafka_producer():
    """Stop the global Kafka producer."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        logger.info("Kafka Producer stopped")
        _producer = None


async def publish_rider_location(rider_id: str, lat: float, lng: float):
    """
    Publish a rider's GPS location to the Kafka topic.
    """
    producer = await get_kafka_producer()
    payload = {
        "rider_id": rider_id,
        "lat": lat,
        "lng": lng,
    }
    # We use rider_id as the key to ensure ordering of events for the same rider
    await producer.send_and_wait(
        topic=RIDER_LOCATION_TOPIC,
        key=str(rider_id).encode("utf-8"),
        value=payload,
    )
