import streamlit as st
from services.notifications import get_user_notifications, mark_notification_as_read, get_unread_notifications_count
import time

def show_notifications():
    st.title("Уведомления")
    
    if 'user_id' not in st.session_state:
        st.warning("Пожалуйста, войдите в систему для просмотра уведомлений")
        return
    
    user_id = st.session_state.user_id
    
    # Получаем уведомления
    notifications = get_user_notifications(user_id)
    
    if not notifications:
        st.info("У вас пока нет уведомлений")
        return
    
    # Отображаем уведомления
    for notification in notifications:
        with st.container():
            col1, col2 = st.columns([0.9, 0.1])
            
            with col1:
                # Определяем цвет в зависимости от типа уведомления
                if notification["type"] == "success":
                    st.success(notification["message"])
                elif notification["type"] == "warning":
                    st.warning(notification["message"])
                elif notification["type"] == "error":
                    st.error(notification["message"])
                else:
                    st.info(notification["message"])
                
                # Показываем время создания
                st.caption(f"Создано: {notification['created_at']}")
            
            with col2:
                if not notification["read"]:
                    if st.button("✓", key=f"read_{notification['id']}"):
                        mark_notification_as_read(user_id, notification["id"])
                        st.rerun()

def notification_bell():
    """Компонент колокольчика с количеством непрочитанных уведомлений"""
    if 'user_id' in st.session_state:
        unread_count = get_unread_notifications_count(st.session_state.user_id)
        if unread_count > 0:
            st.sidebar.markdown(f"🔔 {unread_count}")
            if st.sidebar.button("Показать уведомления"):
                st.switch_page("pages/notifications.py")

# Автоматическое обновление страницы каждые 30 секунд
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 30:
    st.session_state.last_refresh = time.time()
    st.rerun()

show_notifications() 