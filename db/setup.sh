#!/bin/bash

mypath=`realpath "$0"`
mybase=`dirname "$mypath"`
cd $mybase

datadir="${1:-data/}"
if [ ! -d $datadir ] ; then
    echo "$datadir does not exist under $mybase"
    exit 1
fi

source ../.flaskenv
dbname=$DB_NAME

export PGPASSWORD=$DB_PASSWORD

if [[ -n `psql -U $DB_USER -h $DB_HOST -p $DB_PORT -lqt | cut -d \| -f 1 | grep -w "$dbname"` ]]; then
    dropdb -U $DB_USER -h $DB_HOST -p $DB_PORT $dbname
fi
createdb -U $DB_USER -h $DB_HOST -p $DB_PORT $dbname

psql -U $DB_USER -h $DB_HOST -p $DB_PORT -af create.sql $dbname
cd $datadir
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -af $mybase/load.sql $dbname

# Convert Purchases to Orders and Order_Items
echo "Converting purchases to orders..."
psql -U $DB_USER -h $DB_HOST -p $DB_PORT $dbname << EOF
-- Create temporary table for purchases
CREATE TEMP TABLE temp_purchases (
    id INT,
    user_id INT,
    product_id INT,
    time_purchased TIMESTAMP
);

-- Load purchases data
\COPY temp_purchases FROM 'Purchases.csv' WITH DELIMITER ',' NULL '' CSV;

-- Insert into Orders (one order per purchase)
INSERT INTO Orders (buyer_id, total_amount, order_date, fulfillment_status)
SELECT 
    p.user_id,
    pr.price as total_amount,
    p.time_purchased as order_date,
    'fulfilled' as fulfillment_status
FROM temp_purchases p
JOIN Products pr ON p.product_id = pr.product_id;

-- Insert into Order_Items
INSERT INTO Order_Items (order_id, product_id, seller_id, quantity, unit_price, fulfillment_status)
SELECT 
    o.order_id,
    p.product_id,
    pr.seller_id,
    1 as quantity,
    pr.price as unit_price,
    'fulfilled' as fulfillment_status
FROM temp_purchases p
JOIN Products pr ON p.product_id = pr.product_id
JOIN Orders o ON o.buyer_id = p.user_id AND o.order_date = p.time_purchased;

-- Clean up
DROP TABLE temp_purchases;

-- Verify the data
SELECT COUNT(*) as total_orders FROM Orders WHERE buyer_id = 100;
SELECT COUNT(*) as total_order_items FROM Order_Items oi 
JOIN Orders o ON oi.order_id = o.order_id 
WHERE o.buyer_id = 100;
EOF