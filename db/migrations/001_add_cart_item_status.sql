-- Add status and saved_at columns to Cart_Items table
ALTER TABLE Cart_Items 
ADD COLUMN status VARCHAR(20) DEFAULT 'in_cart' CHECK (status IN ('in_cart', 'saved_for_later')),
ADD COLUMN saved_at TIMESTAMP;

-- Update existing records to have status 'in_cart'
UPDATE Cart_Items SET status = 'in_cart' WHERE status IS NULL; 