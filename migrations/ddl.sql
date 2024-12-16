-- Тип для ролей пользователей
CREATE TYPE user_role AS ENUM ('user', 'admin');

-- Таблица пользователей (users)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    password TEXT NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    balance FLOAT DEFAULT 0,
    role user_role NOT NULL DEFAULT 'user'
);

-- Таблица производителей (manufacturers)
CREATE TABLE manufacturers (
    manufacturer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    country VARCHAR(100) NOT NULL
);

-- Таблица продуктов (products)
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price FLOAT NOT NULL,
    description TEXT,
    warranty_period INT, -- Гарантийный период в месяцах
    manufacturer_id INT REFERENCES manufacturers(manufacturer_id) ON DELETE SET NULL,
    stock_quantity INT DEFAULT 0 CHECK (stock_quantity >= 0) -- Количество на складе
);

-- Таблица корзины (carts)
CREATE TABLE carts (
    cart_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    quantity INT NOT NULL CHECK (quantity > 0), -- Количество добавленного товара
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Дата добавления в корзину
);

-- Таблица заказов (orders)
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Дата оформления заказа
    status VARCHAR(50) NOT NULL -- Статус заказа
);

-- Таблица отзывов (reviews)
CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id) ON DELETE CASCADE,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    rating INT CHECK (rating >= 1 AND rating <= 5), -- Оценка (от 1 до 5)
    review_text TEXT, -- Текст отзыва
    review_date DATE NOT NULL -- Дата отзыва
);
