r"""
P2 — the project-wide ID registry: every prefix, its pattern, the ledger that OWNS it (the only place
an id of that prefix may be defined), and what it identifies. IDs are stable: once defined they are
never reused for a different thing (audited by tools/audit_ids.py).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Prefix:
    prefix: str
    pattern: str
    owner: str          # ledger/registry that defines ids of this prefix
    meaning: str


SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
PREFIXES = {p.prefix: p for p in [
    # sources and provenance
    Prefix("SRC", r"SRC-(\d{4}|[A-Z0-9]+(?:-[A-Z0-9]+)*)", "registry/datasets.csv + snapshot ledgers", "a source (database, paper, authority)"),
    Prefix("SNAP", r"SNAP-(\d{4}|[A-Z0-9]+-\d{4})", "ledgers/snapshots/*", "one retrieval of a source, pinned by sha256"),
    Prefix("API", r"API-[A-Z0-9]+(?:-[A-Z0-9]+)*", "docs/SOURCE_ACCESS.md", "an API access route and its terms"),
    Prefix("STUDY", r"STUDY-\d{6}", "ledgers/literature/studies_v*.csv", "one primary study (paper/experiment)"),
    Prefix("MEAS", r"MEAS-\d{6}", "ledgers/literature/measurements_v*.csv", "a measurement protocol within a study"),
    # food identity
    Prefix("ING", r"ING-" + SLUG, "ledgers/ingredients/ing_v*.csv", "a canonical food concept"),
    Prefix("ALIAS", r"ALIAS-\d{6}", "ledgers/ingredients/alias_v*.csv", "a surface name → ING link"),
    Prefix("MOL", r"MOL-[A-Z]{14}-[A-Z]{10}-[A-Z]", "ledgers/molecules/mol_v*.jsonl", "a molecule, keyed by InChIKey"),
    Prefix("MOLCLASS", r"MOLCLASS-" + SLUG, "ledgers/molecules/molclass_v*.csv", "a compound class / assay endpoint (no structure)"),
    Prefix("IMAP", r"IMAP-(\d{4}|IM-\d{6})", "ledgers/molecules/imap_v*.csv", "target→molecule identity (NNNN) or ingredient↔molecule relation (IM-)"),
    # process and conditions
    Prefix("PROC", r"PROC-" + SLUG, "ledgers/process/proc_v*.csv", "a culinary/food process"),
    Prefix("TOOL", r"TOOL-" + SLUG, "ledgers/tools/tool_v*.csv", "a tool/utensil/appliance"),
    Prefix("COND", r"COND-\d{6}", "ledgers/evidence/conditions_v*.csv", "one condition value (axis, status, value)"),
    Prefix("SVAR", r"SVAR-" + SLUG, "ledgers/state/svar_v*.csv", "a state variable (phase, colour, moisture…)"),
    # quantities
    Prefix("UNIT", r"UNIT-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", "ledgers/units/unit_map_v*.csv", "a unit"),
    Prefix("QNT", r"QNT-\d{6}", "parser output", "a parsed quantity expression"),
    Prefix("POR", r"POR-\d{6}", "ledgers/units/por_v*.csv", "a sourced portion/gram-weight record"),
    Prefix("ALLOC", r"ALLOC-\d{6}", "state-engine output", "an allocation of a quantity across split/reserve outputs"),
    # recipe state
    Prefix("INST", r"INST-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", "recipe adapters", "an instruction step"),
    Prefix("EVT", r"EVT-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", "state-engine event log", "an engine event"),
    Prefix("ENTITY", r"ENTITY-[A-Za-z0-9]+(?:-[A-Za-z0-9_]+)*", "state-engine event log", "a physical lot in one recipe/session"),
    Prefix("STATE", r"STATE-ENTITY-[A-Za-z0-9_-]+-v\d+", "state-engine (derived)", "one version of a lot's state"),
    Prefix("REF", r"REF-\d{6}", "gold annotations", "a coreference mention → entity link"),
    Prefix("GRAPH", r"GRAPH-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", "state-engine (derived)", "a replayed recipe/session graph (digest-pinned)"),
    # evidence and safety
    Prefix("EVD", r"EVD-\d{6}", "ledgers/evidence/evidence_v*.jsonl", "one process-effect evidence row"),
    Prefix("RXN", r"RXN-\d{6}", "ledgers/evidence/reactions_v*.jsonl", "an evidenced transformation relation"),
    Prefix("WARN", r"WARN-\d{4}", "ledgers/authority/warnings_v*.csv", "an authority-backed warning"),
    Prefix("ALLERGEN", r"ALLERGEN-\d{2}", "ledgers/authority/allergen_v*.csv", "an FSSAI allergen class"),
    Prefix("LITC", r"LITC[12]?-\d{6}", "ledgers/literature/candidates_*.csv", "a verbatim literature table cell (candidate, not evidence)"),
    Prefix("CELL", r"CELL-\d{5}", "research/cells/priority_cells_v*.csv", "a research-agenda cell"),
    # ML / experiments / governance
    Prefix("MODEL", r"MODEL-" + SLUG, "registry/models.csv", "a model artefact (version/hash pinned)"),
    Prefix("DATASET", r"DATASET-" + SLUG, "registry/datasets_v*.csv", "a dataset release (sha pinned)"),
    Prefix("SPLIT", r"SPLIT-" + SLUG, "registry/splits.csv", "a frozen split assignment"),
    Prefix("EXP", r"EXP-" + SLUG, "registry/experiments.csv", "an experiment run family"),
    Prefix("GATE", r"GATE-[A-Za-z0-9-]+", "registry/gates.csv", "a gate"),
    Prefix("RQ", r"RQ-?[A-Za-z0-9-]+", "registry/experiments.csv", "a research question"),
    Prefix("RS", r"RS-\d{2}-(\d{2}|NEW-\d{2})", "registry/research_spawns.csv", "a research spawn"),
    Prefix("CLM", r"CLM-\d{4}", "registry/claims.csv", "a claim (needs experiment + artefact hash + gate verdict)"),
]}
_RX = {k: re.compile(r"^" + v.pattern + r"$") for k, v in PREFIXES.items()}
_HEAD = re.compile(r"^([A-Z]+[12]?)-")


def prefix_of(identifier: str) -> str:
    """Return the registered prefix of an id; raise ValueError if unknown or malformed."""
    m = _HEAD.match(identifier or "")
    if not m:
        raise ValueError(f"not an id: {identifier!r}")
    p = m.group(1)
    if p == "LITC1" or p == "LITC2":
        p = "LITC"
    if p not in PREFIXES:
        raise ValueError(f"unknown prefix {p!r} in {identifier!r}")
    if not _RX[p].match(identifier):
        raise ValueError(f"malformed {p} id {identifier!r} (expected {PREFIXES[p].pattern})")
    return p


def is_valid(identifier: str, expected: str | None = None) -> bool:
    """True iff the id is well-formed (and, if given, has the expected prefix)."""
    try:
        p = prefix_of(identifier)
    except ValueError:
        return False
    return expected is None or p == expected
