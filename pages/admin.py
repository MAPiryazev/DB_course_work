import pandas as pd
import streamlit as st
import time

import services.user
import services.products
import services.cart

def show_admin_page():
    st.title("Панель администратора")

    # Отображение всех товаров
    st.header("Все товары")
    try:
        products_df = services.products.fetch_product_names_and_ids()
        if not products_df.empty:
            products_df['stock_quantity'] = products_df['product_id'].apply(
                lambda pid: services.products.check_product_stock(pid)
            )
        st.dataframe(products_df)
    except Exception as e:
        st.error(f"Ошибка при получении товаров: {e}")

    # Добавление нового товара
    st.header("Добавить новый товар")
    with st.form("add_product_form"):
        name = st.text_input("Название товара")
        price = st.number_input("Цена", min_value=0.0, step=0.01)
        description = st.text_area("Описание")
        warranty_period = st.number_input("Гарантийный срок (месяцы)", min_value=0, step=1)
        manufacturer_id = st.number_input("ID производителя", min_value=0, step=1)
        stock_quantity = st.number_input("Количество на складе", min_value=0, step=1)
        submitted = st.form_submit_button("Добавить товар")

        if submitted:
            try:
                product_id = services.products.add_new_product(
                    name, price, description, warranty_period, manufacturer_id, stock_quantity
                )
                st.success(f"Товар успешно добавлен с ID: {product_id}")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка при добавлении товара: {e}")

    # Обновление количества на складе
    st.header("Обновить количество товара на складе")
    with st.form("update_stock_form"):
        product_id = st.number_input("ID товара", min_value=0, step=1)
        new_stock_quantity = st.number_input("Новое количество на складе", min_value=0, step=1)
        update_submitted = st.form_submit_button("Обновить количество")

        if update_submitted:
            try:
                current_stock = services.products.check_product_stock(product_id)
                services.products.reduce_product_stock(product_id, current_stock - new_stock_quantity)
                st.success("Количество успешно обновлено.")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка при обновлении количества: {e}")