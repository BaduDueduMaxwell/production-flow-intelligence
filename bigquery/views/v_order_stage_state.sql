CREATE OR REPLACE VIEW `PROJECT.DATASET.v_order_stage_state` AS
WITH accepted AS (
  SELECT *
  FROM `PROJECT.DATASET.v_canonical_events`
  WHERE accepted = TRUE
),
stage_pairs AS (
  SELECT
    order_id,
    ANY_VALUE(product_id) AS product_id,
    ANY_VALUE(product_name) AS product_name,
    ANY_VALUE(product_type) AS product_type,
    ANY_VALUE(variant) AS variant,
    ANY_VALUE(quantity) AS quantity,
    stage,
    MIN(IF(event_type = 'stage_entered', event_timestamp, NULL)) AS stage_entered_at,
    MAX(IF(event_type = 'stage_exited', event_timestamp, NULL)) AS stage_exited_at,
    MAX(event_timestamp) AS last_event_at,
    COUNT(*) AS accepted_event_count
  FROM accepted
  WHERE stage != 'order'
  GROUP BY order_id, stage
)
SELECT
  order_id,
  product_id,
  product_name,
  product_type,
  variant,
  quantity,
  stage,
  stage_entered_at,
  stage_exited_at,
  last_event_at,
  accepted_event_count,
  stage_exited_at IS NULL AS is_open
FROM stage_pairs
WHERE stage_entered_at IS NOT NULL;
