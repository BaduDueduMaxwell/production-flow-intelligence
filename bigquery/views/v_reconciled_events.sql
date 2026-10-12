-- Reconciliation keeps pre-creation records queryable and marks them eligible
-- for the canonical state-machine fold once order creation exists.
CREATE OR REPLACE VIEW `PROJECT.DATASET.v_reconciled_events` AS
SELECT
  e.*,
  CASE
    WHEN e.event_type = 'order_created' AND e.validation_status != 'rejected' THEN 'accepted'
    WHEN c.order_id IS NULL AND e.event_type != 'order_created' THEN 'pending_order_creation'
    WHEN c.order_id IS NOT NULL AND e.validation_status IN ('accepted', 'pending_order_creation', 'pending_state_machine') THEN 'reconcilable'
    ELSE e.validation_status
  END AS reconciliation_status
FROM `PROJECT.DATASET.raw_events` e
LEFT JOIN (
  SELECT order_id, MIN(event_timestamp) AS created_at
  FROM `PROJECT.DATASET.raw_events`
  WHERE event_type = 'order_created'
    AND validation_status = 'accepted'
  GROUP BY order_id
) c USING (order_id);
