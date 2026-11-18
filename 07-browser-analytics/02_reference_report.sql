-- The first statement alone is the approved dashboard dataset.
SELECT facility_id, appointments
FROM analytics.gold.appointments_by_facility
ORDER BY facility_id;

-- Different measures coincide on this deliberately small real fixture.
SELECT COUNT(*) AS represented_facilities,
       SUM(appointments) AS accepted_appointments
FROM analytics.gold.appointments_by_facility;
