-- Reference questions use the actual aggregate, not hard-coded answers.
SELECT SUM(appointments) AS accepted_appointments
FROM analytics.gold.appointments_by_facility;

SELECT facility_id, appointments
FROM analytics.gold.appointments_by_facility
WHERE facility_id = 'FAC02';
