"""
Headless version of the Urdu News Scraper — runs on HuggingFace Spaces (no GUI).
Wraps the scraper logic from urdu_scraper_gui.py and runs it as a background thread.
Exposes a simple Gradio web UI to view progress and start/stop.
"""
import os
import sys
import json
import time
import threading
import signal
from datetime import datetime

# Add the gui_app dir to path so we can reuse the scraper logic
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gui_app"))
# When deployed to HF Space, the gui_app folder is copied alongside
ALT_PATH = "/home/z/my-project/urdu_topic/gui_app"
if os.path.exists(ALT_PATH):
    sys.path.insert(0, ALT_PATH)

from urdu_scraper_gui import ScraperWorker, ScraperState, SOURCES, PARSERS  # noqa


# ============================================================
# CONFIG — override defaults for HF Space deployment
# ============================================================
PROJECT_DIR = os.environ.get("PROJECT_DIR", "/data/urdu_scrape")
DELAY = float(os.environ.get("DELAY", "3"))
MAX_MINUTES = int(os.environ.get("MAX_MINUTES", "0"))  # 0 = unlimited
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "0"))  # 0 = unlimited
MAX_SITEMAPS = int(os.environ.get("MAX_SITEMAPS", "500"))
SINCE_DATE = os.environ.get("SINCE_DATE", "") or None
PARALLEL_MODE = os.environ.get("PARALLEL_MODE", "1") == "1"
SELECTED_SOURCES = os.environ.get("SOURCES", "all")
if SELECTED_SOURCES == "all":
    SELECTED_SOURCES = list(SOURCES.keys())
else:
    SELECTED_SOURCES = [s.strip() for s in SELECTED_SOURCES.split(",") if s.strip() in SOURCES]


# ============================================================
# GLOBAL STATE — for the web UI to read
# ============================================================
class GlobalState:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running = False
        self.stop_flag = threading.Event()
        self.worker_thread = None
        self.log_lines = []  # rolling log (last 1000 lines)
        self.start_time = None
        self.last_update = None

    def add_log(self, msg):
        with self.lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_lines.append(f"[{ts}] {msg}")
            if len(self.log_lines) > 1000:
                self.log_lines = self.log_lines[-1000:]
            self.last_update = datetime.now()

    def get_logs(self, last_n=100):
        with self.lock:
            return list(self.log_lines[-last_n:])

    def get_status(self):
        with self.lock:
            # Count articles per source (handle case where PROJECT_DIR doesn't exist yet)
            articles_per_source = {}
            total_articles = 0
            for source_key in SOURCES.keys():
                try:
                    state = ScraperState(source_key, PROJECT_DIR)
                    articles_per_source[source_key] = len(state.articles)
                    total_articles += len(state.articles)
                except Exception:
                    articles_per_source[source_key] = 0

            return {
                "is_running": self.is_running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "last_update": self.last_update.isoformat() if self.last_update else None,
                "total_articles": total_articles,
                "articles_per_source": articles_per_source,
                "project_dir": PROJECT_DIR,
                "delay": DELAY,
                "max_minutes": MAX_MINUTES,
                "max_articles": MAX_ARTICLES,
                "max_sitemaps": MAX_SITEMAPS,
                "since_date": SINCE_DATE,
                "parallel_mode": PARALLEL_MODE,
                "selected_sources": SELECTED_SOURCES,
            }


STATE = GlobalState()


# ============================================================
# LOG FUNCTION — bridges to global state
# ============================================================
def log_func(msg):
    STATE.add_log(msg)


def progress_func(**kwargs):
    # In headless mode, just log significant progress (every 25 articles per source)
    source = kwargs.get("source", "?")
    current = kwargs.get("current", 0)
    total = kwargs.get("total", 0)
    scraped = kwargs.get("scraped", 0)
    rate = kwargs.get("rate", 0)
    if current % 25 == 0 or current == 1:
        log_func(f"PROGRESS [{source}] {current}/{total} scraped={scraped} rate={rate:.1f}/min")


# ============================================================
# SCRAPER THREAD
# ============================================================
def run_scraper():
    """Run the scraper in a background thread."""
    if STATE.is_running:
        log_func("Already running, ignoring start request")
        return

    STATE.stop_flag.clear()
    STATE.is_running = True
    STATE.start_time = datetime.now()
    log_func("=" * 60)
    log_func(f"Starting scraper at {STATE.start_time.isoformat()}")
    log_func(f"Project dir: {PROJECT_DIR}")
    log_func(f"Sources: {SELECTED_SOURCES}")
    log_func(f"Delay: {DELAY}s, parallel: {PARALLEL_MODE}")
    log_func(f"Max minutes: {MAX_MINUTES}, max articles/source: {MAX_ARTICLES}")
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
        log_func(f"FATAL: {type(e).__name__}: {e}")
    finally:
        STATE.is_running = False
        log_func(f"Scraper stopped at {datetime.now().isoformat()}")


def start_scraper_thread():
    """Start scraper in a daemon thread."""
    t = threading.Thread(target=run_scraper, daemon=True, name="scraper")
    t.start()
    STATE.worker_thread = t


def stop_scraper():
    """Stop the scraper gracefully."""
    log_func("Stop requested — will save and exit after current article")
    STATE.stop_flag.set()


# ============================================================
# AUTO-START ON BOOT — for HF Space deployment
# ============================================================
def auto_start_if_env_set():
    """Auto-start the scraper if AUTOSTART=1 env var is set."""
    if os.environ.get("AUTOSTART", "0") == "1":
        log_func("AUTOSTART=1 detected — starting scraper automatically")
        # Small delay to let the web UI come up first
        threading.Timer(5, start_scraper_thread).start()


# ============================================================
# HEARTBEAT — keep HF Space awake
# ============================================================
def heartbeat():
    """Log a heartbeat every 30 minutes so the Space doesn't sleep."""
    while True:
        time.sleep(30 * 60)
        status = STATE.get_status()
        log_func(f"HEARTBEAT: running={status['is_running']} total_articles={status['total_articles']:,}")


def start_heartbeat():
    t = threading.Thread(target=heartbeat, daemon=True, name="heartbeat")
    t.start()


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    # Create project dir
    os.makedirs(PROJECT_DIR, exist_ok=True)
    os.makedirs(os.path.join(PROJECT_DIR, "data"), exist_ok=True)

    # Start heartbeat (keeps Space awake)
    start_heartbeat()

    # Auto-start if requested
    auto_start_if_env_set()

    # Launch Gradio UI (if installed) or just keep alive
    try:
        import gradio as gr
        print("Gradio available — launching web UI")
        # Build minimal UI
        with gr.Blocks(title="Urdu News Scraper") as demo:
            gr.Markdown("# 📰 Urdu News Scraper (Headless)")
            gr.Markdown("Running 24/7 on HuggingFace Spaces. View live progress below.")

            with gr.Row():
                start_btn = gr.Button("▶ Start", variant="primary")
                stop_btn = gr.Button("■ Stop")

            status_out = gr.JSON(label="Status", value=lambda: STATE.get_status())
            logs_out = gr.Textbox(label="Live Log (last 100 lines)", lines=20, max_lines=20,
                                  value=lambda: "\n".join(STATE.get_logs(100)))

            def _start():
                start_scraper_thread()
                return "Scraper starting..."

            def _stop():
                stop_scraper()
                return "Stop requested..."

            start_btn.click(_start, outputs=[logs_out])
            stop_btn.click(_stop, outputs=[logs_out])

            # Auto-refresh every 10 seconds
            demo.load(lambda: (STATE.get_status(), "\n".join(STATE.get_logs(100))),
                      outputs=[status_out, logs_out], every=10)

        demo.launch(server_name="0.0.0.0", server_port=7860, share=False, prevent_thread_lock=True)

        # Keep main thread alive
        while True:
            time.sleep(60)

    except ImportError:
        print("Gradio not available — running headless only")
        # Just start the scraper and keep alive
        if os.environ.get("AUTOSTART", "0") == "1":
            start_scraper_thread()
        while True:
            time.sleep(60)
