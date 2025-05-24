import pandas as pd
import streamlit as st
import time
import services.user
import services.orders
import logging

logger = logging.getLogger(__name__)

def show_profile_page():
    st.title("Ваш профиль")

    user_data = st.session_state.get("user", {"email": "нет данных", "balance": 0.0})

    email = user_data['email']
    email = email.iloc[0]
    user_balance = services.user.get_user_balance(email)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📧 Почта")
        st.write(f"**{email}**")
    with col2:
        st.markdown("### 💰 Баланс")
        st.write(f"**{user_balance:,.2f} руб.**")

    st.divider()
    if st.button("Обновить данные"):
        st.success("Данные обновлены!")
        time.sleep(0.5)
        st.rerun()

    # Инициализация состояния
    if 'show_balance_input' not in st.session_state:
        st.session_state['show_balance_input'] = False
    if 'new_balance' not in st.session_state:
        st.session_state['new_balance'] = 0.0

    # Кнопка для показа полоски
    if st.button("Пополнить баланс"):
        st.session_state['show_balance_input'] = True

    # Отображение полоски, если флаг активен
    if st.session_state['show_balance_input']:
        new_balance = st.number_input("Введите сумму для пополнения", min_value=0.0, step=0.01)
        if st.button("Подтвердить пополнение"):
            try:
                # Вызов функции для обновления баланса
                services.user.set_user_balance(email, user_balance + new_balance)
                st.success(f"Баланс пополнен на {new_balance:,.2f} руб.")
                time.sleep(0.5)
                st.session_state['show_balance_input'] = False
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка: {e}")

    # Добавляем раздел с заказами
    st.divider()
    st.markdown("### 📦 Мои заказы")
    
    try:
        # Получаем ID пользователя
        user_info = services.user.get_user(email)
        if user_info.empty:
            st.error("Пользователь не найден.")
            return
            
        user_id = int(user_info['user_id'].iloc[0])
        
        # Получаем заказы пользователя
        orders_df = services.orders.get_user_orders(user_id)
        
        if orders_df.empty:
            st.info("У вас пока нет заказов.")
        else:
            # Отображаем заказы
            for index, order in orders_df.iterrows():
                with st.expander(f"Заказ #{order['order_id']} - {order['status']}"):
                    st.write(f"Дата заказа: {order['order_date']}")
                    
                    # Добавляем цветовую индикацию статуса с учетом английских названий
                    status_colors = {
                        "Pending": "🟡 В обработке",
                        "Processing": "🟡 В обработке",
                        "Confirmed": "🔵 Подтвержден",
                        "Shipped": "🟢 Отправлен",
                        "Delivered": "✅ Доставлен",
                        "Cancelled": "❌ Отменен"
                    }
                    status_display = status_colors.get(order['status'], f"⚪ {order['status']}")
                    st.write(f"Статус: {status_display}")
                    
    except Exception as e:
        logger.error(f"Error loading orders: {e}")
        st.error("Произошла ошибка при загрузке заказов. Пожалуйста, попробуйте позже.")