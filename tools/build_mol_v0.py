r"""
K16 — B04-lite molecule registry v0 (v4.0 AH9 / AQ2) for every target touched by DEL-1.

    .venv/bin/python tools/build_mol_v0.py

* Single compounds are resolved by name via PubChem PUG-REST (H2 approved, DEC-019):
  CID, InChIKey (identity key, master prompt H1), canonical/isomeric SMILES, formula.
  Responses are cached under data/raw/pubchem/ with SNAP- hashes; ≤1 request/s.
* Nutrient GROUPS (folate, vitamin B-6, vitamin A RE, …) get NO structure — their members
  are listed and resolved individually. ELEMENTS (Ca, Fe, …) are recorded as elements;
  molecular fingerprints are not meaningful for them.
* RDKit: Morgan (r=2, 2048 bits) + MACCS fingerprints and five descriptors per molecule.
* IMAP- rows join each evidence target (USDA nutrient code) to MOL- ids with the
  relation type (IS / GROUP_MEMBER / ELEMENT).
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import pathlib
import sys
import time
import urllib.parse

import requests
from rdkit import Chem, DataStructs
from rdkit.Chem import Descriptors, MACCSkeys, rdFingerprintGenerator, rdMolDescriptors

MORGAN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/pubchem"
OUT = ROOT / "ledgers/molecules"
UA = {"User-Agent": "CulinaryState-research/0.1 (parvgoyal08@gmail.com)"}
PROPS = "InChIKey,SMILES,ConnectivitySMILES,MolecularFormula,MolecularWeight,IUPACName"

# USDA nutrient code → (kind, members)  kind: COMPOUND | GROUP | ELEMENT
TARGETS = {
    "221": ("COMPOUND", ["ethanol"]),
    "301": ("ELEMENT", ["Ca"]), "303": ("ELEMENT", ["Fe"]), "304": ("ELEMENT", ["Mg"]),
    "305": ("ELEMENT", ["P"]), "306": ("ELEMENT", ["K"]), "307": ("ELEMENT", ["Na"]),
    "309": ("ELEMENT", ["Zn"]), "312": ("ELEMENT", ["Cu"]),
    "318": ("GROUP", ["retinol", "beta-carotene", "alpha-carotene", "beta-cryptoxanthin"]),  # vitamin A, IU
    "392": ("GROUP", ["retinol", "beta-carotene", "alpha-carotene", "beta-cryptoxanthin"]),  # vitamin A, RE
    "321": ("COMPOUND", ["beta-carotene"]), "322": ("COMPOUND", ["alpha-carotene"]),
    "334": ("COMPOUND", ["beta-cryptoxanthin"]), "337": ("COMPOUND", ["lycopene"]),
    "338": ("GROUP", ["lutein", "zeaxanthin"]),
    "401": ("GROUP", ["ascorbic acid", "dehydroascorbic acid"]),   # "total ascorbic acid"
    "404": ("COMPOUND", ["thiamine"]), "405": ("COMPOUND", ["riboflavin"]),
    "406": ("GROUP", ["nicotinic acid", "nicotinamide"]),
    "415": ("GROUP", ["pyridoxine", "pyridoxal", "pyridoxamine"]),
    "417": ("GROUP", ["folic acid", "5-methyltetrahydrofolate"]),   # folate, total
    "418": ("GROUP", ["cyanocobalamin", "hydroxocobalamin", "methylcobalamin", "adenosylcobalamin"]),
    "421": ("GROUP", ["choline", "phosphocholine", "glycerophosphocholine"]),   # choline, total
    "431": ("COMPOUND", ["folic acid"]),
    "432": ("GROUP", ["5-methyltetrahydrofolate", "tetrahydrofolic acid"]),    # food folate
}
ELEMENT_NAME = {"Ca": "calcium", "Fe": "iron", "Mg": "magnesium", "P": "phosphorus", "K": "potassium",
                "Na": "sodium", "Zn": "zinc", "Cu": "copper"}


def fetch(name: str, snaps: list) -> dict | None:
    RAW.mkdir(parents=True, exist_ok=True)
    cache = RAW / f"{name.replace(' ', '_')}.json"
    if not cache.exists():
        url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
               f"{urllib.parse.quote(name)}/property/{PROPS}/JSON")
        r = requests.get(url, headers=UA, timeout=30)
        time.sleep(1.0)
        cache.write_bytes(r.content if r.status_code == 200 else json.dumps(
            {"status": r.status_code, "body": r.text[:200]}).encode())
        snaps.append({"name": name, "url": url, "status": r.status_code,
                      "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                      "sha256": hashlib.sha256(cache.read_bytes()).hexdigest(), "path": str(cache.relative_to(ROOT))})
    d = json.loads(cache.read_text())
    props = d.get("PropertyTable", {}).get("Properties")
    return props[0] if props else None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    snaps: list = []
    names = sorted({m for k, (kind, ms) in TARGETS.items() if kind != "ELEMENT" for m in ms})
    mols, failures = {}, []
    for n in names:
        p = fetch(n, snaps)
        if not p:
            failures.append(n)
            continue
        smi = p.get("IsomericSMILES") or p.get("SMILES") or p.get("CanonicalSMILES") or p.get("ConnectivitySMILES")
        m = Chem.MolFromSmiles(smi) if smi else None
        rec = {"mol_id": f"MOL-{p['InChIKey']}", "name": n, "cid": p["CID"], "inchikey": p["InChIKey"],
               "smiles": smi, "formula": p.get("MolecularFormula"), "mw_pubchem": p.get("MolecularWeight"),
               "rdkit_ok": m is not None}
        if m is not None:
            rec.update({"mw": round(Descriptors.MolWt(m), 3), "logp": round(Descriptors.MolLogP(m), 3),
                        "tpsa": round(rdMolDescriptors.CalcTPSA(m), 3), "hbd": rdMolDescriptors.CalcNumHBD(m),
                        "hba": rdMolDescriptors.CalcNumHBA(m),
                        "morgan2_2048": MORGAN.GetFingerprint(m).ToBitString(),
                        "maccs": MACCSkeys.GenMACCSKeys(m).ToBitString()})
            # identity check: RDKit InChIKey from the PubChem SMILES must equal PubChem's InChIKey
            rec["inchikey_roundtrip_ok"] = Chem.MolToInchiKey(m) == p["InChIKey"]
        mols[n] = rec
    with (OUT / "mol_v0.jsonl").open("w") as fh:
        for n in names:
            if n in mols:
                fh.write(json.dumps(mols[n], sort_keys=True) + "\n")
    with (OUT / "imap_v0.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["imap_id", "target_code", "kind", "member", "mol_id", "relation", "provenance"])
        k = 0
        for code, (kind, members) in TARGETS.items():
            for mem in members:
                k += 1
                if kind == "ELEMENT":
                    w.writerow([f"IMAP-{k:04d}", f"USDA-Nutr-{code}", kind, ELEMENT_NAME[mem], f"ELEM-{mem}",
                                "ELEMENT", "DERIVED_DETERMINISTIC"])
                else:
                    mol = mols.get(mem)
                    w.writerow([f"IMAP-{k:04d}", f"USDA-Nutr-{code}", kind, mem,
                                mol["mol_id"] if mol else "UNRESOLVED",
                                "IS" if kind == "COMPOUND" else "GROUP_MEMBER", "EXTERNAL_VERIFIED" if mol else "UNKNOWN"])
    snap_file = ROOT / "ledgers/snapshots/pubchem_snapshots.jsonl"
    with snap_file.open("a") as fh:
        for s in snaps:
            fh.write(json.dumps(s) + "\n")
    # smoke: Tanimoto between related molecules (B03-lite fingerprint smoke, AH8)
    def tani(a, b):
        fa = DataStructs.CreateFromBitString(mols[a]["morgan2_2048"])
        fb = DataStructs.CreateFromBitString(mols[b]["morgan2_2048"])
        return round(DataStructs.TanimotoSimilarity(fa, fb), 3)
    pairs = [("alpha-carotene", "beta-carotene"), ("lutein", "zeaxanthin"), ("pyridoxal", "pyridoxine"),
             ("ascorbic acid", "ethanol")]
    sims = {f"{a}~{b}": tani(a, b) for a, b in pairs if a in mols and b in mols and mols[a]["rdkit_ok"] and mols[b]["rdkit_ok"]}
    report = {"names": len(names), "resolved": len(mols), "failures": failures,
              "rdkit_parsed": sum(m["rdkit_ok"] for m in mols.values()),
              "inchikey_roundtrip_ok": sum(bool(m.get("inchikey_roundtrip_ok")) for m in mols.values()),
              "new_requests": len(snaps), "tanimoto_smoke": sims}
    (OUT / "mol_v0.report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
