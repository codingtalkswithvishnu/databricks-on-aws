-- Bind facility as a single string: ALL, FAC02, FAC99.
SELECT facility_id, appointments
FROM analytics.gold.appointments_by_facility
WHERE :facility = 'ALL' OR facility_id = :facility
ORDER BY facility_id;
