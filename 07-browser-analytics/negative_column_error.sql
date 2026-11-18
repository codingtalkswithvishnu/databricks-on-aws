-- EXPECTED FAILURE: appointment_count is intentionally not a source column.
-- The corrected read-only query uses SUM(appointments), returning 3.
SELECT SUM(appointment_count) AS accepted_appointments
FROM analytics.gold.appointments_by_facility;
