# Browser analytics on Databricks on AWS

This original Northstar supplement supports Chapters 3, 7, 12, 15, and 19 of
*Databricks on AWS* by Vishnu VG. It uses the existing synthetic appointment
contract and adds no dependency to the canonical pipeline or prediction job.

Use the assigned Databricks on AWS workspace and approved learning catalog.
Free Edition is an optional rehearsal of supported features; it does not verify
an enterprise AWS deployment, different users' permissions, or every ML workload.
Replace `analytics` consistently in your practice copy when the owner supplies
another writable catalog.

Import `00_notebook_readiness.py` as a Databricks source notebook and run its
cells on permitted Python/Spark compute. The SQL cell should sum the temporary
view to 3; it does not create a persistent report or establish S3 access.
`00_workspace_context.sql` identifies the actual SQL session context before you
use fully qualified object names. Neither operation requires a second personal
signup when an AWS workspace has already been assigned.

## Upload inspection — Chapter 3

1. Obtain a permitted scratch namespace; an authorized learning engineer can
   run `00_prepare_scratch.sql`. Keep it separate from bronze/silver/gold.
2. Use the [AWS file-upload UI](https://docs.databricks.com/aws/en/ingestion/create-or-modify-table)
   to create `analytics.learning_preview.appointments_upload` from the unchanged
   `sample-data/appointments.csv`. Keep all four source fields as strings, retain
   the missing key and `invalid-date`, and do not overwrite an existing table.
3. Upload this folder's `learning_facilities.json` as
   `analytics.learning_preview.facilities_upload`. It is newline-delimited JSON:
   each of its three lines is a separate object.
4. Run `01_inspect_uploads.sql` in SQL Editor on a permitted SQL warehouse.
   Expect six arrivals, one lookup row per facility, and raw joined counts
   FAC01: 3, FAC02: 2, FAC03: 1. These are arrivals, not accepted appointments.

The lookup is only a display/import exercise. Neither scratch table supplies
replacement input to the main job. The canonical pipeline still reads its
existing source fixtures and accepts A001/A002/A006 after two rejected arrivals
and one identical valid repeat.

## SQL and dashboard — Chapter 7

Run the existing ingestion, quality, and report checkpoints first, or obtain
the engineer's accepted aggregate and run evidence. `02_reference_report.sql`
must return FAC01: 1, FAC02: 1, FAC03: 1, represented facilities: 3, and accepted
appointments: 3. The analyst needs only the existing gold aggregate and the
appropriate catalog/schema usage, SQL entitlement, and compute rights.

For `03_facility_parameter.sql`, configure a single string parameter named
`facility`: `ALL` returns three rows, `FAC02` returns one, and `FAC99` returns no
rows. `04_sum_vs_count.sql` creates no table: its isolated hypothetical 2/1/1
values return three facilities and four appointments. Do not persist those
hypothetical values as the canonical report.

Follow the [AWS dashboard authoring guide](https://docs.databricks.com/aws/en/dashboards/tutorials/create-dashboard)
using only the first SELECT in `02_reference_report.sql` as one dataset. Create
a facility bar chart, a counter summing `appointments`, and a two-column table.
Connect a field filter to `facility_id` in that same dataset. Check all values,
FAC02, FAC01 plus FAC03, and reset: counter totals must be 3, 1, 2, and 3.
Keep the fixed synthetic March-snapshot scope visible; this two-column product
has no genuine date dimension for a historical trend or date slider.

Before sharing, review dataset scope, asset permissions, and the
[AWS publishing data-permission mode](https://docs.databricks.com/aws/en/dashboards/share/share).
The book's aggregate-only path uses individual data permissions. Test an actual
intended viewer separately; a second tab under the author's identity is not
a distinct-user test. Publication freezes an asset definition, while refreshed
values can change when the producing table changes.

## Genie and coding assistance — Chapter 15

Use `05_genie_examples.sql` as references for a curated Genie Agent over only
`analytics.gold.appointments_by_facility`. Define the accepted appointment
measure and fixed period. Check per-facility counts, total 3, FAC02 follow-up,
unsupported patient details, and unsupported attendance trends. Inspect the
actual generated SQL and result, and retain the data/compute prerequisites in
the [AWS Genie setup guide](https://docs.databricks.com/aws/en/genie-agents/set-up).

`negative_column_error.sql` is deliberately invalid. Run it only as a separate
scratch exercise: `appointment_count` does not exist. Ask the built-in coding
assistant to explain the error, review the proposed correction to `appointments`,
and run the corrected read-only query. Preserve the successful reference and do
not broaden data access to make an error disappear.

## Local checks and evidence boundary

From the repository root, on Python 3.10 or later:

```sh
python -W error tools/check_local.py
python -W error tools/check_browser_analytics.py
```

The second command executes the supplied SQL using SQLite after removing only
catalog/schema qualification. With PySpark 4.0.1 and a compatible Java runtime,
`python tools/check_browser_analytics.py --spark` executes the same examples with
actual local Spark SQL and bound parameter values. Both routes use temporary
local objects and no cloud credentials. GitHub Actions checks these routes.

Neither local SQL execution nor book HTML rendering establishes authenticated
Databricks UI clicks, Unity Catalog authorization, a live AI response, or an AWS
deployment. Record those observations in the actual workspace. After learning,
retire only the designated scratch assets and unused schedules; keep the main
gold product while other book exercises still depend on it.
