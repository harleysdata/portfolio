-- Star-style reporting model for contingent workforce compliance.
-- fact table: one row per contractor; dimension: vendors.

DROP TABLE IF EXISTS vendors;
CREATE TABLE vendors (
    vendor_id         TEXT PRIMARY KEY,
    vendor_name       TEXT NOT NULL,
    risk_tier         TEXT CHECK (risk_tier IN ('Low', 'Medium', 'High')),
    contract_end_date DATE
);

DROP TABLE IF EXISTS contingent_workers;
CREATE TABLE contingent_workers (
    worker_id               TEXT PRIMARY KEY,
    vendor_id               TEXT NOT NULL REFERENCES vendors(vendor_id),
    business_unit           TEXT NOT NULL,
    role                    TEXT,
    start_date              DATE,
    end_date                DATE,
    bill_rate_cad           REAL,
    background_check_status TEXT,
    nda_signed              INTEGER,  -- 1 = yes, 0 = no
    training_completed      INTEGER,
    tenure_review_done      INTEGER,
    issue_count             INTEGER,  -- number of failed compliance checks
    is_compliant            INTEGER
);
