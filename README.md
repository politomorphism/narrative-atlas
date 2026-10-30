# Narrative Atlas

Political and media intelligence platform for narrative discovery, semantic analysis and monitoring.

Narrative Atlas is a rebuild of PACES, a political media monitoring SaaS, designed from scratch. The guiding idea is that an analysis is only worth as much as you can verify it: every cleaning step in this project is counted, labelled and visible, so a reader can see exactly where a number comes from.

**Status: work in progress (v0.5).** The first dataset and its explorer work today. Full-text collection and semantic analysis of recurring political narratives are the next stage and are not implemented yet.

## What works today

The first dataset is **34,043 interpellations from the 8th term of the Polish Sejm (2015-2019)**: written questions that members of parliament address to the government. The data is cleaned, deduplicated and linked to parties. You can browse it in a web interface with:

- a filterable table (party, free-text search, option to hide repeated interpellations) with paging;
- a quarterly timeline chart that follows the party and repeat filters;
- a data-quality panel that states how many records were repeated and where each party label came from.

## How the data is made verifiable

Raw political data is messy, and silent fixes hide errors. Narrative Atlas applies each fix visibly:

- **Repeats.** Records with the same date, MP and text are treated as repeats of one interpellation. Each record carries `repeat_count` and `is_repeat`, and the interface can hide repeats instead of deleting them.
- **Party resolution.** Where the source record has no party, it is filled in from the Sejm's own MP list. Every record carries `party_source` with one of `data`, `sejm_list`, `merged_label` or `unresolved`, and the table shows that label next to the party.
- **Renamed clubs.** The label `KO` is merged into `PO-KO`, the name the club later took, and this is recorded as `merged_label`, not hidden.
- **Audit scripts.** `backend/check_data.py` reports duplicates, unknown parties and text length. `backend/compare_parties.py` compares the party in the data with the Sejm club of each MP and writes a report.

## Project layout

```
backend/
  app/main.py          FastAPI application (the API)
  check_data.py        data audit: duplicates, unknown parties, text length
  compare_parties.py   data party versus Sejm club report
  requirements.txt
frontend/              React + Vite interface
```

## Data

The data files are not stored in this repository. The backend expects two JSON files, by default in `~/data/raw/`:

| File | Content |
| --- | --- |
| `interpellations_term8_texts.json` | A list of interpellation records (fields used include `term`, `num`, `date`, `year`, `mp_id`, `party`, `text`, `word_count`) |
| `sejm_term8_mps.json` | A list of MPs (fields used include `id`, `club`, `firstLastName`) |

The source is the Sejm's public API: <https://api.sejm.gov.pl/>. The script that downloads and assembles these two files is not in this repository yet. Until it is added, you need to provide files with the structure above.

You can put the files anywhere by setting two environment variables:

```
NARRATIVE_ATLAS_INTERPELLATIONS=/path/to/interpellations_term8_texts.json
NARRATIVE_ATLAS_SEJM_MPS=/path/to/sejm_term8_mps.json
```

If the MP list is missing, the API still runs, but missing parties stay `unresolved` and the interface shows a warning.

## Run it locally

You need Python 3.10 or newer and Node.js.

**Backend** (from the repository root):

```
cd backend
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API starts at `http://127.0.0.1:8000`, with interactive documentation at `http://127.0.0.1:8000/docs`.

**Frontend** (in a second terminal, from the repository root):

```
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## API

| Endpoint | Returns |
| --- | --- |
| `GET /health` | `{"status": "ok"}` |
| `GET /data-quality` | Record counts, repeats, and how many parties came from the data, the Sejm list, merged labels, or are unresolved |
| `GET /parties` | Resolved parties with record counts |
| `GET /timeline` | Interpellations per calendar quarter. Parameters: `party`, `hide_repeats` |
| `GET /interpellations` | Paged records. Parameters: `party`, `year`, `q` (text search), `hide_repeats`, `limit` (1-500), `offset` |

## Known limits

- The frontend currently calls the API at `http://127.0.0.1:8000`, and the backend allows cross-origin requests only from `localhost:5173`. A hosted deployment needs both made configurable.
- The backend loads the whole dataset into memory and filters it in Python on each request. This is fine for tens of thousands of records and is not meant for much larger collections.
- Text search is a plain substring match, not semantic search.
- Interpellation texts are public parliamentary documents, but they can mention private individuals. Review a sample before republishing full texts.

## Roadmap

1. A reproducible data download script.
2. Full-text collection beyond the first dataset.
3. Semantic analysis: embeddings, clustering and tracking of recurring narratives.
4. A methodology page that records, for each analysis, its sources, model, prompt version and limits.
5. An evaluation set of hand-labelled documents to measure how well automated narrative detection agrees with an expert.

## Author

Serban Gabriel Florin, [Politomorphism Research Project](https://github.com/politomorphism).
