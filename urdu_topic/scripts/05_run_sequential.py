"""
Run scrapers sequentially in a single process — no backgrounding, no nohup.
Saves progress as it goes.
"""
import os, sys, json, time, traceback
sys.path.insert(0, "/home/z/my-project/urdu_topic/scripts")
from importlib import import_module

# Import everything from 04_scrape_safe
exec(open("/home/z/my-project/urdu_topic/scripts/04_scrape_safe.py").read())

SOURCES_TO_RUN = ["jang", "geo", "samaa"]  # express already done

if __name__ == "__main__":
    print(f"Will run: {SOURCES_TO_RUN}", flush=True)
    print(f"Already done: express (150 articles)", flush=True)

    for name in SOURCES_TO_RUN:
        print(f"\n{'='*60}", flush=True)
        print(f"Starting {name.upper()} at {time.strftime('%H:%M:%S')}", flush=True)
        print(f"{'='*60}", flush=True)

        collector, parser = SOURCES[name]
        try:
            t0 = time.time()
            urls = collector()
            print(f"URLs collected: {len(urls)} in {time.time()-t0:.1f}s", flush=True)

            if not urls:
                print(f"No URLs for {name}, skipping", flush=True)
                continue

            url_list = list(urls)[:1500]
            print(f"Parsing {len(url_list)} articles...", flush=True)

            articles = []
            failed = 0
            t1 = time.time()
            with ThreadPoolExecutor(max_workers=8) as ex:
                futures = {ex.submit(parser, u): u for u in url_list}
                for i, fut in enumerate(as_completed(futures)):
                    try:
                        art = fut.result(timeout=15)
                        if art:
                            articles.append(art)
                        else:
                            failed += 1
                    except Exception:
                        failed += 1
                    if (i + 1) % 50 == 0:
                        print(f"  [{i+1}/{len(url_list)}] ok={len(articles)} fail={failed} elapsed={time.time()-t1:.1f}s", flush=True)
                        # Save incrementally
                        out_path = os.path.join(OUT_DIR, f"{name}_articles.json")
                        with open(out_path, "w", encoding="utf-8") as f:
                            json.dump(articles, f, ensure_ascii=False, indent=2)

            print(f"Done {name}: parsed={len(articles)} failed={failed} in {time.time()-t1:.1f}s", flush=True)
            out_path = os.path.join(OUT_DIR, f"{name}_articles.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            print(f"Saved: {out_path}", flush=True)

        except Exception as e:
            print(f"FATAL on {name}: {e}", flush=True)
            traceback.print_exc()

    # Final combine
    print(f"\n{'='*60}", flush=True)
    print("FINAL COMBINE", flush=True)
    print(f"{'='*60}", flush=True)
    all_articles = []
    for s in ["bbc", "express", "jang", "geo", "samaa", "nawaiwaqt"]:
        p = os.path.join(OUT_DIR, f"{s}_articles.json")
        if os.path.exists(p):
            with open(p) as f:
                arts = json.load(f)
            print(f"  {s}: {len(arts)} articles", flush=True)
            all_articles.extend(arts)

    out = os.path.join(OUT_DIR, "all_articles.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    print(f"\nTotal: {len(all_articles)} articles", flush=True)
    print(f"Saved: {out}", flush=True)
