# A bounded read-only agent exercise

Local mode simulates one tool plan so dispatcher behavior can be checked without
a model. --live asks the approved model for one JSON plan. Only signup_summary
with no arguments, or search_policies with one bounded query, is accepted.

There is one model-planning call and at most one tool call, no loop, no shell,
no arbitrary SQL, no write tool, and no generated final interpretation after
the tool result. Wrong types, extra arguments, duplicate JSON keys and unknown tools fail closed.
The returned tool evidence is visible in JSON. This does not establish planning
quality; a model can still choose an irrelevant permitted read tool.

A small phrase check refuses direct requests such as "Delete customer records."
It allows read questions such as "What is the billing email?" This convenience
check is not the access boundary: every plan must still pass the exact dispatcher
contract, and the dispatcher exposes no write operation.

Use the same live environment settings as the assistant. For real data, add
user/workload identity design, actual permissions, audit, usage controls and
evaluation before deployment. Synthetic fixtures deliberately avoid implying
that app access grants access to arbitrary enterprise data.

