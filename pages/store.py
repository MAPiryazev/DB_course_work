import pandas as pd
import streamlit as st
import time
from thefuzz import fuzz, process
import services.user
import services.products


def show_store_page():
    st.title("Магазин")

    user_data = st.session_state.get("user", {"email": "нет данных", "balance": 0.0})
    user_id = st.session_state.get('user', {}).get('user_id')
    email = user_data['email']
    email = email.iloc[0] if isinstance(email, pd.Series) else email

    # Строка поиска товаров
    st.subheader("Поиск товаров")
    search_query = st.text_input("Введите название товара:", "")

    # Получение списка товаров
    products_df = services.products.fetch_product_names_and_ids()

    # Фильтрация товаров с учетом поиска
    if search_query.strip():
        # Использование thefuzz для поиска похожих товаров
        product_names = products_df['name'].tolist()
        matches = process.extract(search_query, product_names, scorer=fuzz.partial_ratio, limit=10)

        # Список совпадений
        matched_product_names = [match[0] for match in matches if match[1] > 50]  # threshold 50 - можно настроить
        if matched_product_names:
            filtered_products = products_df[products_df['name'].isin(matched_product_names)]
        else:
            filtered_products = pd.DataFrame()  # Если нет совпадений, создаем пустой DataFrame
    else:
        filtered_products = pd.DataFrame()  # Пустой запрос - пустой результат

    # Если результаты найдены, показываем товары
    if not filtered_products.empty:
        st.write("Результаты поиска:")
        selected_product_name = st.selectbox(
            "Выберите товар из списка:",
            filtered_products['name']
        )

        # Получение информации о выбранном товаре
        if selected_product_name:
            selected_product_id = int(
                filtered_products[filtered_products['name'] == selected_product_name]['product_id'].iloc[0])

            try:
                product_details = services.products.fetch_product_details_by_id(selected_product_id)

                # Отображение полной информации о товаре
                if product_details:
                    st.subheader(f"Информация о товаре: {selected_product_name}")
                    st.write(f"**Цена:** {product_details['price']} руб.")
                    st.write(f"**Описание:** {product_details['description']}")
                    st.write(f"**Гарантия:** {product_details['warranty_period']} мес.")
                    st.write(f"**В наличии:** {product_details['stock_quantity']} шт.")
                    st.write(
                        f"**Производитель:** {product_details['manufacturer_name']} ({product_details['manufacturer_country']})")

                    # Выбор количества
                    quantity = st.number_input("Количество", min_value=0, value=1)


                    # Кнопка добавления в корзину
                    if st.button("Добавить в корзину"):
                        try:
                            # Проверка количества доступного товара
                            available_stock = services.products.check_product_stock(selected_product_id)
                            if quantity > available_stock:
                                st.error(
                                    f"Указанное количество товаров ({quantity}) превышает доступное на складе ({available_stock} шт.). Пожалуйста, укажите корректное количество.")
                            elif quantity == 0:
                                st.error("выберите число больше 0")
                            else:

                                # Добавляем в корзину
                                user_id_series = st.session_state.get('user', {}).get('user_id')
                                user_id = user_id_series.iloc[0] if isinstance(user_id_series,
                                                                           pd.Series) else user_id_series
                                services.products.add_product_to_user_cart(int(user_id), selected_product_id, quantity)
                                # services.products.reduce_product_stock(selected_product_id, quantity)
                                st.success(f"Товар '{selected_product_name}' добавлен в корзину в количестве {quantity} шт.")
                        except Exception as e:
                            st.error(f"Ошибка при добавлении товара в корзину: {e}")

                    # Отзывы
                    st.subheader("Отзывы")
                    reviews = product_details.get("reviews", [])
                    if reviews:
                        for review in reviews:
                            st.write(f"**Оценка:** {review['rating']}/5")
                            st.write(f"**Отзыв:** {review['review_text']}")
                            st.write(f"**Дата:** {review['review_date']}")
                            st.write("---")
                    else:
                        st.write("Нет отзывов на этот товар.")
                else:
                    st.error("Информация о выбранном товаре не найдена.")
            except Exception as e:
                st.error(f"Не удалось загрузить информацию о товаре: {e}")
    else:
        st.write("Нет товаров, соответствующих вашему запросу.")