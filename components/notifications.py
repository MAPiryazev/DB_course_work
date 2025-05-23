import streamlit
import json
import threading
import time
from services.redis_service import RedisService

redis_service = RedisService()

def init_notifications():
    """Initialize notifications in session state"""
    if "notifications" not in streamlit.session_state:
        streamlit.session_state.notifications = []

def add_notification(message: str, type: str = "info"):
    """Add a notification to the session state"""
    if "notifications" not in streamlit.session_state:
        streamlit.session_state.notifications = []
    
    # Add new notification
    streamlit.session_state.notifications.append({
        "message": message,
        "type": type,
        "timestamp": time.time()
    })
    
    # Keep only last 5 notifications
    if len(streamlit.session_state.notifications) > 5:
        streamlit.session_state.notifications = streamlit.session_state.notifications[-5:]

def notification_listener():
    """Listen for notifications from Redis PubSub"""
    try:
        while True:
            message = redis_service.get_message()
            if message and message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    if data.get('type') == 'order_status_changed':
                        add_notification(
                            f"Статус заказа {data['order_id']} изменен на {data['status']}",
                            "success"
                        )
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error in notification listener: {e}")
        # Try to reconnect
        try:
            redis_service.close_pubsub()
            redis_service.pubsub = redis_service.redis_client.pubsub()
            redis_service.pubsub.subscribe("order_status_changed")
        except Exception as reconnect_error:
            print(f"Failed to reconnect: {reconnect_error}")

def start_notification_listener():
    """Start notification listener in a separate thread"""
    if "notification_thread" not in streamlit.session_state:
        streamlit.session_state.notification_thread = threading.Thread(
            target=notification_listener,
            daemon=True
        )
        streamlit.session_state.notification_thread.start()

def show_notifications():
    """Display notifications in the UI"""
    if "notifications" in streamlit.session_state:
        current_time = time.time()
        # Filter out old notifications (older than 10 seconds)
        streamlit.session_state.notifications = [
            n for n in streamlit.session_state.notifications
            if current_time - n["timestamp"] < 10
        ]
        
        # Show notifications
        for notification in streamlit.session_state.notifications:
            if notification["type"] == "success":
                streamlit.success(notification["message"])
            elif notification["type"] == "error":
                streamlit.error(notification["message"])
            else:
                streamlit.info(notification["message"]) 