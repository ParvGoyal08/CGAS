# Pass 2 — events (DEL3-GOLD-v0 YAML)
Annotate the steps as a DEL3-GOLD-v0 YAML document (keys: gold_format, recipe_id, annotator, steps[step, text, events]).
Operations: CREATE, TRANSFORM, MERGE, SPLIT, RESERVE, DISCARD, RECOMBINE, TRANSFER, SET_FIELD, OBSERVE.
Rules: copy quantities verbatim into qty.raw; give unit/value only when written; ranges as lo/hi; never a midpoint;
never convert to grams; record time/temperature/endpoints only when written (endpoints go in `plan`); keep "or"
alternatives verbatim in `process`; every lot id is new and never reused. Return ONLY the YAML in a ```yaml block.
