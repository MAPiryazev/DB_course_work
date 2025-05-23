import redis
import json
from datetime import timedelta
from settings import REDIS_CONFIG
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=REDIS_CONFIG['host'],
                port=REDIS_CONFIG['port'],
                db=REDIS_CONFIG['db'],
                password=REDIS_CONFIG['password'],
                decode_responses=True
            )
            # Проверка подключения
            self.redis_client.ping()
            logger.info("Successfully connected to Redis")
            self.pubsub = self.redis_client.pubsub()
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    # Token management
    def store_token(self, user_id: str, token: str, ttl: int = 3600):
        """Store user token with TTL"""
        try:
            key = f"token:{user_id}"
            logger.info(f"Attempting to store token for user {user_id} with key {key}")
            self.redis_client.setex(key, ttl, token)
            # Verify the token was stored
            stored_token = self.redis_client.get(key)
            logger.info(f"Token stored successfully. Verification: {'Token found' if stored_token else 'Token not found'}")
        except Exception as e:
            logger.error(f"Failed to store token for user {user_id}: {e}")
            raise

    def get_token(self, user_id: str) -> str:
        """Get user token"""
        try:
            key = f"token:{user_id}"
            logger.info(f"Attempting to get token for user {user_id} with key {key}")
            token = self.redis_client.get(key)
            logger.info(f"Token retrieval {'successful' if token else 'failed'} for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to get token for user {user_id}: {e}")
            raise

    def delete_token(self, user_id: str):
        """Delete user token"""
        try:
            self.redis_client.delete(f"token:{user_id}")
            logger.info(f"Deleted token for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete token for user {user_id}: {e}")
            raise

    # Session management
    def store_session(self, session_id: str, data: dict, ttl: int = 1800):
        """Store session data"""
        try:
            self.redis_client.setex(f"session:{session_id}", ttl, json.dumps(data))
            logger.info(f"Stored session {session_id} with TTL {ttl}")
        except Exception as e:
            logger.error(f"Failed to store session {session_id}: {e}")
            raise

    def get_session(self, session_id: str) -> dict:
        """Get session data"""
        try:
            data = self.redis_client.get(f"session:{session_id}")
            if data:
                logger.info(f"Retrieved session {session_id}")
                return json.loads(data)
            logger.warning(f"Session {session_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise

    # Order status management
    def update_order_status(self, order_id: str, status: str):
        """Update order status and notify subscribers"""
        try:
            self.redis_client.set(f"order:{order_id}:status", status)
            self.publish_event("order_status_changed", {
                "order_id": order_id,
                "status": status
            })
            logger.info(f"Updated status for order {order_id} to {status}")
        except Exception as e:
            logger.error(f"Failed to update status for order {order_id}: {e}")
            raise

    def get_order_status(self, order_id: str) -> str:
        """Get order status"""
        try:
            status = self.redis_client.get(f"order:{order_id}:status")
            logger.info(f"Retrieved status for order {order_id}")
            return status
        except Exception as e:
            logger.error(f"Failed to get status for order {order_id}: {e}")
            raise

    # Pub/Sub functionality
    def publish_event(self, channel: str, message: dict):
        """Publish event to channel"""
        try:
            self.redis_client.publish(channel, json.dumps(message))
            logger.info(f"Published message to channel {channel}")
        except Exception as e:
            logger.error(f"Failed to publish message to channel {channel}: {e}")
            raise

    def subscribe_to_channel(self, channel: str):
        """Subscribe to channel"""
        try:
            self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel {channel}")
        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
            raise

    def get_message(self):
        """Get message from subscribed channels"""
        try:
            message = self.pubsub.get_message()
            if message and message['type'] == 'message':
                logger.info(f"Received message from channel {message['channel']}")
            return message
        except Exception as e:
            logger.error(f"Failed to get message: {e}")
            raise

    # Cache management
    def cache_data(self, key: str, data: dict, ttl: int = 300):
        """Cache data with TTL"""
        try:
            self.redis_client.setex(f"cache:{key}", ttl, json.dumps(data))
            logger.info(f"Cached data for key {key} with TTL {ttl}")
        except Exception as e:
            logger.error(f"Failed to cache data for key {key}: {e}")
            raise

    def get_cached_data(self, key: str) -> dict:
        """Get cached data"""
        try:
            data = self.redis_client.get(f"cache:{key}")
            if data:
                logger.info(f"Retrieved cached data for key {key}")
                return json.loads(data)
            logger.warning(f"No cached data found for key {key}")
            return None
        except Exception as e:
            logger.error(f"Failed to get cached data for key {key}: {e}")
            raise

    def invalidate_cache(self, key: str):
        """Invalidate cached data"""
        try:
            self.redis_client.delete(f"cache:{key}")
            logger.info(f"Invalidated cache for key {key}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache for key {key}: {e}")
            raise 