CREATE OR REPLACE VIEW `PROJECT.DATASET.v_dashboard_overview` AS
SELECT
  CURRENT_TIMESTAMP() AS data_as_of,
  COUNT(DISTINCT order_id) AS active_orders,
  COUNTIF(elapsed_hours >= threshold_hours) AS delayed_stage_rows,
  COUNT(DISTINCT stage) AS observed_stages,
  COUNT(DISTINCT product_type) AS product_types
FROM `PROJECT.DATASET.v_delayed_orders`;
