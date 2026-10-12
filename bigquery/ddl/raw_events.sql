CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.raw_events` (
  event_id STRING NOT NULL,
  order_id STRING NOT NULL,
  product_id STRING,
  product_name STRING,
  product_type STRING,
  variant STRING,
  quantity INT64,
  stage STRING NOT NULL,
  event_type STRING NOT NULL,
  event_timestamp TIMESTAMP NOT NULL,
  ingested_at TIMESTAMP NOT NULL,
  supplier_id STRING,
  source STRING NOT NULL,
  payload_hash STRING NOT NULL,
  ingestion_run_id STRING,
  validation_status STRING NOT NULL
)
PARTITION BY DATE(ingested_at)
CLUSTER BY order_id, stage, event_id;
