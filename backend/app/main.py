import json
import os
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

DATA_FILE = Path(
    os.environ.get(
        "NARRATIVE_ATLAS_INTERPELLATIONS",
        str(Path.home() / "data" / "raw" / "interpellations_term8_texts.json"),
    )
)

app = FastAPI(
    title="Narrative Atlas API",
    description="Political and media intelligence platform for narrative discovery, semantic analysis and monitoring.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def load_interpellations() -> list[dict]:
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Fișierul de date trebuie să conțină o listă de obiecte.")
    return data


def get_data() -> list[dict]:
    try:
        return load_interpellations()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Fișierul de date nu a fost găsit: " + str(DATA_FILE),
        )
    except (ValueError, json.JSONDecodeError) as err:
        raise HTTPException(status_code=500, detail="Fișier de date invalid: " + str(err))


@app.get("/")
def root():
    return {"project": "Narrative Atlas", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/parties")
def parties():
    data = get_data()
    counts = Counter(item.get("party") or "necunoscut" for item in data)
    return [
        {"party": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ]


@app.get("/interpellations")
def interpellations(
    party: Optional[str] = None,
    year: Optional[int] = None,
    q: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    data = get_data()
    items = data

    if party:
        items = [item for item in items if (item.get("party") or "necunoscut") == party]
    if year is not None:
        items = [item for item in items if item.get("year") == year]
    if q:
        needle = q.lower()
        items = [item for item in items if needle in (item.get("text") or "").lower()]

    total = len(items)
    page = items[offset : offset + limit]

    result = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": page,
    }
    return result

