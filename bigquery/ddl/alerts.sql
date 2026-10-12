CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.alerts` (
  alert_key STRING NOT NULL,
  order_id STRING NOT NULL,
  stage STRING NOT NULL,
  condition_type STRING NOT NULL,
  detected_at TIMESTAMP NOT NULL,
  last_seen_at TIMESTAMP NOT NULL,
  status STRING NOT NULL,
  notification_status STRING NOT NULL,
  notification_attempts INT64 NOT NULL,
  last_error STRING,
  resolved_at TIMESTAMP
)
PARTITION BY DATE(detected_at)
CLUSTER BY alert_key, order_id, status;
