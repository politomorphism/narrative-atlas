import json
import os
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

RAW_DIR = Path.home() / "data" / "raw"

DATA_FILE = Path(
    os.environ.get(
        "NARRATIVE_ATLAS_INTERPELLATIONS",
        str(RAW_DIR / "interpellations_term8_texts.json"),
    )
)

SEJM_MPS_FILE = Path(
    os.environ.get(
        "NARRATIVE_ATLAS_SEJM_MPS",
        str(RAW_DIR / "sejm_term8_mps.json"),
    )
)

# Sejm club names (upper case) mapped to the party spelling used in the interpellations data.
# "PO" is the club's name before it was renamed "PO-KO" (late 2018).
CLUB_TO_PARTY = {
    "PIS": "PIS",
    "PO-KO": "PO-KO",
    "PO": "PO-KO",
    "KUKIZ15": "KUKIZ",
    "NIEZ.": "niez.",
    "UPR": "UPR",
    "PSL-KP": "PSL-KP",
    "KONFEDERACJA": "Konfederacja",
    "PP": "PP",
    "TERAZ!": "TERAZ!",
    "WIS": "WIS",
    "PSL-UED": "PSL-UED",
}

app = FastAPI(
    title="Narrative Atlas API",
    description="Political and media intelligence platform for narrative discovery, semantic analysis and monitoring.",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def repeat_key(item: dict) -> tuple:
    # Records with the same date, MP and text are treated as repeats of one interpellation.
    return (item.get("date"), item.get("mp_id"), item.get("text"))


@lru_cache(maxsize=1)
def load_sejm_clubs() -> dict:
    # Maps Sejm MP id to club. Returns an empty dict if the file is missing or invalid.
    try:
        with open(SEJM_MPS_FILE, encoding="utf-8") as f:
            mps = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    clubs = {}
    for mp in mps:
        club = mp.get("club")
        if mp.get("id") is not None and club:
            clubs[mp["id"]] = club
    return clubs


def resolve_party(item: dict, clubs: dict) -> tuple:
    party = item.get("party")
    if party and party != "UNKNOWN":
        if party == "KO":
            # "KO" is an earlier label for the club later named "PO-KO".
            return "PO-KO", "merged_label"
        return party, "data"
    club = clubs.get(to_int(item.get("mp_id")))
    if club:
        return CLUB_TO_PARTY.get(str(club).strip().upper(), club), "sejm_list"
    return "UNKNOWN", "unresolved"


@lru_cache(maxsize=1)
def load_interpellations() -> list[dict]:
    with open(DATA_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise ValueError("The data file must contain a list of objects.")

    clubs = load_sejm_clubs()
    group_sizes = Counter(repeat_key(item) for item in raw)
    seen = set()
    data = []
    for item in raw:
        key = repeat_key(item)
        record = dict(item)
        record["repeat_count"] = group_sizes[key]
        record["is_repeat"] = key in seen
        seen.add(key)
        resolved, source = resolve_party(item, clubs)
        record["party_resolved"] = resolved
        record["party_source"] = source
        data.append(record)
    return data


def get_data() -> list[dict]:
    try:
        return load_interpellations()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Data file not found: " + str(DATA_FILE),
        )
    except (ValueError, json.JSONDecodeError) as err:
        raise HTTPException(status_code=500, detail="Invalid data file: " + str(err))


@app.get("/")
def root():
    return {"project": "Narrative Atlas", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/data-quality")
def data_quality():
    data = get_data()
    total = len(data)
    repeats = sum(1 for item in data if item["is_repeat"])
    sources = Counter(item["party_source"] for item in data)
    unresolved = [item for item in data if item["party_source"] == "unresolved"]
    return {
        "total_records": total,
        "repeat_records": repeats,
        "unique_records": total - repeats,
        "sejm_list_loaded": len(load_sejm_clubs()) > 0,
        "party_from_data": sources.get("data", 0),
        "party_from_sejm_list": sources.get("sejm_list", 0),
        "party_from_merged_label": sources.get("merged_label", 0),
        "party_unresolved_records": len(unresolved),
        "party_unresolved_mps": len({item.get("mp_id") for item in unresolved}),
    }


@app.get("/parties")
def parties():
    data = get_data()
    counts = Counter(item["party_resolved"] for item in data)
    return [
        {"party": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ]


@app.get("/interpellations")
def interpellations(
    party: Optional[str] = None,
    year: Optional[int] = None,
    q: Optional[str] = None,
    hide_repeats: bool = False,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    data = get_data()
    items = data

    if party:
        items = [item for item in items if item["party_resolved"] == party]
    if year is not None:
        items = [item for item in items if item.get("year") == year]
    if q:
        needle = q.lower()
        items = [item for item in items if needle in (item.get("text") or "").lower()]
    if hide_repeats:
        items = [item for item in items if not item["is_repeat"]]

    total = len(items)
    page = items[offset : offset + limit]

    result = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": page,
    }
    return result


# end of file

