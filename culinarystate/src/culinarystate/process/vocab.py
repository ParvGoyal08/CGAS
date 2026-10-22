r"""
Raw cooking verb → canonical PROC- identifier (block B05, gate: every process
mention maps to an ID or to an explicit UNMAPPED that keeps the raw verb).

    vocab = ProcessVocabulary.load()
    vocab.resolve("Stirring")   → MAPPED      PROC-stir
    vocab.resolve("reduce")     → AMBIGUOUS   (PROC-reduce-liquid, PROC-adjust-heat)
    vocab.resolve("wok")        → NON_PROCESS term_class=TOOL
    vocab.resolve("julienne")   → UNMAPPED    raw kept, never guessed

Resolution never invents a mapping. AMBIGUOUS returns candidates only; choosing
one needs sentence context (an upstream parser or a human).
"""
from __future__ import annotations

import csv
import pathlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
LEDGER = ROOT / "ledgers" / "process"

MAPPED, AMBIGUOUS, NON_PROCESS, UNMAPPED = "MAPPED", "AMBIGUOUS", "NON_PROCESS", "UNMAPPED"


def normalise(raw: str) -> str:
    s = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9\- ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


@dataclass(frozen=True)
class Resolution:
    raw: str
    key: str
    status: str
    proc_id: Optional[str] = None
    term_class: Optional[str] = None
    candidates: tuple[str, ...] = ()
    note: str = ""


class ProcessVocabulary:
    def __init__(self, procs: dict[str, dict], term_map: dict[str, dict]):
        self.procs = procs
        self.term_map = term_map
        self._alias: dict[str, str] = {}
        for pid, r in procs.items():
            self._alias.setdefault(normalise(r["label"]), pid)
            self._alias.setdefault(normalise(pid[len("PROC-"):]), pid)
            for syn in filter(None, r["synonyms"].split("|")):
                # synonyms with a parenthetical sense, e.g. "tempering (chocolate)", are
                # sense labels, not bare aliases: only the full string is indexed
                self._alias.setdefault(normalise(syn), pid)

    @classmethod
    def load(cls, ledger_dir: pathlib.Path = LEDGER) -> "ProcessVocabulary":
        with (ledger_dir / "proc_v0.csv").open(encoding="utf-8") as fh:
            procs = {r["proc_id"]: r for r in csv.DictReader(fh)}
        with (ledger_dir / "recipedb_term_map_v0.csv").open(encoding="utf-8") as fh:
            term_map = {normalise(r["recipedb_term"]): r for r in csv.DictReader(fh)}
        return cls(procs, term_map)

    def resolve(self, raw: str) -> Resolution:
        key = normalise(raw)
        t = self.term_map.get(key)
        if t is not None:
            cls = t["term_class"]
            if cls in ("PROCESS", "INFLECTION", "SYNONYM"):
                return Resolution(raw, key, MAPPED, t["target_proc_id"], cls, note=t["senses_or_note"])
            if cls == "AMBIGUOUS":
                cands = tuple(dict.fromkeys(
                    f"PROC-{s}" for s in re.findall(r"→ ([a-z0-9-]+)", t["senses_or_note"])
                    if f"PROC-{s}" in self.procs))
                return Resolution(raw, key, AMBIGUOUS, None, cls, cands, t["senses_or_note"])
            return Resolution(raw, key, NON_PROCESS, t["target_proc_id"] or None, cls,
                              note=t["senses_or_note"])
        pid = self._alias.get(key)
        if pid is not None:
            return Resolution(raw, key, MAPPED, pid, "PROCESS_OR_SYNONYM")
        return Resolution(raw, key, UNMAPPED, note="no PROC- entry; raw verb kept for review")
