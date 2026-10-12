-- Quality detail preserves source values and exposes derived classifications.
CREATE OR REPLACE VIEW `PROJECT.DATASET.v_data_quality_detail` AS
WITH raw_quality AS (
  SELECT
    r.event_id,
    r.order_id,
    r.product_id,
    r.product_name,
    r.product_type,
    r.variant,
    r.quantity,
    r.stage,
    r.event_type,
    CAST(r.event_timestamp AS STRING) AS source_event_timestamp,
    CAST(r.event_timestamp AS STRING) AS normalized_event_timestamp,
    r.ingested_at,
    r.validation_status AS source_validation_status,
    COALESCE(c.issue_type, IF(r.validation_status = 'rejected', 'rejected_at_ingestion', NULL)) AS quality_issue,
    c.accepted AS canonical_accepted,
    CAST(NULL AS STRING) AS completion_status,
    CAST(NULL AS INT64) AS elapsed_hours,
    'raw_events' AS record_origin
  FROM `PROJECT.DATASET.raw_events` r
  LEFT JOIN `PROJECT.DATASET.v_canonical_events` c USING (event_id)
), quarantined AS (
  SELECT
    event_id,
    order_id,
    CAST(NULL AS STRING) AS product_id,
    CAST(NULL AS STRING) AS product_name,
    CAST(NULL AS STRING) AS product_type,
    CAST(NULL AS STRING) AS variant,
    CAST(NULL AS INT64) AS quantity,
    CAST(NULL AS STRING) AS stage,
    CAST(NULL AS STRING) AS event_type,
    JSON_VALUE(raw_payload, '$.event_timestamp') AS source_event_timestamp,
    CAST(NULL AS STRING) AS normalized_event_timestamp,
    received_at AS ingested_at,
    validation_status AS source_validation_status,
    ARRAY_TO_STRING(issue_codes, ', ') AS quality_issue,
    FALSE AS canonical_accepted,
    'unavailable: rejected before timestamp normalization' AS completion_status,
    CAST(NULL AS INT64) AS elapsed_hours,
    'rejected_events' AS record_origin
  FROM `PROJECT.DATASET.rejected_events`
)
SELECT * FROM raw_quality
UNION ALL
SELECT * FROM quarantined;
