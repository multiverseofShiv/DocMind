CREATE TABLE IF NOT EXISTS api_key(
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash TEXT NOT NULL UNIQUE,
    tenant_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    active BOOLEAN DEFAULT true
);



-- docker compose cp scripts/migrate_create_api_keys.sql postgres:/tmp/migrate_create_api_keys.sql
-- docker compose exec -T postgres psql -U docmind -d docmind -f /tmp/migrate_create_api_keys.sql


--                   id                  |                             key_hash                             | tenant_id |          created_at          | active 
-- --------------------------------------+------------------------------------------------------------------+-----------+------------------------------+--------
--  e25beea4-dd90-48c0-8287-799012f48123 | ce03f1361705e0ffa5b865dd78a0ca3b7408e390922da4950bd9faad4ab1eefa | tenant_a  | 2026-04-29 11:39:45.11862+00 | t
--  49de97b6-4504-4b01-a828-19514bbb2557 | 77455b1763083716ad2c29dbb18547b377deb0b53fde2873e93a05694f018dda | tenant_b  | 2026-04-29 11:39:45.11862+00 | t

-- bec32180a873bd1039751b5ed0e9e61dac667350c8e18475e49afbf421b19d22


-- Created tenant tenant_a with API key: E7cliHommioXMzYBvqR5ivlmXxJoE936
-- Created tenant tenant_b with API key: qHK09MDh4ets4AcYdmVu9VdV_Le8KaGT