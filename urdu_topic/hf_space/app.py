"""
Urdu News Scraper — HuggingFace Spaces (Gradio SDK, FREE)

Runs the scraper 24/7 in a background thread. Gradio UI provides a dashboard
to view progress, start/stop, and download data.

Persistent storage at /data/ survives Space restarts.

Setup:
1. Create HF Space with Gradio SDK
2. Upload app.py + requirements.txt + gui_app/ folder
3. Add Storage bucket in Space settings (free, 20 GB)
4. Set AUTOSTART=1 in Space variables
5. Visit Space URL — scraper runs 24/7
"""
import os
import sys
import json
import time
import threading
import traceback
from datetime import datetime
from pathlib import Path

# ============================================================
# PATH SETUP — find the gui_app folder
# ============================================================
# When deployed to HF Space, gui_app folder sits next to app.py
HERE = Path(__file__).parent.resolve()
GUI_APP_PATH = HERE / "gui_app"
if not GUI_APP_PATH.exists():
    # Fallback for local dev
    GUI_APP_PATH = Path("/home/z/my-project/urdu_topic/gui_app")
sys.path.insert(0, str(GUI_APP_PATH))

# ============================================================
# CONFIG — from env vars (override in HF Space Settings → Variables)
# ============================================================
# Default: /data/urdu_scrape (HF persistent storage)
# Falls back to ./data for local dev
PROJECT_DIR = os.environ.get("PROJECT_DIR", "/data/urdu_scrape")
if not os.path.exists("/data"):
    # Local dev mode — use a local folder
    PROJECT_DIR = str(HERE / "data")
os.makedirs(PROJECT_DIR, exist_ok=True)
os.makedirs(os.path.join(PROJECT_DIR, "data"), exist_ok=True)

DELAY = float(os.environ.get("DELAY", "3"))
MAX_MINUTES = int(os.environ.get("MAX_MINUTES", "0"))
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "0"))
MAX_SITEMAPS = int(os.environ.get("MAX_SITEMAPS", "500"))
SINCE_DATE = os.environ.get("SINCE_DATE", "") or None
PARALLEL_MODE = os.environ.get("PARALLEL_MODE", "1") == "1"
SOURCES_ENV = os.environ.get("SOURCES", "all")

# Import the scraper logic from gui_app
from urdu_scraper_gui import ScraperWorker, ScraperState, SOURCES  # noqa

if SOURCES_ENV == "all":
    SELECTED_SOURCES = list(SOURCES.keys())
else:
    SELECTED_SOURCES = [s.strip() for s in SOURCES_ENV.split(",") if s.strip() in SOURCES]

# ============================================================
# GLOBAL STATE
# ============================================================
class GlobalState:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running = False
        self.stop_flag = threading.Event()
        self.worker_thread = None
        self.log_lines = []
        self.start_time = None
        self.last_heartbeat = None

    def add_log(self, msg):
        with self.lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_lines.append(f"[{ts}] {msg}")
            if len(self.log_lines) > 5000:
                self.log_lines = self.log_lines[-5000:]

    def get_logs(self, last_n=200):
        with self.lock:
            return list(self.log_lines[-last_n:])

    def get_status(self):
        with self.lock:
            articles_per_source = {}
            total_articles = 0
            for source_key in SOURCES.keys():
                try:
                    state = ScraperState(source_key, PROJECT_DIR)
                    articles_per_source[source_key] = len(state.articles)
                    total_articles += len(state.articles)
                except Exception:
                    articles_per_source[source_key] = 0

            elapsed = None
            if self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()

            return {
                "is_running": self.is_running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "elapsed_seconds": elapsed,
                "total_articles": total_articles,
                "articles_per_source": articles_per_source,
                "project_dir": PROJECT_DIR,
                "config": {
                    "delay": DELAY,
                    "max_minutes": MAX_MINUTES,
                    "max_articles": MAX_ARTICLES,
                    "max_sitemaps": MAX_SITEMAPS,
                    "since_date": SINCE_DATE,
                    "parallel_mode": PARALLEL_MODE,
                    "selected_sources": SELECTED_SOURCES,
                },
            }


STATE = GlobalState()


def log_func(msg):
    STATE.add_log(msg)


def progress_func(**kwargs):
    source = kwargs.get("source", "?")
    current = kwargs.get("current", 0)
    total = kwargs.get("total", 0)
    scraped = kwargs.get("scraped", 0)
    rate = kwargs.get("rate", 0)
    # Log every 25 articles per source to avoid spam
    if current % 25 == 0 or current == 1:
        log_func(f"[{source}] {current}/{total} scraped={scraped} rate={rate:.1f}/min")


# ============================================================
# SCRAPER THREAD
# ============================================================
def run_scraper():
    if STATE.is_running:
        log_func("Already running, ignoring start request")
        return

    STATE.stop_flag.clear()
    STATE.is_running = True
    STATE.start_time = datetime.now()
    log_func("=" * 60)
    log_func(f"🚀 Starting scraper at {STATE.start_time.isoformat()}")
    log_func(f"📁 Project dir: {PROJECT_DIR}")
    log_func(f"📡 Sources ({len(SELECTED_SOURCES)}): {SELECTED_SOURCES}")
    log_func(f"⏱️  Delay: {DELAY}s, Parallel: {PARALLEL_MODE}")
    log_func(f"📊 Max minutes: {MAX_MINUTES}, Max articles/source: {MAX_ARTICLES}")
    log_func("=" * 60)

    worker = ScraperWorker(
        project_dir=PROJECT_DIR,
        selected_sources=SELECTED_SOURCES,
        delay=DELAY,
        max_minutes=MAX_MINUTES,
        max_articles_per_source=MAX_ARTICLES or None,
        max_sitemaps_per_source=MAX_SITEMAPS,
        since_date=SINCE_DATE,
        log_func=log_func,
        progress_func=progress_func,
        stop_flag=STATE.stop_flag,
        parallel_mode=PARALLEL_MODE,
    )

    try:
        worker.run()
    except Exception as e:
        log_func(f"❌ FATAL: {type(e).__name__}: {e}")
        log_func(traceback.format_exc())
    finally:
        STATE.is_running = False
        log_func(f"🛑 Scraper stopped at {datetime.now().isoformat()}")


def start_scraper_thread():
    if STATE.is_running:
        return "Already running"
    t = threading.Thread(target=run_scraper, daemon=True, name="scraper")
    t.start()
    STATE.worker_thread = t
    return "Scraper starting..."


def stop_scraper():
    if not STATE.is_running:
        return "Not running"
    log_func("⏸️ Stop requested — will save and exit after current article")
    STATE.stop_flag.set()
    return "Stop requested — saving progress..."


# ============================================================
# HEARTBEAT — keeps Space awake (HF sleeps after 48h idle)
# ============================================================
def heartbeat_loop():
    while True:
        time.sleep(30 * 60)  # 30 minutes
        try:
            status = STATE.get_status()
            log_func(f"💓 HEARTBEAT: running={status['is_running']} total={status['total_articles']:,}")
            STATE.last_heartbeat = datetime.now()
        except Exception:
            pass


def start_heartbeat():
    t = threading.Thread(target=heartbeat_loop, daemon=True, name="heartbeat")
    t.start()


# ============================================================
# AUTO-START
# ============================================================
def auto_start():
    """Auto-start the scraper when Space boots (if AUTOSTART=1)."""
    if os.environ.get("AUTOSTART", "1") == "1":
        log_func("🤖 AUTOSTART=1 — starting scraper automatically in 10 seconds...")
        threading.Timer(10, start_scraper_thread).start()


# ============================================================
# GRADIO UI
# ============================================================
def build_ui():
    import gradio as gr

    with gr.Blocks(
        title="Urdu News Scraper",
        theme=gr.themes.Soft(),
        css="""
        .status-box { background: #f0f9ff; padding: 15px; border-radius: 8px; }
        .log-box { font-family: monospace; font-size: 11px; }
        """
    ) as demo:
        gr.Markdown("""
        # 📰 Urdu News Scraper — 24/7 on HuggingFace Spaces

        Scrapes Urdu news from 8 Pakistani outlets in parallel.
        Target: 5M+ articles over ~26 days of 24/7 operation.

        **Sources**: Nawa-i-Waqt (2.5M), Express (450K), ARY Urdu (352K), 24 News HD (186K),
        Ummat (116K), Bol (71K), Daily Ausaf (52K), Independent Urdu (52K) — **3.86M total available**
        """)

        with gr.Row():
            with gr.Column(scale=1):
                start_btn = gr.Button("▶ Start Scraping", variant="primary", size="lg")
                stop_btn = gr.Button("⏸️ Stop (safe)", variant="stop", size="lg")
                refresh_btn = gr.Button("🔄 Refresh Now")

            with gr.Column(scale=2):
                status_md = gr.Markdown("Loading status...")

        with gr.Row():
            with gr.Column(scale=2):
                logs_out = gr.Textbox(
                    label="Live Log (last 200 lines)",
                    lines=25,
                    max_lines=25,
                    interactive=False,
                    elem_classes=["log-box"],
                )

            with gr.Column(scale=1):
                sources_md = gr.Markdown("Loading sources...")

        # Functions to update UI
        def get_status_markdown():
            s = STATE.get_status()
            is_running = s["is_running"]
            status_icon = "🟢 Running" if is_running else "⚪ Stopped"
            elapsed = s.get("elapsed_seconds", 0) or 0
            elapsed_str = f"{int(elapsed // 3600)}h {int((elapsed % 3600) // 60)}m" if elapsed else "—"

            # Throughput estimate
            if elapsed and elapsed > 60:
                rate = s["total_articles"] / (elapsed / 60)
                rate_str = f"{rate:.0f} articles/min"
            else:
                rate_str = "—"

            # ETA to 5M
            if elapsed and s["total_articles"] > 100:
                rate_per_sec = s["total_articles"] / elapsed
                if rate_per_sec > 0:
                    eta_seconds = (5_000_000 - s["total_articles"]) / rate_per_sec
                    eta_days = eta_seconds / 86400
                    eta_str = f"{eta_days:.1f} days"
                else:
                    eta_str = "—"
            else:
                eta_str = "—"

            return f"""
            <div class="status-box">
            **Status**: {status_icon} | **Elapsed**: {elapsed_str} | **Total articles**: {s["total_articles"]:,}

            **Rate**: {rate_str} | **ETA to 5M**: {eta_str}

            **Config**: delay={s["config"]["delay"]}s, parallel={s["config"]["parallel_mode"]},
            sources={len(s["config"]["selected_sources"])}, max_sitemaps={s["config"]["max_sitemaps"]}

            **Project dir**: `{s["project_dir"]}`
            </div>
            """

        def get_sources_markdown():
            s = STATE.get_status()
            lines = ["**Articles per source:**\n"]
            lines.append("| Source | Articles |")
            lines.append("|--------|---------:|")
            for source_key, count in s["articles_per_source"].items():
                name = SOURCES[source_key]["name"]
                est = SOURCES[source_key]["estimated_articles"]
                pct = count / est * 100 if est > 0 else 0
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                lines.append(f"| {name} | {count:,} / {est:,} ({pct:.1f}%) |")
            lines.append(f"| **TOTAL** | **{s['total_articles']:,}** |")
            return "\n".join(lines)

        def get_logs_text():
            return "\n".join(STATE.get_logs(200))

        # Wire up buttons
        def _start():
            msg = start_scraper_thread()
            return msg

        def _stop():
            msg = stop_scraper()
            return msg

        start_btn.click(_start, outputs=[logs_out])
        stop_btn.click(_stop, outputs=[logs_out])

        # Manual refresh
        refresh_btn.click(
            lambda: (get_status_markdown(), get_logs_text(), get_sources_markdown()),
            outputs=[status_md, logs_out, sources_md],
        )

        # Auto-refresh every 15 seconds
        demo.load(
            lambda: (get_status_markdown(), get_logs_text(), get_sources_markdown()),
            outputs=[status_md, logs_out, sources_md],
            every=15,
        )

    return demo


# ============================================================
# MAIN
# ============================================================
def main():
    # Start heartbeat (keeps Space awake)
    start_heartbeat()
    log_func(f"💓 Heartbeat started — logs every 30 min to keep Space awake")

    # Auto-start scraper if configured
    auto_start()

    # Build and launch Gradio UI
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        prevent_thread_lock=True,
        show_error=True,
    )

    # Keep main thread alive
    log_func("🚀 Gradio UI launched — scraper running in background")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        log_func("Shutdown received")
        stop_scraper()


if __name__ == "__main__":
    main()
