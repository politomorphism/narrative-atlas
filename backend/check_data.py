import json
from collections import Counter, defaultdict
from pathlib import Path

DATA_FILE = Path.home() / "data" / "raw" / "interpellations_term8_texts.json"


def date_range(items):
    dates = sorted(d for d in (item.get("date") for item in items) if d)
    if not dates:
        return None, None
    return dates[0], dates[-1]


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    print("=== Narrative Atlas data check ===")
    print("File:", DATA_FILE)
    print("Total records:", len(data))
    print()

    fields = Counter()
    for item in data:
        fields.update(item.keys())
    print("Fields and how many records have them:")
    for name, count in fields.most_common():
        print("  " + name + ": " + str(count))
    print()

    # 1. Duplicates
    exact = Counter(
        json.dumps(item, sort_keys=True, ensure_ascii=False) for item in data
    )
    exact_extra = sum(count - 1 for count in exact.values() if count > 1)

    content = Counter(
        (item.get("date"), item.get("mp_id"), item.get("text")) for item in data
    )
    content_extra = sum(count - 1 for count in content.values() if count > 1)

    ids = Counter((item.get("term"), item.get("num")) for item in data)
    id_repeats = sum(1 for count in ids.values() if count > 1)

    print("--- Duplicates ---")
    print("Extra copies of fully identical records:", exact_extra)
    print("Extra copies with same date, MP and text:", content_extra)
    print("(term, num) pairs that appear more than once:", id_repeats)
    shown = 0
    for key, count in content.items():
        if count > 1 and shown < 3:
            print(
                "  Example ("
                + str(count)
                + "x): "
                + str(key[0])
                + ", MP "
                + str(key[1])
                + ", "
                + str(key[2])[:80]
            )
            shown += 1
    print()

    # 2. UNKNOWN party
    mp_parties = defaultdict(Counter)
    for item in data:
        mp_parties[item.get("mp_id")][item.get("party") or "UNKNOWN"] += 1

    unknown_items = [
        item for item in data if (item.get("party") or "UNKNOWN") == "UNKNOWN"
    ]
    unknown_mps = {item.get("mp_id") for item in unknown_items}

    recoverable_mps = set()
    ambiguous_mps = set()
    no_known_mps = set()
    for mp in unknown_mps:
        known = [p for p in mp_parties[mp] if p != "UNKNOWN"]
        if len(known) == 1:
            recoverable_mps.add(mp)
        elif len(known) > 1:
            ambiguous_mps.add(mp)
        else:
            no_known_mps.add(mp)

    recoverable_records = sum(
        1 for item in unknown_items if item.get("mp_id") in recoverable_mps
    )

    switchers = [
        mp
        for mp, parties in mp_parties.items()
        if len([p for p in parties if p != "UNKNOWN"]) > 1
    ]

    print("--- UNKNOWN party ---")
    print("Records with UNKNOWN party:", len(unknown_items))
    print("Distinct MPs behind them:", len(unknown_mps))
    print(
        "MPs with exactly one known party elsewhere (party can be filled in):",
        len(recoverable_mps),
        "-> records:",
        recoverable_records,
    )
    print("MPs with several known parties (ambiguous):", len(ambiguous_mps))
    print("MPs with no known party at all:", len(no_known_mps))
    print("MPs who appear under more than one known party:", len(switchers))
    print()

    # 3. KO versus PO-KO
    ko = [item for item in data if item.get("party") == "KO"]
    po_ko = [item for item in data if item.get("party") == "PO-KO"]
    ko_mps = {item.get("mp_id") for item in ko}
    po_ko_mps = {item.get("mp_id") for item in po_ko}

    print("--- KO versus PO-KO ---")
    print("KO records:", len(ko), "dates:", date_range(ko))
    print("PO-KO records:", len(po_ko), "dates:", date_range(po_ko))
    print("MPs in KO:", len(ko_mps), "MPs in PO-KO:", len(po_ko_mps))
    print("MPs appearing under both names:", len(ko_mps & po_ko_mps))
    print()

    # 4. Text length
    word_counts = sorted(
        item.get("word_count") for item in data if isinstance(item.get("word_count"), int)
    )
    if word_counts:
        print("--- Text length (words) ---")
        print("Shortest:", word_counts[0])
        print("Median:", word_counts[len(word_counts) // 2])
        print("Longest:", word_counts[-1])


if __name__ == "__main__":
    main()

# end of file
