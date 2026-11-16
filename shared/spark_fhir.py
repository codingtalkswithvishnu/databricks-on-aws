"""Extract the explicitly limited synthetic FHIR R4-shaped appointment fixture.

This is an envelope/reference mapping, not a complete FHIR conformance validator.
Only booked appointments with one relative Patient and one Location reference
are supported; the fixture uses UTC-Z starts and a UTC reporting date.
"""
from pyspark.sql import functions as F

BUNDLE_SCHEMA = (
    "resourceType STRING, type STRING, entry ARRAY<STRUCT<resource:STRUCT<"
    "resourceType:STRING,id:STRING,status:STRING,start:STRING,end:STRING,"
    "participant:ARRAY<STRUCT<actor:STRUCT<reference:STRING>,status:STRING>>>>>"
)


def extract_appointments(raw):
    documents = raw.select(F.from_json("payload", BUNDLE_SCHEMA).alias("bundle"))
    if documents.filter(F.col("bundle").isNull()
                        | F.col("bundle.resourceType").isNull()
                        | (F.col("bundle.resourceType") != "Bundle")
                        | (F.col("bundle.type") != "collection")
                        | F.col("bundle.type").isNull()
                        | F.col("bundle.entry").isNull()
                        | (F.size("bundle.entry") == 0)).limit(1).count():
        raise ValueError("Expected a nonempty collection Bundle envelope")
    entries = documents.select(F.explode("bundle.entry").alias("entry")).select("entry.resource.*")
    if entries.filter(F.col("resourceType").isNull() | (F.col("resourceType") != "Appointment")
                      | F.col("status").isNull() | (F.col("status") != "booked")).limit(1).count():
        raise ValueError("This fixture mapping accepts booked Appointment resources only")
    references = (entries.withColumn("patient_refs", F.expr(
        "transform(filter(participant, p -> p.actor.reference RLIKE '^Patient/[A-Za-z0-9.-]+$'), "
        "p -> p.actor.reference)"))
        .withColumn("location_refs", F.expr(
        "transform(filter(participant, p -> p.actor.reference RLIKE '^Location/[A-Za-z0-9.-]+$'), "
        "p -> p.actor.reference)")))
    if references.filter(F.col("patient_refs").isNull() | F.col("location_refs").isNull()
                         | (F.size("patient_refs") != 1) | (F.size("location_refs") != 1)).limit(1).count():
        raise ValueError("Resolve exactly one supported patient and facility reference per appointment")
    return references.select(
        F.col("id").alias("appointment_id"),
        F.regexp_extract(F.element_at("patient_refs", 1), r"^Patient/(.+)$", 1).alias("patient_id"),
        F.when(F.col("start").endswith("Z") & F.expr("try_cast(start AS TIMESTAMP)").isNotNull(),
               F.substring("start", 1, 10)).alias("scheduled_date"),
        F.regexp_extract(F.element_at("location_refs", 1), r"^Location/(.+)$", 1).alias("facility_id"),
    )
