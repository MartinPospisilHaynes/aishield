-- ══════════════════════════════════════════════════════════════
-- MIGRACE 005: Subscriptions (opakované platby) + refundace
-- Datum: 2026-02-09
-- ══════════════════════════════════════════════════════════════

-- 1. Tabulka subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    plan TEXT NOT NULL,
    gopay_parent_payment_id BIGINT NOT NULL,
    amount INTEGER NOT NULL,
    cycle TEXT NOT NULL DEFAULT 'ON_DEMAND',
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, active, cancelled, expired, failed
    order_number TEXT,
    total_charged INTEGER DEFAULT 0,
    activated_at TIMESTAMPTZ,
    last_charged_at TIMESTAMPTZ,
    next_charge_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index pro rychlé lookup
CREATE INDEX IF NOT EXISTS idx_subscriptions_email ON subscriptions(email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_gopay ON subscriptions(gopay_parent_payment_id);

-- RLS
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all_subscriptions" ON subscriptions
    FOR ALL USING (auth.role() = 'service_role');

-- 2. Rozšíření tabulky orders o nové sloupce
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_type TEXT DEFAULT 'one_time';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS subscription_id UUID REFERENCES subscriptions(id);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMPTZ;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_amount INTEGER;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_reason TEXT;

-- Index pro subscription platby
CREATE INDEX IF NOT EXISTS idx_orders_subscription_id ON orders(subscription_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_type ON orders(order_type);

-- 3. Komentáře
COMMENT ON TABLE subscriptions IS 'GoPay opakované platby (subscriptions) pro SaaS model';
COMMENT ON COLUMN subscriptions.cycle IS 'GoPay recurrence_cycle: ON_DEMAND, MONTH, WEEK, DAY';
COMMENT ON COLUMN subscriptions.status IS 'pending=čeká na platbu, active=běží, cancelled=zrušeno';
COMMENT ON COLUMN orders.order_type IS 'one_time=jednorázová, subscription=první platba, subscription_recurrence=stržení';
