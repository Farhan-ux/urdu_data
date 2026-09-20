"""
Run all 5 sources in PARALLEL processes (not threads).
Each source saves to its own file. Total wall-time = slowest source.
"""
import os, sys, time, json, subprocess
from multiprocessing import Process

LOG_DIR = "/home/z/my-project/urdu_topic/logs"
os.makedirs(LOG_DIR, exist_ok=True)

SOURCES = ["express", "jang", "geo", "samaa", "nawaiwaqt"]

def run_source(name):
    """Run a single source scraper as a subprocess."""
    log_path = os.path.join(LOG_DIR, f"{name}.log")
    cmd = ["/home/z/.venv/bin/python", "/home/z/my-project/urdu_topic/scripts/02_scrape_v2.py", name]
    with open(log_path, "w") as logf:
        proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT)
        return proc

if __name__ == "__main__":
    print("Launching 5 parallel source scrapers...")
    procs = []
    for s in SOURCES:
        p = run_source(s)
        procs.append((s, p))
        print(f"  Started {s} (PID {p.pid})")
        time.sleep(2)  # stagger

    print(f"\nAll {len(procs)} scrapers running. Monitoring...")
    # Monitor
    start = time.time()
    while True:
        alive = sum(1 for _, p in procs if p.poll() is None)
        elapsed = time.time() - start
        print(f"  [{elapsed:.0f}s] {alive}/{len(procs)} still running")
        if alive == 0:
            break
        time.sleep(15)

    print("\n=== All scrapers finished ===")
    # Combine
    data_dir = "/home/z/my-project/urdu_topic/data"
    all_articles = []
    for s in SOURCES + ["bbc"]:
        path = os.path.join(data_dir, f"{s}_articles.json")
        if os.path.exists(path):
            with open(path) as f:
                arts = json.load(f)
            print(f"  {s}: {len(arts)} articles")
            all_articles.extend(arts)

    out = os.path.join(data_dir, "all_articles.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    print(f"\nTotal: {len(all_articles)} articles")
    print(f"Saved: {out}")
