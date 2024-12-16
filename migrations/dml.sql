-- Заполнение таблицы users (объединенной с admins)
INSERT INTO
    users (password, email, balance, role)
VALUES
    ('password123', 'ivanov@gmail.com', 150.0, 'admin'),   -- Админ
    ('qwerty456', 'petrov@gmail.com', 200.0, 'user'),
    ('abcde789', 'sidorov@yahoo.com', 120.0, 'user'),
    ('zxcvbn123', 'alex@mail.ru', 90.0, 'user');

-- Заполнение таблицы manufacturers
INSERT INTO
    manufacturers (name, country)
VALUES
    ('Continental', 'Germany'),
    ('Shimano', 'Japan'),
    ('Brooks', 'United Kingdom'),
    ('Avid', 'USA');

-- Заполнение таблицы products (объединенной с products_info)
INSERT INTO
    products (name, price, description, warranty_period, manufacturer_id)
VALUES
    ('Шина для велосипеда 26x2.1', 30.0, 'Шина для горного велосипеда, подходит для любых условий.', 12, 1),
    ('Цепь велосипедная Shimano HG54', 20.0, 'Цепь 10 скоростей, подходит для MTB и шоссейных велосипедов.', 6, 2),
    ('Велосипедное седло Brooks B17', 80.0, 'Классическое кожаное седло для комфортной езды.', 24, 3),
    ('Тормозные колодки Avid BB5', 15.0, 'Надежные тормозные колодки для дисковых тормозов.', 6, 4),
    ('Педали Shimano SPD PD-M520', 50.0, 'Педали с двойным креплением для горных и шоссейных велосипедов.', 12, 2);

-- Заполнение таблицы orders
INSERT INTO
    orders (user_id, order_date, status)
VALUES
    (1, '2024-12-01 12:30:00', 'Pending'),
    (2, '2024-12-02 14:00:00', 'Completed'),
    (3, '2024-12-03 09:15:00', 'Shipped');

-- Заполнение таблицы reviews
INSERT INTO
    reviews (product_id, user_id, rating, review_text, review_date)
VALUES
    (1, 1, 5, 'Отличная шина, подходит для всех типов дорог!', '2024-12-02'),
    (2, 2, 4, 'Цепь хорошо работает, но немного шумновата.', '2024-12-03'),
    (3, 3, 5, 'Седло очень удобное, рекомендую для дальних поездок.', '2024-12-04'),
    (4, 1, 3, 'Тормозные колодки быстро изнашиваются.', '2024-12-05'),
    (5, 4, 5, 'Педали отличные, легко устанавливаются.', '2024-12-05');
