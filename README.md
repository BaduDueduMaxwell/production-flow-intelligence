# Production Flow Intelligence

The prototype uses simulated fashion and merchandise orders: hoodies, T-shirts, tote bags, caps, sweatshirts, polo shirts, and canvas jackets. Product fields enrich the existing order histories; they are not production data.

An independent portfolio prototype for operational data and workflow automation.

This repository contains deterministic synthetic fixtures, BigQuery DDL and views, importable n8n workflows, a constrained Gemini adapter, and local tests. Cloud verification is reported only where reproducible execution evidence is available.

## What the prototype demonstrates

```text
simulated event -> n8n validation -> BigQuery raw storage
  -> SQL state, quality, and delay views
  -> scheduled alert workflow -> Looker Studio dashboard
```

The lifecycle sequence is:

```text
order_created -> supplier_sourcing -> quotation -> sampling
  -> customer_approval -> production -> fulfillment
```

`order_created` is the authoritative lifecycle start. Invalid events are quarantined without changing the last accepted state. Structurally valid but semantically problematic events remain available in raw data and are classified by derived views. Timestamps in the sample data are UTC.

## Prerequisites

For local tests: Python 3.11+ and Git.

For local n8n: Docker Desktop with Docker Compose and a browser.

Optional cloud integrations require a Google Cloud project with BigQuery access, an authorized credential, a Gemini API key for the optional adapter, and a Looker Studio account. Local tests do not require cloud credentials, n8n credentials, BigQuery, or Gemini.

## Repository layout

```text
bigquery/              BigQuery DDL and GoogleSQL views
n8n/workflows/         Importable n8n workflow definitions
python/                Synthetic fixtures, local runner, Gemini adapter
tests/                 Unit and local end-to-end tests
docker-compose.yml     Local n8n service definition
.env.example           Safe configuration template
```

## Quick start: verify locally

```bash
git clone https://github.com/BaduDueduMaxwell/production-flow-intelligence.git
cd production-flow-intelligence
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The tests cover simulated fashion product metadata, invalid and duplicate events, conflicts, quarantine behavior, delay calculations, metric reconciliation, and Gemini safeguards. Compile the Python modules with:

```bash
python3 -m compileall -q python tests
```

## Start local n8n

```bash
cp .env.example .env
```

Set a local-only encryption key in `.env`:

```text
N8N_ENCRYPTION_KEY=local-development-only-change-me
```

Start and stop n8n with:

```bash
docker compose up -d
docker compose down
```

Open [http://localhost:5678](http://localhost:5678). The `n8n/data/` volume is local runtime state and must never be committed.

## Import the n8n workflows

Use n8n's **Import from File** action in this order:

1. `n8n/workflows/ingest-events-local.json` for the credential-free local path.
2. `n8n/workflows/ingest-events.json` for BigQuery-backed ingestion.
3. `n8n/workflows/detect-delays.json` for scheduled delay detection and alert canonicalization.

Exported workflows contain no credentials. Configure credentials only in n8n, never in JSON files or Git.

The ingestion path is `Receive simulated event -> Validate and normalize -> Valid event? -> Insert raw event -> Accepted response`, with a rejected response for invalid events. The delay workflow runs every 15 minutes, prepares deterministic alert keys, and writes canonical alert records. Its concurrency setting is a best-effort overlap guard, not a distributed lock; exactly-once external notification delivery is not claimed.

## Test the webhook path

1. Open the imported ingestion workflow.
2. Click **Execute workflow** until the webhook says **Listening for test event**.
3. Run this request in a second terminal while it is listening.
4. Return to n8n and inspect validation, BigQuery, and response nodes.

```bash
curl -X POST "http://localhost:5678/webhook-test/production-flow/events" \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_id": "demo-fashion-ord-1002",
    "order_id": "ORD-1002",
    "stage": "sampling",
    "event_type": "stage_entered",
    "event_timestamp": "2026-10-12T09:00:00-04:00",
    "source": "simulated",
    "product_id": "TSHIRT-002",
    "product_name": "Embroidered T-shirt",
    "product_type": "t-shirt",
    "variant": "White cotton, size M",
    "quantity": 25
  }'
```

The test URL is temporary and accepts one request after listening starts. A `404` saying the webhook is not registered means the workflow is not listening; click **Execute workflow** again and resend the request.

## Optional BigQuery setup

The SQL targets GoogleSQL. Use an authorized test project and dataset, replace project or dataset placeholders for your environment, and never commit service-account keys.

Run DDL in this order: `raw_events.sql`, `rejected_events.sql`, `processing_attempts.sql`, `quality_issues.sql`, `orders.sql`, `stage_thresholds.sql`, then `alerts.sql`.

Then create views in this order: `v_canonical_events.sql`, `v_reconciled_events.sql`, `v_order_stage_state.sql`, `v_data_quality_detail.sql`, `v_data_quality_overview.sql`, `v_delayed_orders.sql`, then `v_dashboard_overview.sql`.

The required dashboard views are `v_dashboard_overview`, `v_data_quality_overview`, `v_data_quality_detail`, and `v_delayed_orders`. SQL files alone do not prove cloud execution; verification requires an authorized project and captured execution result.

## Optional Looker Studio setup

Connect Looker Studio to the four required views. Use the pages in this order: **Overview** for summary metrics, **Data Quality** for validation investigation, and **Delayed Orders** for affected products, orders, stages, elapsed hours, and thresholds. Keep the simulated-data disclaimer visible.

## Optional Gemini adapter

`python/gemini_query.py` supports the constrained `delayed_orders` intent and rejects unsupported questions. Set `GEMINI_API_KEY` only locally when testing it. No key is required for the core tests.

## Troubleshooting

- **Python unavailable:** install Python 3.11+ and check `python3 --version`.
- **Docker unavailable:** start Docker Desktop and check `docker compose version`.
- **Port 5678 busy:** stop the other service or change the host-side port in `docker-compose.yml`.
- **Webhook 404:** click **Execute workflow** first; the test webhook exists only while listening and accepts one request.
- **BigQuery permission error:** check the project, BigQuery API, dataset permissions, and n8n credential. Local tests do not require BigQuery.
- **Looker Studio view error:** confirm the view exists, the account can query it, and field names match the view schema.
- **Gemini key error:** set `GEMINI_API_KEY` locally or skip the optional adapter.
