-- 007_admin_crm.sql
-- CRM workflow management for admin dashboard
-- Idempotent: safe to run multiple times

-- ============================================================
-- 1-7. Add new columns to companies table
-- ============================================================
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'companies' AND column_name = 'workflow_status'
  ) THEN
    ALTER TABLE companies
      ADD COLUMN workflow_status VARCHAR(50) DEFAULT 'new';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'companies' AND column_name = 'payment_status'
  ) THEN
    ALTER TABLE companies
      ADD COLUMN payment_status VARCHAR(50) DEFAULT 'none';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'companies' AND column_name = 'assigned_to'
  ) THEN
    ALTER TABLE companies
      ADD COLUMN assigned_to VARCHAR(255);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'companies' AND column_name = 'priority'
  ) THEN
    ALTER TABLE companies
      ADD COLUMN priority VARCHAR(20) DEFAULT 'normal';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'companies' AND column_name = 'last_contact_at'
  ) THEN
    ALTER TABLE companies
      ADD COLUMN last_contact_at TIMESTAMPTZ;
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'companies' AND column_name = 'next_action'
  ) THEN
    ALTER TABLE companies
      ADD COLUMN next_action TEXT;
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'companies' AND column_name = 'next_action_at'
  ) THEN
    ALTER TABLE companies
      ADD COLUMN next_action_at TIMESTAMPTZ;
  END IF;
END $$;

-- ============================================================
-- 8. Company activities table (timeline / activity log)
-- ============================================================
CREATE TABLE IF NOT EXISTS company_activities (
  id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id    UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  actor         TEXT          NOT NULL,
  activity_type VARCHAR(50)   NOT NULL,
  title         VARCHAR(500),
  description   TEXT,
  metadata      JSONB         DEFAULT '{}',
  created_at    TIMESTAMPTZ   DEFAULT NOW()
);

-- Composite index for fast timeline queries per company
CREATE INDEX IF NOT EXISTS idx_company_activities_company_created
  ON company_activities (company_id, created_at DESC);

-- RLS: restrict to service_role only
ALTER TABLE company_activities ENABLE ROW LEVEL SECURITY;

-- Drop + recreate policy to stay idempotent
DROP POLICY IF EXISTS "service_role_only" ON company_activities;
CREATE POLICY "service_role_only"
  ON company_activities
  FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================================
-- 9. Indexes on new companies columns
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_companies_workflow_status
  ON companies (workflow_status);

CREATE INDEX IF NOT EXISTS idx_companies_payment_status
  ON companies (payment_status);

CREATE INDEX IF NOT EXISTS idx_companies_priority
  ON companies (priority);

CREATE INDEX IF NOT EXISTS idx_companies_next_action_at
  ON companies (next_action_at);
