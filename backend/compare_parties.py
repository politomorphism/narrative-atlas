import json
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path.home() / "data"
INTERPELLATIONS = DATA_DIR / "raw" / "interpellations_term8_texts.json"
SEJM_MPS = DATA_DIR / "raw" / "sejm_term8_mps.json"
REPORT = DATA_DIR / "party_report.txt"

# The two files spell some party names differently; map them to one form for comparison.
CLUB_ALIASES = {"KUKIZ15": "KUKIZ"}


def normalize(name):
    if not name:
        return "NONE"
    key = str(name).strip().upper()
    return CLUB_ALIASES.get(key, key)


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def main():
    with open(INTERPELLATIONS, encoding="utf-8") as f:
        data = json.load(f)
    with open(SEJM_MPS, encoding="utf-8") as f:
        mps_list = json.load(f)

    mps = {m["id"]: m for m in mps_list}
    out = []

    def line(text=""):
        out.append(text)

    # Annotate every record with the normalized data party and the Sejm club
    records = []
    for item in data:
        mp_id = to_int(item.get("mp_id"))
        mp = mps.get(mp_id)
        records.append(
            {
                "mp_id": mp_id,
                "date": item.get("date"),
                "data_party": normalize(item.get("party")),
                "sejm_club": normalize(mp.get("club")) if mp else "NOT IN SEJM LIST",
                "name": mp.get("firstLastName") if mp else "?",
            }
        )

    line("=== Narrative Atlas: data party versus Sejm club ===")
    line("Records: " + str(len(records)))
    line("MPs in the Sejm list: " + str(len(mps)))
    line()

    # A. Records with a known party in the data
    known = [r for r in records if r["data_party"] != "UNKNOWN"]
    matches = sum(1 for r in known if r["data_party"] == r["sejm_club"])
    line("--- A. Records with a known party in the data ---")
    line("Known-party records: " + str(len(known)))
    line("Same party as the Sejm club: " + str(matches))
    line("Different: " + str(len(known) - matches))
    if known:
        line("Agreement: " + str(round(100 * matches / len(known), 1)) + " percent")
    line()
    line("Most common differences (data party -> Sejm club : records):")
    pairs = Counter(
        (r["data_party"], r["sejm_club"]) for r in known if r["data_party"] != r["sejm_club"]
    )
    for (a, b), count in pairs.most_common(15):
        line("  " + a + " -> " + b + " : " + str(count))
    line()

    per_mp = defaultdict(lambda: {"parties": Counter(), "club": "", "name": "", "diff": 0})
    for r in known:
        entry = per_mp[r["mp_id"]]
        entry["parties"][r["data_party"]] += 1
        entry["club"] = r["sejm_club"]
        entry["name"] = r["name"]
        if r["data_party"] != r["sejm_club"]:
            entry["diff"] += 1
    differing = [(mp_id, e) for mp_id, e in per_mp.items() if e["diff"] > 0]
    differing.sort(key=lambda pair: -pair[1]["diff"])
    line("MPs whose data party differs from the Sejm club: " + str(len(differing)))
    for mp_id, e in differing[:40]:
        parties = ", ".join(p + " x" + str(c) for p, c in e["parties"].most_common())
        line(
            "  MP "
            + str(mp_id)
            + " "
            + str(e["name"])
            + " | data: "
            + parties
            + " | Sejm: "
            + str(e["club"])
        )
    line()

    # B. Records with UNKNOWN party
    unknown = [r for r in records if r["data_party"] == "UNKNOWN"]
    line("--- B. Records with UNKNOWN party ---")
    line("Records: " + str(len(unknown)))
    by_mp = defaultdict(list)
    for r in unknown:
        by_mp[r["mp_id"]].append(r)
    line("MPs: " + str(len(by_mp)))
    club_records = Counter()
    club_mps = Counter()
    for mp_id, rows in by_mp.items():
        club_records[rows[0]["sejm_club"]] += len(rows)
        club_mps[rows[0]["sejm_club"]] += 1
    line()
    line("Sejm club of these MPs (MPs / records):")
    for club, count in club_records.most_common():
        line("  " + club + " : " + str(club_mps[club]) + " MPs / " + str(count) + " records")
    line()
    line("Each UNKNOWN MP (id, name, Sejm club, records):")
    for mp_id, rows in sorted(by_mp.items(), key=lambda pair: -len(pair[1])):
        line(
            "  "
            + str(mp_id)
            + " | "
            + str(rows[0]["name"])
            + " | "
            + rows[0]["sejm_club"]
            + " | "
            + str(len(rows))
        )
    line()

    # C. The three MPs behind the KO label
    ko = [r for r in records if r["data_party"] == "KO"]
    line("--- C. Records labelled KO ---")
    line("Records: " + str(len(ko)))
    ko_by_mp = defaultdict(list)
    for r in ko:
        ko_by_mp[r["mp_id"]].append(r)
    for mp_id, rows in ko_by_mp.items():
        dates = sorted(r["date"] for r in rows if r["date"])
        line(
            "  MP "
            + str(mp_id)
            + " | "
            + str(rows[0]["name"])
            + " | Sejm club: "
            + rows[0]["sejm_club"]
            + " | records: "
            + str(len(rows))
            + " | "
            + (dates[0] + " to " + dates[-1] if dates else "no dates")
        )
    line()
    line("# end of file")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print("Report written to " + str(REPORT))
    print("Known-party records: " + str(len(known)) + ", agreement with Sejm: " + str(matches))
    print("UNKNOWN records: " + str(len(unknown)) + ", UNKNOWN MPs: " + str(len(by_mp)))


if __name__ == "__main__":
    main()

# end of file