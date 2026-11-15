# Start with the contract

Cedar Retail is a fictional retailer. Begin with the six signup rows: two invalid,
one identical duplicate after validation, three accepted signups, and GB/IN/US
country counts of one each. Conflicting duplicate emails need an explicit winner
rule; the local check refuses to invent one.

The order fixture has 20 customers (C001–C020), two orders per customer, and
a deliberately synthetic binary churned label. It is a pipeline fixture, not
a real churn model. Hold out C005/C010/C015/C020 for the 16/4 learning split.

Create a practice copy outside this reference folder. Run the local checks from
the repository root first. Keep your environment/access notes in your practice
copy. The reference scripts do not overwrite a notes file.

For Databricks, ask the administrator for a disposable analytics catalog and the
required USE/CREATE permissions. Record workspace, region, principal,
runtime/access mode, package versions and spending owner. Run 00_setup.py,
then 01_ingest, 02_clean and 03_report in order. Creation of learning schemas
and overwrite resets are intentional; never point them at production namespaces.

The bundle uses an explicitly supplied existing classic learning cluster.
Review API/library compatibility before choosing runtime. Runtime-specific ML
support is a separate prerequisite for the prediction notebook.

For S3: upload only supplied fixtures to approved prefixes and complete the
external-location/role configuration first. A synthetic DataFrame run is not
evidence of AWS access. Optional integrations and cloud verification are in
06-integrations/README.md.

