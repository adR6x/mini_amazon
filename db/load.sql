INSERT INTO Categories (category_id, category_name) VALUES
(1, 'Ice Cream'),
(2, 'Beverages'),
(3, 'Luxury Items')
ON CONFLICT (category_id) DO NOTHING;

\COPY Users(user_id, email, password_hash, full_name, address, balance, created_at, updated_at) FROM 'Users.csv' WITH DELIMITER ',' NULL '' CSV HEADER;
-- since user_id is auto-generated, adjust the sequence counter
SELECT pg_catalog.setval('public.users_user_id_seq',
                         (SELECT COALESCE(MAX(user_id), 1) FROM Users),
                         false);

\COPY Products(product_id, seller_id, category_id, short_name, description, image_url, price, created_at, updated_at) FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV HEADER;
SELECT pg_catalog.setval('public.products_product_id_seq',
                         (SELECT COALESCE(MAX(product_id), 1) FROM Products),
                         false);

\COPY Inventory(inventory_id, seller_id, product_id, quantity_available, price, created_at, updated_at) FROM 'Inventory.csv' WITH DELIMITER ',' NULL '' CSV HEADER;
SELECT pg_catalog.setval('public.inventory_inventory_id_seq',
                         (SELECT COALESCE(MAX(inventory_id), 1) FROM Inventory),
                         false);
