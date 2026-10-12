CREATE OR REPLACE VIEW `PROJECT.DATASET.v_delayed_orders` AS
SELECT
  s.order_id,
  s.product_id,
  s.product_name,
  s.product_type,
  s.variant,
  s.quantity,
  s.stage,
  s.stage_entered_at,
  t.threshold_hours,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), s.stage_entered_at, HOUR) AS elapsed_hours,
  CONCAT(s.order_id, ':', s.stage, ':stage_delay') AS alert_key
FROM `PROJECT.DATASET.v_order_stage_state` s
JOIN `PROJECT.DATASET.stage_thresholds` t USING (stage)
WHERE t.is_active
  AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), s.stage_entered_at, HOUR) >= t.threshold_hours;
