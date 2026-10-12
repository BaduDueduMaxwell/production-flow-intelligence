-- GoogleSQL scenario checklist for Milestone A.
-- These queries are not reported as executed until run against BigQuery.
-- Expected outcomes are documented in docs/lifecycle-rules.md.

-- Pre-creation events remain available for reconciliation.
SELECT order_id, event_id, validation_status
FROM `PROJECT.DATASET.raw_events`
WHERE validation_status = 'pending_order_creation';

-- Invalid transitions do not advance canonical state.
SELECT order_id, event_id, issue_type
FROM `PROJECT.DATASET.quality_issues`
WHERE issue_type = 'invalid_transition';
