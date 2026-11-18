-- Run after the two explicitly named browser uploads; source fields remain strings.
SELECT COUNT(*) AS delivered_arrivals
FROM analytics.learning_preview.appointments_upload;

SELECT facility_id, COUNT(*) AS lookup_rows
FROM analytics.learning_preview.facilities_upload
GROUP BY facility_id
ORDER BY facility_id;

SELECT a.facility_id, f.facility_label,
       COUNT(*) AS delivered_arrivals
FROM analytics.learning_preview.appointments_upload AS a
LEFT JOIN analytics.learning_preview.facilities_upload AS f
  ON a.facility_id = f.facility_id
GROUP BY a.facility_id, f.facility_label
ORDER BY a.facility_id;
