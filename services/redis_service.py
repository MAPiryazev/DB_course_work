import redis
import json
from datetime import timedelta, datetime, timezone
from settings import REDIS_CONFIG
import logging
from repositories import products

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
            
            # Инициализация PubSub
            self.pubsub = self.redis_client.pubsub()
            try:
                logger.info("Attempting to subscribe to order_status_changed channel")
                self.pubsub.subscribe("order_status_changed")
                logger.info("Successfully subscribed to order_status_changed channel")
            except Exception as e:
                logger.error(f"Failed to subscribe to order_status_changed: {e}")
                # Не прерываем выполнение, так как это не критическая ошибка
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

    # Product caching
    def cache_products(self, products_data: list, ttl: int = 3600):
        """Cache products list with TTL"""
        try:
            # Store products as a hash for efficient updates
            for product in products_data:
                # Store basic product info (name and id)
                self.redis_client.hset(
                    f"product:{product['product_id']}",
                    mapping={
                        'product_id': product['product_id'],
                        'name': product['name']
                    }
                )
                self.redis_client.expire(f"product:{product['product_id']}", ttl)
            
            # Store product IDs list for quick access
            product_ids = [str(p['product_id']) for p in products_data]
            self.redis_client.sadd("products:all", *product_ids)
            self.redis_client.expire("products:all", ttl)
            
            logger.info(f"Cached {len(products_data)} products")
        except Exception as e:
            logger.error(f"Failed to cache products: {e}")
            raise

    def get_cached_products(self) -> list:
        """Get all cached products"""
        try:
            # Get all product IDs
            product_ids = self.redis_client.smembers("products:all")
            if not product_ids:
                return []
            
            # Get all products data
            products = []
            for pid in product_ids:
                product_data = self.redis_client.hgetall(f"product:{pid}")
                if product_data and 'name' in product_data and 'product_id' in product_data:
                    products.append({
                        'name': product_data['name'],
                        'product_id': int(product_data['product_id'])
                    })
            
            return products
        except Exception as e:
            logger.error(f"Failed to get cached products: {e}")
            raise

    # Cart caching
    def cache_cart(self, user_id: str, cart_data: list, ttl: int = 1800):
        """Cache user's cart data"""
        try:
            cart_key = f"cart:{user_id}"
            # Store cart items as a hash
            for item in cart_data:
                # Convert datetime to string
                if 'added_date' in item:
                    item['added_date'] = item['added_date'].isoformat()
                self.redis_client.hset(
                    cart_key,
                    str(item['product_id']),
                    json.dumps(item)
                )
            self.redis_client.expire(cart_key, ttl)
            logger.info(f"Cached cart for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to cache cart: {e}")
            raise

    def get_cached_cart(self, user_id: str) -> list:
        """Get user's cached cart"""
        try:
            cart_key = f"cart:{user_id}"
            cart_data = self.redis_client.hgetall(cart_key)
            if not cart_data:
                return []
            
            result = []
            for item in cart_data.values():
                item_data = json.loads(item)
                # Convert string back to datetime if needed
                if 'added_date' in item_data:
                    try:
                        item_data['added_date'] = datetime.fromisoformat(item_data['added_date'])
                    except (ValueError, TypeError):
                        pass
                result.append(item_data)
            return result
        except Exception as e:
            logger.error(f"Failed to get cached cart: {e}")
            raise

    # Order status management with PubSub
    def update_order_status(self, order_id: str, status: str, user_id: str = None):
        """Update order status and notify subscribers"""
        try:
            logger.info(f"Updating order {order_id} status to {status}")
            # Store order status
            self.redis_client.set(f"order:{order_id}:status", status)
            
            # Publish status change event
            event_data = {
                "order_id": order_id,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            if user_id:
                event_data["user_id"] = user_id
            
            logger.debug(f"Publishing event with data: {event_data}")
            self.publish_event("order_status_changed", event_data)
            
            # If user_id provided, store in user's orders
            if user_id:
                self.redis_client.sadd(f"user:{user_id}:orders", order_id)
            
            logger.info(f"Successfully updated status for order {order_id} to {status}")
        except Exception as e:
            logger.error(f"Failed to update order status: {e}")
            raise

    def get_order_status(self, order_id: str) -> str:
        """Get order status"""
        try:
            return self.redis_client.get(f"order:{order_id}:status")
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            raise

    def get_user_orders(self, user_id: str) -> list:
        """Get all orders for a user"""
        try:
            order_ids = self.redis_client.smembers(f"user:{user_id}:orders")
            orders = []
            for order_id in order_ids:
                status = self.get_order_status(order_id.decode('utf-8'))
                if status:
                    orders.append({
                        "order_id": order_id.decode('utf-8'),
                        "status": status.decode('utf-8')
                    })
            return orders
        except Exception as e:
            logger.error(f"Failed to get user orders: {e}")
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
            if message:
                logger.debug(f"Received message: {message}")
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        logger.info(f"Received message from channel {message['channel']}: {data}")
                        return data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message data: {e}")
                        return None
            return None
        except Exception as e:
            logger.error(f"Failed to get message: {e}")
            return None

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

    def close_pubsub(self):
        """Safely close PubSub connection"""
        try:
            if hasattr(self, 'pubsub') and self.pubsub:
                logger.info("Attempting to close PubSub connection")
                self.pubsub.unsubscribe()
                self.pubsub.close()
                logger.info("PubSub connection closed successfully")
        except Exception as e:
            logger.error(f"Error while closing PubSub connection: {e}")

    def __del__(self):
        """Destructor to ensure connections are closed"""
        logger.info("Cleaning up Redis connections")
        self.close_pubsub()
        if hasattr(self, 'redis_client'):
            try:
                self.redis_client.close()
                logger.info("Redis client connection closed")
            except Exception as e:
                logger.error(f"Error while closing Redis connection: {e}")

    def cleanup_user_sessions(self, user_id: str) -> None:
        """
        Clean up all sessions for a specific user
        :param user_id: The user ID to clean up sessions for
        """
        try:
            # Get all session keys
            session_keys = self.redis_client.keys("session:*")
            
            for session_key in session_keys:
                # Get session data
                session_data = self.redis_client.hgetall(session_key)
                
                # If session belongs to this user, delete it
                if session_data.get('user_id') == user_id:
                    self.redis_client.delete(session_key)
            
            # Also delete user's token
            self.delete_token(user_id)
            
            # Close PubSub connection
            self.close_pubsub()
            
            print(f"Cleaned up all sessions for user {user_id}")
        except Exception as e:
            print(f"Error cleaning up user sessions: {e}")
            raise 