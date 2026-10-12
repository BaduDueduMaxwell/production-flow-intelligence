# Production Flow Intelligence

The prototype uses simulated fashion and merchandise orders: hoodies, T-shirts, tote bags, caps, sweatshirts, polo shirts, and canvas jackets. Product fields enrich the existing order histories; they do not represent THE/STUDIO production data.

An independent, simulated portfolio prototype for THE/STUDIO's Data and Automation Systems Builder role.

This repository contains the lifecycle contract, deterministic synthetic fixtures, BigQuery DDL and view definitions, importable n8n workflow definitions, a constrained Gemini adapter, and local tests. Cloud verification is reported only where reproducible execution evidence is available.

## Lifecycle contract

`order_created` is the authoritative start of an order lifecycle. Events arriving before it remain in raw data as `pending_order_creation` and are reconsidered by reconciliation views after the creation event arrives.

The linear stage sequence is:

```text
order_created -> supplier_sourcing -> quotation -> sampling -> customer_approval -> production -> fulfillment
```

A stage must exit before the next stage can begin. Invalid events are quarantined without changing the last accepted state. All timestamps are UTC.

## Local tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Data-quality contract

Structurally invalid events belong in the `rejected_events` quarantine; structurally valid but semantically problematic events remain in `raw_events` and are classified by derived views.

## n8n import

Import the JSON files under `n8n/workflows/` into a local n8n instance. Credentials and environment variables are intentionally not configured in the exported workflows.

The delay workflow uses one scheduled query and `settings.maxConcurrency = 1` as a best-effort overlap guard. BigQuery is not used as a distributed lock; repeated sequential runs are canonicalized by `alert_key`, but exactly-once external notification delivery is not claimed.

## Gemini adapter

`python/gemini_query.py` supports one intent, `delayed_orders`, and refuses unsupported questions. It raises a clear error when `GEMINI_API_KEY` is absent. It has not been executed against Gemini in this repository.

The SQL files target GoogleSQL and are not reported as executed until they run against an authorized BigQuery project.

The exported n8n definitions are configuration artifacts. Any cloud execution claim must be backed by a reproducible execution result and should be recorded separately from local test results. Manual credential setup and an authorized test project are required for integration verification.

## CI and release artifacts

GitHub Actions runs Python tests, compiles modules, validates n8n workflow JSON, and performs basic SQL checks on every pull request and push to `main`. The manual deployment workflow packages the n8n workflow definitions, BigQuery SQL, and this README into a versioned GitHub Release artifact. It does not claim to deploy credentials or connect to a production environment.
