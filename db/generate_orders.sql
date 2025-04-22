-- First, let's create some orders
INSERT INTO Orders (order_id, buyer_id, total_amount, order_date, fulfillment_status, created_at)
VALUES 
    (DEFAULT, 1, 29.99, '2024-03-20 10:00:00', 'fulfilled', '2024-03-20 10:00:00'),
    (DEFAULT, 1, 45.49, '2024-03-20 11:00:00', 'pending', '2024-03-20 11:00:00'),
    (DEFAULT, 1, 1199000.0, '2024-03-20 12:00:00', 'partial', '2024-03-20 12:00:00'),
    (DEFAULT, 1, 25.50, '2024-03-20 13:00:00', 'fulfilled', '2024-03-20 13:00:00'),
    (DEFAULT, 1, 44.99, '2024-03-20 14:00:00', 'pending', '2024-03-20 14:00:00'),
    (DEFAULT, 1, 19.99, '2024-03-20 15:00:00', 'fulfilled', '2024-03-20 15:00:00'),
    (DEFAULT, 1, 99.00, '2024-03-20 16:00:00', 'partial', '2024-03-20 16:00:00'),
    (DEFAULT, 1, 1299.99, '2024-03-20 17:00:00', 'pending', '2024-03-20 17:00:00'),
    (DEFAULT, 1, 799.99, '2024-03-20 18:00:00', 'fulfilled', '2024-03-20 18:00:00'),
    (DEFAULT, 1, 14.99, '2024-03-20 19:00:00', 'pending', '2024-03-20 19:00:00'),
    (DEFAULT, 1, 9.99, '2024-03-20 20:00:00', 'fulfilled', '2024-03-20 20:00:00'),
    (DEFAULT, 1, 25.50, '2024-03-20 21:00:00', 'partial', '2024-03-20 21:00:00'),
    (DEFAULT, 1, 1199000.0, '2024-03-20 22:00:00', 'pending', '2024-03-20 22:00:00'),
    (DEFAULT, 1, 19.99, '2024-03-20 23:00:00', 'fulfilled', '2024-03-20 23:00:00'),
    (DEFAULT, 1, 99.00, '2024-03-21 00:00:00', 'pending', '2024-03-21 00:00:00'),
    (DEFAULT, 1, 1299.99, '2024-03-21 01:00:00', 'partial', '2024-03-21 01:00:00');

-- Now let's add order items for each order
INSERT INTO Order_Items (order_item_id, order_id, product_id, seller_id, quantity, unit_price, fulfillment_status, fulfilled_at)
VALUES 
    -- Order 1 (fulfilled)
    (DEFAULT, 1, 2, 0, 1, 19.99, 'fulfilled', '2024-03-20 10:30:00'),
    (DEFAULT, 1, 3, 0, 1, 9.99, 'fulfilled', '2024-03-20 10:30:00'),
    
    -- Order 2 (pending)
    (DEFAULT, 2, 4, 0, 1, 11.49, 'pending', NULL),
    (DEFAULT, 2, 5, 0, 1, 33.99, 'pending', NULL),
    
    -- Order 3 (partial)
    (DEFAULT, 3, 5, 0, 1, 1199000.0, 'fulfilled', '2024-03-20 12:30:00'),
    (DEFAULT, 3, 6, 0, 1, 0.0, 'pending', NULL),
    
    -- Order 4 (fulfilled)
    (DEFAULT, 4, 3, 0, 1, 25.50, 'fulfilled', '2024-03-20 13:30:00'),
    
    -- Order 5 (pending)
    (DEFAULT, 5, 4, 0, 3, 14.99, 'pending', NULL),
    
    -- Order 6 (fulfilled)
    (DEFAULT, 6, 2, 0, 1, 19.99, 'fulfilled', '2024-03-20 15:30:00'),
    
    -- Order 7 (partial)
    (DEFAULT, 7, 6, 0, 1, 99.00, 'fulfilled', '2024-03-20 16:30:00'),
    (DEFAULT, 7, 1, 0, 1, 0.0, 'pending', NULL),
    
    -- Order 8 (pending)
    (DEFAULT, 8, 1, 0, 1, 1299.99, 'pending', NULL),
    
    -- Order 9 (fulfilled)
    (DEFAULT, 9, 0, 0, 1, 799.99, 'fulfilled', '2024-03-20 18:30:00'),
    
    -- Order 10 (pending)
    (DEFAULT, 10, 4, 0, 1, 14.99, 'pending', NULL),
    
    -- Order 11 (fulfilled)
    (DEFAULT, 11, 5, 0, 1, 9.99, 'fulfilled', '2024-03-20 20:30:00'),
    
    -- Order 12 (partial)
    (DEFAULT, 12, 3, 0, 1, 25.50, 'fulfilled', '2024-03-20 21:30:00'),
    (DEFAULT, 12, 2, 0, 1, 0.0, 'pending', NULL),
    
    -- Order 13 (pending)
    (DEFAULT, 13, 5, 0, 1, 1199000.0, 'pending', NULL),
    
    -- Order 14 (fulfilled)
    (DEFAULT, 14, 2, 0, 1, 19.99, 'fulfilled', '2024-03-20 23:30:00'),
    
    -- Order 15 (pending)
    (DEFAULT, 15, 6, 0, 1, 99.00, 'pending', NULL),
    
    -- Order 16 (partial)
    (DEFAULT, 16, 1, 0, 1, 1299.99, 'fulfilled', '2024-03-21 01:30:00'),
    (DEFAULT, 16, 0, 0, 1, 0.0, 'pending', NULL);

-- Update inventory quantities
UPDATE Inventory 
SET quantity_available = quantity_available - 1 
WHERE (product_id, seller_id) IN (
    (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (1, 0), (0, 0)
); 