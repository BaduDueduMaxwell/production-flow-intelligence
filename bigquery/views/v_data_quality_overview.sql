CREATE OR REPLACE VIEW `PROJECT.DATASET.v_data_quality_overview` AS
SELECT
  record_origin,
  COALESCE(stage, 'unknown') AS stage,
  COALESCE(quality_issue, 'valid_or_pending') AS quality_status,
  COUNT(*) AS record_count,
  COUNTIF(canonical_accepted = TRUE) AS canonical_record_count,
  CURRENT_TIMESTAMP() AS data_as_of
FROM `PROJECT.DATASET.v_data_quality_detail`
GROUP BY record_origin, stage, quality_status;
