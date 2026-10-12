-- Explicit state-machine reconstruction. Invalid events are returned with
-- accepted=FALSE so later valid events are evaluated from the prior accepted state.
CREATE OR REPLACE VIEW `PROJECT.DATASET.v_canonical_events` AS
WITH RECURSIVE
ordered AS (
  SELECT
    e.*,
    ROW_NUMBER() OVER (
      PARTITION BY order_id
      -- Creation is evaluated first when present so pre-creation records can
      -- be reconciled without being discarded. Their original event time is
      -- retained and can be marked late by downstream quality logic.
      ORDER BY CASE WHEN event_type = 'order_created' THEN 0 ELSE 1 END,
        event_timestamp,
        CASE event_type WHEN 'order_created' THEN 0 WHEN 'stage_entered' THEN 1
          WHEN 'stage_exited' THEN 2 WHEN 'order_cancelled' THEN 3 ELSE 99 END,
        ingested_at, event_id, payload_hash
    ) AS seq
  FROM `PROJECT.DATASET.v_reconciled_events` e
  WHERE reconciliation_status IN ('accepted', 'reconcilable')
),
fold AS (
  SELECT
    o.*,
    1 AS state_seq,
    'order_created' AS accepted_state,
    CAST(NULL AS STRING) AS open_stage,
    TRUE AS accepted,
    CAST(NULL AS STRING) AS issue_type
  FROM ordered o
  WHERE o.seq = 1 AND o.event_type = 'order_created'
  UNION ALL
  SELECT
    o.*,
    f.state_seq + 1,
    CASE
      WHEN o.event_type = 'stage_exited' AND f.open_stage = o.stage THEN o.stage
      WHEN o.event_type = 'stage_entered' AND f.open_stage IS NULL THEN f.accepted_state
      ELSE f.accepted_state
    END AS accepted_state,
    CASE
      WHEN o.event_type = 'stage_entered' AND f.open_stage IS NULL THEN o.stage
      WHEN o.event_type = 'stage_exited' AND f.open_stage = o.stage THEN NULL
      ELSE f.open_stage
    END AS open_stage,
    CASE
      WHEN o.event_type = 'stage_entered'
        AND f.open_stage IS NULL
        AND o.stage = CASE WHEN f.accepted_state = 'order_created' THEN 'supplier_sourcing'
          ELSE CASE f.accepted_state WHEN 'supplier_sourcing' THEN 'quotation'
            WHEN 'quotation' THEN 'sampling' WHEN 'sampling' THEN 'customer_approval'
            WHEN 'customer_approval' THEN 'production' WHEN 'production' THEN 'fulfillment' END END
        THEN TRUE
      WHEN o.event_type = 'stage_exited' AND f.open_stage = o.stage THEN TRUE
      ELSE FALSE
    END AS accepted,
    CASE
      WHEN o.event_type = 'stage_exited' AND f.open_stage != o.stage THEN 'orphan_exit'
      WHEN o.event_type = 'stage_entered' AND f.open_stage IS NOT NULL THEN 'invalid_transition'
      WHEN o.event_type = 'stage_entered' AND o.stage != CASE WHEN f.accepted_state = 'order_created' THEN 'supplier_sourcing'
        ELSE CASE f.accepted_state WHEN 'supplier_sourcing' THEN 'quotation'
          WHEN 'quotation' THEN 'sampling' WHEN 'sampling' THEN 'customer_approval'
          WHEN 'customer_approval' THEN 'production' WHEN 'production' THEN 'fulfillment' END END THEN 'invalid_transition'
      ELSE NULL
    END AS issue_type
  FROM fold f
  JOIN ordered o ON o.order_id = f.order_id AND o.seq = f.seq + 1
)
SELECT * FROM fold;
