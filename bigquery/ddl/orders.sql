CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.orders` (
  order_id STRING NOT NULL,
  product_id STRING,
  product_name STRING,
  product_type STRING,
  variant STRING,
  quantity INT64,
  supplier_id STRING,
  created_at TIMESTAMP NOT NULL,
  cancelled_at TIMESTAMP,
  source STRING NOT NULL
)
PARTITION BY DATE(created_at)
CLUSTER BY order_id, supplier_id;
