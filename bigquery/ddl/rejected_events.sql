CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.rejected_events` (
  quarantine_id STRING NOT NULL,
  event_id STRING,
  order_id STRING,
  received_at TIMESTAMP NOT NULL,
  source STRING,
  ingestion_run_id STRING,
  validation_status STRING NOT NULL,
  issue_codes ARRAY<STRING>,
  issue_details STRING NOT NULL,
  raw_payload JSON NOT NULL
)
PARTITION BY DATE(received_at)
CLUSTER BY order_id, validation_status;
