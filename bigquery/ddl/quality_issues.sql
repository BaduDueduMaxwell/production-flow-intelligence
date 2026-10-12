CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.quality_issues` (
  issue_id STRING NOT NULL,
  issue_type STRING NOT NULL,
  event_id STRING,
  order_id STRING,
  detected_at TIMESTAMP NOT NULL,
  severity STRING NOT NULL,
  details JSON,
  resolved_at TIMESTAMP
)
PARTITION BY DATE(detected_at)
CLUSTER BY issue_type, order_id;
