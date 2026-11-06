"""Stream-parse the BPI Challenge 2019 XES log (gzip) into two flat tables.

The XES file is 729 MB of XML when unzipped, so it's read element by element
instead of being loaded into memory at once.

    python src/parse_xes.py data/raw/BPI_Challenge_2019.xes.gz data/interim
"""
import csv
import gzip
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://www.xes-standard.org/}"
EVENT_KEYS = ["concept:name", "time:timestamp", "org:resource", "User", "Cumulative net worth (EUR)"]
CASE_KEYS = ["concept:name", "Purchasing Document", "Item", "Item Type", "Item Category", "Document Type",
             "GR-Based Inv. Verif.", "Goods Receipt", "Company", "Vendor", "Name", "Spend area text",
             "Sub spend area text", "Spend classification text", "Source", "Purch. Doc. Category name"]


def parse(src: Path, out: Path) -> tuple[int, int]:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "cases.csv", "w", newline="") as cf, open(out / "events.csv", "w", newline="") as ef:
        cw = csv.DictWriter(cf, fieldnames=CASE_KEYS, extrasaction="ignore")
        ew = csv.DictWriter(ef, fieldnames=["case_id"] + EVENT_KEYS)
        cw.writeheader(); ew.writeheader()
        case, event, in_event, n_case, n_ev = {}, {}, False, 0, 0
        for action, el in ET.iterparse(gzip.open(src), events=("start", "end")):
            t = el.tag.replace(NS, "")
            if action == "start":
                if t == "trace":
                    case = {}
                elif t == "event":
                    in_event, event = True, {}
                continue
            if t in ("string", "date", "float", "int", "boolean"):
                (event if in_event else case)[el.get("key")] = el.get("value")
            elif t == "event":
                # Trace attributes come before the first event in this file, so the case id is known here.
                ew.writerow({"case_id": case.get("concept:name"), **{k: event.get(k) for k in EVENT_KEYS}})
                in_event = False; n_ev += 1; el.clear()
            elif t == "trace":
                cw.writerow(case); n_case += 1; el.clear()
    return n_case, n_ev


if __name__ == "__main__":
    print(parse(Path(sys.argv[1]), Path(sys.argv[2])))
