WITH appointment_facts(appointment_id, facility_id, scheduled_date) AS (
  VALUES
    ('A001', 'FAC01', DATE '2026-03-10'),
    ('A002', 'FAC02', DATE '2026-03-10'),
    ('A006', 'FAC03', DATE '2026-03-10')
), facility_versions(facility_version_key, facility_id, region, valid_from, valid_to) AS (
  VALUES
    (10, 'FAC01', 'East',  DATE '2020-01-01', DATE '9999-12-31'),
    (20, 'FAC02', 'North', DATE '2020-01-01', DATE '2026-03-01'),
    (21, 'FAC02', 'South', DATE '2026-03-01', DATE '9999-12-31'),
    (30, 'FAC03', 'West',  DATE '2020-01-01', DATE '9999-12-31')
)
SELECT a.appointment_id, a.facility_id, d.region,
       COUNT(d.facility_version_key) OVER (
         PARTITION BY a.appointment_id
       ) AS dimension_matches
FROM appointment_facts a
LEFT JOIN facility_versions d
  ON a.facility_id = d.facility_id
 AND a.scheduled_date >= d.valid_from
 AND a.scheduled_date < d.valid_to
ORDER BY a.appointment_id;
