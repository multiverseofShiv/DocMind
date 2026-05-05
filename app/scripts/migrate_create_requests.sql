CREATE TABLE IF NOT EXISTS requests(
        id          BIGSERIAL PRIMARY KEY,
        tenant_id   TEXT NOT NULL,
        query       TEXT NOT NULL,
        model       TEXT,
        tokenS_in    INTEGER NOT NULL DEFAULT 0,
        tokenS_out   INTEGER NOT NULL DEFAULT 0,
        cost_usd    DOUBLE PRECISION NOT NULL DEFAULT 0,
        latency_ms  INTEGER NOT NULL DEFAULT 0,
        cache_hit   BOOLEAN NOT NULL DEFAULT false,
        ts          TIMESTAMP WITH TIME ZONE DEFAULT now()
);


CREATE INDEX IF NOT EXISTS idx_requests_tenant_ts ON requests (tenant_id, ts DESC)



Created tenant tenant_a with API key: Hiaw_8NBx5QaiIYSwfbx_1pmxPYnFY6a
Created tenant tenant_b with API key: kX-vyq1EwJu2BhFy6KjOXANRa1hBLnTK