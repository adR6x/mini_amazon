DELETE FROM Order_Items;
DELETE FROM Orders;
DELETE FROM Cart_Items;
DELETE FROM Carts;
DELETE FROM Product_Reviews;
DELETE FROM Seller_Reviews;
DELETE FROM Inventory;
DELETE FROM Products;
DELETE FROM Categories;
DELETE FROM Users;

\COPY Users FROM 'Users.csv' WITH DELIMITER ',' NULL '' CSV
-- since id is auto-generated; we need the next command to adjust the counter
-- for auto-generation so next INSERT will not clash with ids loaded above:
SELECT pg_catalog.setval('public.users_id_seq',
                         (SELECT MAX(id)+1 FROM Users),
                         false);

-- Load categories first (satisfy FK constraints)
\COPY Categories FROM 'Categories.csv' WITH DELIMITER ',' NULL '' CSV;

-- Load products next
\COPY Products FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV;

\COPY Product_Reviews FROM 'ProductReviews.csv' WITH DELIMITER ',' NULL '' CSV;

\COPY Seller_Reviews FROM 'SellerReviews.csv' WITH DELIMITER ',' NULL '' CSV;

\COPY Inventory FROM 'Inventory.csv' WITH DELIMITER ',' NULL '' CSV;

\COPY Orders FROM 'Orders.csv' WITH DELIMITER ',' NULL '' CSV;
-- Reset Orders sequence
SELECT pg_catalog.setval('public.orders_order_id_seq',
                         (SELECT MAX(order_id)+1 FROM Orders),
                         false);

\COPY Order_Items FROM 'Order_Items.csv' WITH DELIMITER ',' NULL '' CSV;
-- Reset Order_Items sequence
SELECT pg_catalog.setval('public.order_items_order_item_id_seq',
                         (SELECT MAX(order_item_id)+1 FROM Order_Items),
                         false);

-- No need to reset identity sequence manually if using GENERATED AS IDENTITY


-- \COPY Products FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV
-- SELECT pg_catalog.setval('public.products_id_seq',
--                          (SELECT MAX(product_id)+1 FROM Products),
--                          false);

-- \COPY Purchases FROM 'Purchases.csv' WITH DELIMITER ',' NULL '' CSV
-- SELECT pg_catalog.setval('public.purchases_id_seq',
--                          (SELECT MAX(id)+1 FROM Purchases),
--                          false);

-- \COPY Wishes FROM 'Wishes.csv' WITH DELIMITER ',' NULL '' CSV
-- SELECT pg_catalog.setval('public.wishes_id_seq',
--                          (SELECT MAX(id)+1 FROM Wishes),
--                          false);
