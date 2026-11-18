-- Hypothetical arithmetic only: no persisted source or canonical fixture changes.
WITH illustrative_counts AS (
  SELECT 'FAC01' AS facility_id, 2 AS appointments
  UNION ALL SELECT 'FAC02', 1
  UNION ALL SELECT 'FAC03', 1
)
SELECT COUNT(*) AS represented_facilities,
       SUM(appointments) AS accepted_appointments
FROM illustrative_counts;
