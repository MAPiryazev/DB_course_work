import pandas as pd
import streamlit as st
import time

import services.user
import services.products
import services.cart
import services.orders
from services.redis_service import RedisService

# Инициализация Redis сервиса
redis_service = RedisService()

def show_cart_page():
    st.title("Корзина")

    # Получение данных о пользователе из session_state
    user_data = st.session_state.get("user", {"email": "нет данных", "balance": 0.0})
    email = user_data.get("email", "нет данных").iloc[0]

    # Получение актуального баланса пользователя
    user_balance = services.user.get_user_balance(email)

    # Отображение текущего баланса пользователя
    st.write(f"**Ваш баланс:** {user_balance:.2f} $")

    # Получение ID пользователя и проверка авторизации
    user_info = services.user.get_user(email)
    if user_info.empty:
        st.error("Пользователь не найден. Авторизуйтесь, чтобы просмотреть корзину.")
        return

    user_id = int(user_info['user_id'].iloc[0])

    # Загрузка содержимого корзины
    try:
        cart_items = services.cart.fetch_user_cart(user_id)

        if cart_items.empty:
            st.warning("Ваша корзина пуста.")
        else:
            st.write("### Содержимое вашей корзины")

            total_price = 0  # Общая сумма заказа
            quantity_changes = {}  # Изменения количества товаров
            all_quantities_zero = True  # Флаг для проверки количества товаров

            # Отображаем товары с возможностью изменения количества
            for index, item in cart_items.iterrows():
                # Поле для изменения количества
                new_quantity = st.number_input(
                    f"{item['product_name']} (Количество)",
                    min_value=0,  # Позволяем установить 0 для удаления из корзины
                    value=item['quantity'],
                    step=1,
                    key=f"quantity_{item['product_id']}"
                )
                # Вычисление стоимости для текущего товара
                item_total = new_quantity * item['price']
                st.write(f"Цена: {item_total:.2f} $")

                # Обновление общей суммы
                total_price += item_total

                # Сохраняем изменения количества
                if new_quantity != item['quantity']:
                    quantity_changes[item['product_id']] = new_quantity

                # Проверяем, есть ли хоть один товар с количеством больше 0
                if new_quantity > 0:
                    all_quantities_zero = False

            st.write(f"**Общая сумма:** {total_price:.2f} $")

            # Кнопка оформления заказа
            confirm_disabled = all_quantities_zero  # Блокируем кнопку, если все количества равны 0
            if st.button("Подтвердить заказ", disabled=confirm_disabled):
                if user_balance >= total_price:
                    try:
                        # Применяем изменения в корзине и вычитаем со склада
                        for product_id, new_quantity in quantity_changes.items():
                            services.cart.update_cart_item(user_id, product_id, new_quantity)
                            services.products.reduce_product_stock(product_id, new_quantity)

                        # Создаем новый заказ
                        order_id = services.orders.create_order(user_id, 0)  # total_amount больше не используется
                        
                        # Отправляем уведомление о новом заказе
                        redis_service.update_order_status(
                            str(order_id),
                            "В обработке",
                            str(user_id)
                        )

                        # Очищаем корзину
                        services.cart.clear_cart(user_id)

                        # Обновляем баланс пользователя
                        new_balance = user_balance - total_price
                        services.user.set_user_balance(email, new_balance)
                        st.session_state['user']['balance'] = new_balance

                        st.success("Заказ успешно оформлен!")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка при оформлении заказа: {e}")
                else:
                    st.error("Недостаточно средств на балансе.")

            # Кнопка очистки корзины
            if st.button("Очистить корзину"):
                try:
                    # Очищаем корзину
                    services.cart.clear_cart(user_id)
                    st.success("Корзина успешно очищена!")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка при очистке корзины: {e}")

    except Exception as e:
        st.error(f"Ошибка при загрузке корзины: {e}")
