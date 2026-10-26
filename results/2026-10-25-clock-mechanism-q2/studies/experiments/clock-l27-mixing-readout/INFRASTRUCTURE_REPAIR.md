The first attempt passed archived L24 mixing reproduction and same-context
identity, but failed BEFORE intervention outcomes while attaching native timing
coordinates: arrays used h24/h27 keys and the template lookup added another h.
Attempt1 evidence is preserved under attempt1/. Parameter equality and GPU lease
release completed normally. No discovery or confirmation patch results existed.

run_local_v2.py changes only the conversion from array keys h24/h27 to state
indices 24/27. Original frozen run_local.py and frozen_sources.json are unchanged.
The bank, projection construction, intervention, metrics and selection gates are
unchanged. The incomplete native stage is rerun; no threshold or candidate changes.
