"""Batch-run every poem in ./poems through both backends and save results.
No pandas/numpy needed.

Usage:
    python run_comparison.py --runs 1
Optional: annotations.csv (columns: poem,rhyme_scheme) gives a rhyme accuracy score.
"""
import argparse
import csv
import json
from pathlib import Path

from analyzer import BACKENDS, analyze_poem


def norm(s):
    return "".join(ch for ch in str(s or "").upper() if ch.isalpha())


def pct(x):
    return f"{x * 100:.0f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1, help="repeats per poem (consistency)")
    ap.add_argument("--poems", default="poems")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(exist_ok=True)
    poems = sorted(Path(args.poems).glob("*.txt"))
    if not poems:
        raise SystemExit("No .txt poems found in ./poems")

    ann = {}
    ann_path = Path("annotations.csv")
    if ann_path.exists():
        with ann_path.open(encoding="utf-8") as f:
            ann = {r["poem"]: norm(r["rhyme_scheme"]) for r in csv.DictReader(f)}

    rows, raw_log = [], []
    for p in poems:
        text = p.read_text(encoding="utf-8")
        for backend in BACKENDS:
            for i in range(args.runs):
                print(f"{p.stem} | {backend} | run {i + 1}")
                r = analyze_poem(text, backend)
                res = r["result"] or {}
                rows.append({
                    "poem": p.stem, "backend": backend, "model": r["model"], "run": i + 1,
                    "ok": r["ok"], "latency_s": r["latency_s"],
                    "form": res.get("form"), "meter": res.get("meter"),
                    "rhyme_scheme": res.get("rhyme_scheme"), "error": r["error"],
                })
                raw_log.append(r)

    with (out_dir / "results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (out_dir / "raw.json").write_text(json.dumps(raw_log, indent=2), encoding="utf-8")

    summary = []
    for backend in BACKENDS:
        rs = [r for r in rows if r["backend"] == backend]
        ok = sum(1 for r in rs if r["ok"]) / len(rs)
        lat = [r["latency_s"] for r in rs if r["latency_s"] is not None]
        avg_lat = sum(lat) / len(lat) if lat else 0
        by_poem = {}
        for r in rs:
            by_poem.setdefault(r["poem"], []).append(norm(r["rhyme_scheme"]))
        cons = sum(1 for v in by_poem.values() if len(set(v)) <= 1) / len(by_poem)
        scored = [r for r in rs if r["poem"] in ann]
        acc = (sum(1 for r in scored if norm(r["rhyme_scheme"]) == ann[r["poem"]]) / len(scored)) if scored else None
        summary.append({
            "backend": backend, "model": rs[0]["model"],
            "parse_success": round(ok, 2), "avg_latency_s": round(avg_lat, 2),
            "rhyme_consistency": round(cons, 2),
            "rhyme_accuracy": round(acc, 2) if acc is not None else "",
        })

    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)

    print("\n=== SUMMARY ===")
    for s in summary:
        print(s)
    errs = [r for r in rows if r["error"]]
    if errs:
        print("\nFirst error:", errs[0]["backend"], "->", errs[0]["error"])


if __name__ == "__main__":
    main()
