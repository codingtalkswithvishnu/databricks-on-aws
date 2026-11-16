# One plan and one permitted read

Run from the repository root:

```shell
python 05-agent/agent.py --question "How many accepted appointments are there by facility?"
python 05-agent/agent.py --question "How much notice is needed for appointment rescheduling?"
python 05-agent/agent.py --question "Cancel the patient appointment"
```

Default planning is simulated. `--live` requests one model-generated plan using
the same bounded serving adapter described in [04-assistant](../04-assistant/README.md).
The dispatcher still validates the plan and executes at most one local tool.

| Tool | Arguments | Result |
| --- | --- | --- |
| appointment_summary | Exactly an empty object. | Accepted local fixture counts: FAC01/FAC02/FAC03 = 1. |
| search_policies | Exactly query, a bounded string. | At most two approved/effective policy documents with source metadata. |

Unknown tools, extra/wrong arguments, duplicate JSON keys and malformed plans
fail before tool execution. The cancellation request is refused. Limited phrase
guards are demonstrations; hard dispatch limits still expose no write, arbitrary
SQL, shell, patient lookup, score disclosure, contact or clinical action.

The rescheduling-notice question must route to policy evidence rather than counts.
Tests include permitted reads, clinical/write refusals, malformed/unknown plans
and fake-model errors. Neither local nor live planning queries a Databricks table;
the summary recalculates from the same appointments.csv as the pipeline.

For an actual application, separately design caller/workload authorization,
auditing, source access, content evaluation, rate/time/cost limits, recovery and
human release authority. The repository deploys no MCP server, multi-agent
orchestrator or clinical workflow. These are distinct extension decisions.
