-- ============================================
-- AIshield.cz — Migration 008: Multi-gateway support
-- Adds support for Stripe and Comgate payment gateways.
-- Changes gopay_payment_id from BIGINT to TEXT to support
-- string-based IDs (Stripe cs_..., Comgate transId).
-- Adds payment_gateway column.
-- ============================================

-- 1. Alter gopay_payment_id from BIGINT to TEXT
ALTER TABLE orders ALTER COLUMN gopay_payment_id TYPE TEXT USING gopay_payment_id::TEXT;

-- 2. Add payment_gateway column (default: gopay for backward compatibility)
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_gateway TEXT DEFAULT 'gopay';

-- 3. Update existing orders to have payment_gateway = 'gopay'
UPDATE orders SET payment_gateway = 'gopay' WHERE payment_gateway IS NULL;

-- 4. Drop old index and create new one for TEXT column
DROP INDEX IF EXISTS idx_orders_gopay;
CREATE INDEX IF NOT EXISTS idx_orders_payment_id ON orders(gopay_payment_id);
CREATE INDEX IF NOT EXISTS idx_orders_gateway ON orders(payment_gateway);

-- 5. Also update subscriptions table if gopay_parent_payment_id is BIGINT
ALTER TABLE subscriptions ALTER COLUMN gopay_parent_payment_id TYPE TEXT USING gopay_parent_payment_id::TEXT;
