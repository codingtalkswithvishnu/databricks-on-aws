# A bounded read-only agent exercise

Local mode simulates one tool plan so dispatcher behavior can be checked without
a model. --live asks the approved model for one JSON plan. Only signup_summary
with no arguments, or search_policies with one bounded query, is accepted.

There is one model-planning call and at most one tool call, no loop, no shell,
no arbitrary SQL, no write tool, and no generated final interpretation after
the tool result. Wrong types, extra arguments and unknown tools fail closed.
The returned tool evidence is visible in JSON. This does not establish planning
quality; a model can still choose an irrelevant permitted read tool.

Use the same live environment settings as the assistant. For real data, add
user/workload identity design, actual permissions, audit, usage controls and
evaluation before deployment. Synthetic fixtures deliberately avoid implying
that app access grants access to arbitrary enterprise data.

