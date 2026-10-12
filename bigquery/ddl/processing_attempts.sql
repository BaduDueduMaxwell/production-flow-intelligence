CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.processing_attempts` (
  attempt_id STRING NOT NULL,
  event_id STRING,
  workflow_name STRING NOT NULL,
  attempted_at TIMESTAMP NOT NULL,
  status STRING NOT NULL,
  error_code STRING,
  error_message STRING,
  n8n_execution_id STRING
)
PARTITION BY DATE(attempted_at)
CLUSTER BY workflow_name, status;
