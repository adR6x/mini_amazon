\COPY Users FROM 'Users.csv' WITH DELIMITER ',' NULL '' CSV
-- since id is auto-generated; we need the next command to adjust the counter
-- for auto-generation so next INSERT will not clash with ids loaded above:
SELECT pg_catalog.setval('public.users_id_seq',
                         (SELECT MAX(id)+1 FROM Users),
                         false);

\COPY Products FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.products_id_seq',
                         (SELECT MAX(id)+1 FROM Products),
                         false);

\COPY Purchases FROM 'Purchases.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.purchases_id_seq',
                         (SELECT MAX(id)+1 FROM Purchases),
                         false);

\COPY Wishes FROM 'Wishes.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.purchases_id_seq',
                         (SELECT MAX(id)+1 FROM Wishes),
                         false);
--\COPY Orders FROM 'Orders.csv' WITH DELIMITER ',' NULL '' CSV
--SELECT pg_catalog.setval('public.orders_order_id_seq',
--                         (SELECT MAX(order_id)+1 FROM Orders),
--                         false);

--\COPY Order_Items FROM 'Order_Items.csv' WITH DELIMITER ',' NULL '' CSV
--SELECT pg_catalog.setval('public.order_items_order_item_id_seq',
--                         (SELECT MAX(order_item_id)+1 FROM Order_Items),
--                         false);
