CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.stage_thresholds` (
  stage STRING NOT NULL,
  threshold_hours INT64 NOT NULL,
  effective_from TIMESTAMP NOT NULL,
  effective_to TIMESTAMP,
  is_active BOOL NOT NULL
);
