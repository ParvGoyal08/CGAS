r"""
CulinaryState-RAG demo (P11). Run from the project folder:

    .venv/bin/streamlit run app/demo.py

Renders src/culinarystate/demo/scenarios.py. Default verbaliser is the deterministic template;
"local Ollama" uses qwen2.5:3b on this machine. Claude API is not reachable from the demo (H3).
"""
from __future__ import annotations

import json
import pathlib
import sys

import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from culinarystate.demo.scenarios import SCENARIOS, TemplateLLM, cited_ok  # noqa: E402
from culinarystate.llm.client import OllamaBackend  # noqa: E402

st.set_page_config(page_title="CulinaryState-RAG demo", layout="wide")
st.title("CulinaryState-RAG — course demo")
st.caption("Evidence: USDA Retention Factors R6 (CC0). Allergens: FSSAI Labelling & Display Regulations. "
           "Scenario inputs are scripted examples, not benchmark items.")

verb = st.sidebar.radio("Verbaliser", ["template (deterministic)", "local Ollama (qwen2.5:3b)"])
llm = TemplateLLM() if verb.startswith("template") else OllamaBackend()
labels = [f"{sid} · {t} — {q}" for sid, t, q, _ in SCENARIOS]
pick = st.sidebar.radio("Scenario", labels)
sid, task, question, fn = SCENARIOS[labels.index(pick)]

st.subheader(question)
st.write(f"**Task type:** {task}")
with st.spinner("running…"):
    r = fn(llm)
c1, c2 = st.columns([1, 3])
c1.metric("Decision mode", r["mode"])
if r.get("evidence_class"):
    c1.metric("Evidence class", r["evidence_class"])
c1.write("Citations valid ✅" if cited_ok(r) else "Citation check FAILED ❌")
ans = r["answer"]
c2.markdown("**Answer**")
c2.write(ans if isinstance(ans, str) else ans)
if r.get("note"):
    c2.info(r["note"])
if r.get("detail"):
    with st.expander("Inspect (state / feasibility / conversions)"):
        st.code(json.dumps(r["detail"], indent=2, default=str), language="json")
