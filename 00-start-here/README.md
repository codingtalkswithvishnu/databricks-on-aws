# Begin with the healthcare source contract

Northstar Health Network is fictional. Every patient, appointment, facility,
ticket and policy is invented. This is scheduling/attendance operations and
administrative AI, not clinical prediction or an appointment-changing system.

## Reconcile the inputs

| Source | Grain and expected state |
| --- | --- |
| appointments.csv | 6 arrivals; 4 valid including 1 identical duplicate; 3 accepted keys A001/A002/A006; 2 rejections. |
| appointment_history.csv | 40 January scheduled visits for P001–P020; visit_id, date, finite nonnegative lead_days, attended 0/1. |
| attendance_outcomes.csv | One later target for each of 20 patients; scheduled 15 February, observed 16 February; no_show 0/1. |
| tickets.csv | 3 administrative examples, expected billing/technical/other. |
| policies.json | 3 approved version-1.0 administrative policies effective 1 January. |
| events.jsonl | 3 check-in events in one minute, one for each facility; optional Kinesis branch. |
| appointment_updates.csv | 4 arrivals for the isolated versioned update exercise. |
| appointments_bundle.json | Limited nested R4-shaped collection mapping of the 6 appointment arrivals. |

Appointments count scheduled bookings, not patients or completed encounters.
The missing appointment key and invalid date each produce one rejection.
Unknown facilities and missing patient IDs also reject. Conflicting valid
payloads under one appointment key stop the batch; an arbitrary winner is invalid.

The baseline date is 10 March 2026. FAC01/FAC02/FAC03 each have one accepted
appointment. The report uses facility_id and appointments in a fixed snapshot.

## Preserve the time boundary

Aggregate January history before the 1 February feature cutoff. Only then attach
the February no_show labels. Predictors are prior_visits, prior_missed_visits,
and avg_lead_days. The 20-patient fixture splits 16/4; held-out patients are
P005/P010/P015/P020. Score the 3 March accepted appointments, retaining keys,
cutoff and model_run_id. A missing predictor match blocks publication.

The cutoff is fixed for reproducibility and stale for actual March operations.
A real deployment needs accepted freshness, labels, temporal/subgroup evaluation,
calibration and permitted human review. The tiny fixture cannot establish model
quality or improved attendance. The review queue may contain 0–3 rows according
to the actual predictions and triggers no contact.

## Prepare the execution environment

Local Python commands need no credentials. Spark notebooks need a separately
approved workspace and disposable analytics catalog, compatible runtime/access
mode and required packages. 00_setup.py checks a DataFrame operation, creates
the agreed schemas and prepares raw fixture DataFrames. It does not verify S3.

Keep these schemas together: bronze, silver, gold, operations, ml, support,
monitoring. The learning engineer needs the scoped write rights; an operations
analyst needs only the accepted aggregate. A model owner separately reviews
patient-level learning outputs. Administrators configure actual AWS storage and
network access; sign-in alone does not establish it.

Record the code revision, compute/runtime/access mode, workload identity,
namespace approval, source definitions, expected results and spending owner.
Run the numbered checkpoints in order. Preserve source snapshots and actual
output/run references so failed stages can be diagnosed and recovered.
