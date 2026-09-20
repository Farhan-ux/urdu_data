"""
HF Space app for Scrapy-based Urdu news scraper.

Launches the Scrapy spider as a subprocess, monitors progress, shows live log
in a Gradio dashboard. Articles are saved to /data/urdu_scrape/ (persistent).

Usage:
    Visit https://YOUR_SPACE.hf.space
    Click "Start Scrapy" to begin scraping
    Watch live log + article count
"""
import os
import sys
import time
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ============================================================
# CONFIG
# ============================================================
HERE = Path(__file__).parent.resolve()
PROJECT_DIR = os.environ.get("OUTPUT_DIR", "/data/urdu_scrape")
if not os.path.exists("/data"):
    PROJECT_DIR = str(HERE / "data")
os.makedirs(PROJECT_DIR, exist_ok=True)
os.makedirs(os.path.join(PROJECT_DIR, "data"), exist_ok=True)

SCRAPY_PROJECT_DIR = str(HERE)

# ============================================================
# GLOBAL STATE
# ============================================================
class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running = False
        self.process = None
        self.log_lines = []
        self.start_time = None
        self.log_file_path = None

    def add_log(self, msg):
        with self.lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_lines.append(f"[{ts}] {msg}")
            if len(self.log_lines) > 5000:
                self.log_lines = self.log_lines[-5000:]

    def get_logs(self, n=200):
        with self.lock:
            return list(self.log_lines[-n:])

    def get_status(self):
        with self.lock:
            # Count articles per source from CSV
            articles_per_source = defaultdict(int)
            total_articles = 0
            csv_path = os.path.join(PROJECT_DIR, "all_articles_labeled.csv")
            if os.path.exists(csv_path):
                try:
                    import csv
                    with open(csv_path, encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            src = row.get("source", "unknown")
                            articles_per_source[src] += 1
                            total_articles += 1
                except Exception:
                    pass

            elapsed = None
            if self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()

            return {
                "is_running": self.is_running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "elapsed_seconds": elapsed,
                "total_articles": total_articles,
                "articles_per_source": dict(articles_per_source),
                "project_dir": PROJECT_DIR,
                "log_file": self.log_file_path,
            }


STATE = State()


# ============================================================
# SCRAPER THREAD
# ============================================================
def run_scrapy():
    """Run Scrapy as a subprocess and stream output to logs."""
    if STATE.is_running:
        STATE.add_log("Already running")
        return

    STATE.is_running = True
    STATE.start_time = datetime.now()
    log_file = os.path.join(PROJECT_DIR, f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    STATE.log_file_path = log_file

    STATE.add_log("=" * 60)
    STATE.add_log(f"🚀 Starting Scrapy at {STATE.start_time.isoformat()}")
    STATE.add_log(f"📁 Output: {PROJECT_DIR}")
    STATE.add_log(f"📝 Log: {log_file}")
    STATE.add_log(f"⚙️  Sources: all (8 sources, parallel)")
    STATE.add_log(f"⚡ Concurrent: 64 total, 16/domain, 0.1s delay")
    STATE.add_log("=" * 60)

    # Build command
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "urdu_news",
        "-s", "LOG_FILE=",
        "-s", "LOG_LEVEL=INFO",
        "-s", f"OUTPUT_DIR={PROJECT_DIR}",
        "-s", "CONCURRENT_REQUESTS=64",
        "-s", "CONCURRENT_REQUESTS_PER_DOMAIN=16",
        "-s", "DOWNLOAD_DELAY=0.1",
    ]

    STATE.add_log(f"Command: {' '.join(cmd[:6])}...")

    try:
        # Run as subprocess, capture stdout+stderr
        STATE.process = subprocess.Popen(
            cmd,
            cwd=SCRAPY_PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env={**os.environ, "OUTPUT_DIR": PROJECT_DIR, "PYTHONUNBUFFERED": "1"},
        )

        # Stream output line by line
        for line in STATE.process.stdout:
            line = line.rstrip()
            if line:
                STATE.add_log(line)
                # Also write to log file
                try:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                except Exception:
                    pass

        STATE.process.wait()
        rc = STATE.process.returncode
        STATE.add_log(f"\nScrapy finished with exit code {rc}")

    except Exception as e:
        STATE.add_log(f"❌ FATAL: {type(e).__name__}: {e}")
    finally:
        STATE.is_running = False
        STATE.process = None
        STATE.add_log(f"Stopped at {datetime.now().isoformat()}")


def start_scraper():
    if STATE.is_running:
        return "Already running"
    t = threading.Thread(target=run_scrapy, daemon=True, name="scrapy")
    t.start()
    return "Scrapy starting..."


def stop_scraper():
    if not STATE.is_running or not STATE.process:
        return "Not running"
    STATE.add_log("⏸️ Stop requested — sending SIGTERM to Scrapy")
    STATE.process.terminate()
    return "Stop requested — Scrapy will finish current requests then exit"


# ============================================================
# HEARTBEAT
# ============================================================
def heartbeat_loop():
    while True:
        time.sleep(30 * 60)
        try:
            s = STATE.get_status()
            STATE.add_log(f"💓 HEARTBEAT: running={s['is_running']} total={s['total_articles']:,}")
        except Exception:
            pass


# ============================================================
# AUTO-START
# ============================================================
def auto_start():
    if os.environ.get("AUTOSTART", "1") == "1":
        STATE.add_log("🤖 AUTOSTART=1 — starting Scrapy in 10s...")
        threading.Timer(10, start_scraper).start()


# ============================================================
# GRADIO UI
# ============================================================
def build_ui():
    import gradio as gr

    with gr.Blocks(title="Urdu News Scraper (Scrapy)", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 📰 Urdu News Scraper — Scrapy Edition

        **5x faster** than the previous scraper. Targets 5M+ articles with **category labels**.

        - 8 sources in parallel (16 concurrent requests per domain)
        - Articles saved with category as ground-truth label
        - Output: `all_articles_labeled.csv` (for ML training) + JSONL per source
        """)

        with gr.Row():
            with gr.Column(scale=1):
                start_btn = gr.Button("▶ Start Scrapy", variant="primary", size="lg")
                stop_btn = gr.Button("⏸️ Stop", variant="stop", size="lg")
                refresh_btn = gr.Button("🔄 Refresh")

            with gr.Column(scale=2):
                status_md = gr.Markdown("Loading...")

        with gr.Row():
            with gr.Column(scale=2):
                logs_out = gr.Textbox(
                    label="Live Log (last 200 lines)",
                    lines=25,
                    max_lines=25,
                    interactive=False,
                )
            with gr.Column(scale=1):
                sources_md = gr.Markdown("Loading...")

        def get_status_md():
            s = STATE.get_status()
            is_running = s["is_running"]
            icon = "🟢 Running" if is_running else "⚪ Stopped"
            elapsed = s.get("elapsed_seconds", 0) or 0
            elapsed_str = f"{int(elapsed // 3600)}h {int((elapsed % 3600) // 60)}m" if elapsed else "—"
            rate = s["total_articles"] / max(0.01, elapsed / 60) if elapsed and elapsed > 30 else 0
            eta = (5_000_000 - s["total_articles"]) / (rate * 60 * 24) if rate > 0 else None
            eta_str = f"{eta:.1f} days" if eta else "—"

            return f"""
**Status**: {icon} | **Elapsed**: {elapsed_str} | **Total**: {s["total_articles"]:,}

**Rate**: {rate:.0f} articles/min | **ETA to 5M**: {eta_str}

**Output**: `{s["project_dir"]}`
**Log file**: `{s["log_file"] or "(none)"}`
"""

        def get_sources_md():
            s = STATE.get_status()
            lines = ["**Articles per source:**\n"]
            lines.append("| Source | Articles |")
            lines.append("|--------|---------:|")
            source_names = {
                "express": "Express Urdu", "nawaiwaqt": "Nawa-i-Waqt",
                "aryurdu": "ARY Urdu", "24newshd": "24 News HD",
                "ummat": "Ummat", "bolurdu": "Bol News Urdu",
                "dailyausaf": "Daily Ausaf", "independenturdu": "Independent Urdu",
            }
            for src, count in sorted(s["articles_per_source"].items(), key=lambda x: -x[1]):
                name = source_names.get(src, src)
                lines.append(f"| {name} | {count:,} |")
            lines.append(f"| **TOTAL** | **{s['total_articles']:,}** |")
            return "\n".join(lines)

        def get_logs():
            return "\n".join(STATE.get_logs(200))

        start_btn.click(lambda: (start_scraper(), get_logs()), outputs=[logs_out, logs_out])
        stop_btn.click(lambda: (stop_scraper(), get_logs()), outputs=[logs_out, logs_out])
        refresh_btn.click(
            lambda: (get_status_md(), get_logs(), get_sources_md()),
            outputs=[status_md, logs_out, sources_md],
        )

        timer = gr.Timer(value=15)
        timer.tick(
            lambda: (get_status_md(), get_logs(), get_sources_md()),
            outputs=[status_md, logs_out, sources_md],
        )

    return demo


# ============================================================
# DUMMY GPU (for ZeroGPU)
# ============================================================
try:
    import spaces
    @spaces.GPU(duration=5)
    def _dummy(x=0):
        return x
except ImportError:
    def _dummy(x=0):
        return x


# ============================================================
# MAIN
# ============================================================
def main():
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    auto_start()
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        prevent_thread_lock=True,
        show_error=True,
    )
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
