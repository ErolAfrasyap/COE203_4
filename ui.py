import json
import os
import glob
import logging
import tkinter as tk
from tkinter import messagebox, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser
import subprocess
import sys

from viz_seaborn import fig_hist, fig_box
from scrape_and_clean import run_scrape_and_clean
from analysis_report import save_latest_report

logger = logging.getLogger(__name__)

class CryptoAnalyticsApp:
    def __init__(self, root, limit=50):
        self.root = root
        self.limit = limit

        self.root.title("Crypto Analytics System v4 (Scrape+Clean + Seaborn + Analysis + React)")
        self.root.geometry("980x650")

        top = tk.Frame(root)
        top.pack(fill="x", padx=10, pady=10)

        tk.Button(top, text="RUN SCRAPE + CLEAN", command=self.run_scrapy, width=20).pack(side="left")
        tk.Button(top, text="SEABORN VIZ", command=self.open_seaborn_window, width=14).pack(side="left", padx=8)
        tk.Button(top, text="RUN ANALYSIS", command=self.run_analysis, width=14).pack(side="left", padx=8)
        tk.Button(top, text="OPEN WEB DASHBOARD", command=self.open_web_dashboard, width=20).pack(side="left", padx=8)
        tk.Button(top, text="Clear Log", command=self.clear_log, width=10).pack(side="right")

        self.txt = scrolledtext.ScrolledText(root, height=30)
        self.txt.pack(fill="both", expand=True, padx=10, pady=10)

        self.log("UI ready. Use RUN SCRAPE + CLEAN first.")

    def log(self, msg: str):
        self.txt.insert(tk.END, msg + "\n")
        self.txt.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        self.txt.delete("1.0", tk.END)

    def run_scrapy(self):
        try:
            self.log(">>> Running Web Scrape + Cleaning...")
            raw_out, clean_out, log_out = run_scrape_and_clean()

            with open(log_out, "r", encoding="utf-8") as f:
                log = json.load(f)

            self.log(f">>> RAW saved:   {raw_out}")
            self.log(f">>> CLEAN saved: {clean_out}")
            self.log(f">>> LOG saved:   {log_out}")
            self.log("")
            self.log("=== CLEANING STEPS (put into README.md) ===")
            for s in log.get("steps", []):
                self.log(f"- {s.get('name')}: {s.get('description')}")
            self.log("")
            self.log("=== CLEANING SUMMARY ===")
            self.log(f"Input rows:  {log.get('input_rows')}")
            self.log(f"Dropped:     {log.get('dropped')}")
            self.log(f"Output rows: {log.get('output_rows')}")

            messagebox.showinfo("Success", f"Clean file:\n{clean_out}\n\nLog file:\n{log_out}")
        except Exception as exc:
            logger.exception("Scrape+clean failed")
            messagebox.showerror("Error", f"Scrape+clean failed:\n{exc}")

    def run_analysis(self):
        try:
            self.log(">>> Running analysis_report.py to generate advanced analysis + anomalies...")
            out = save_latest_report("data/clean/latest_analysis_report.json")
            self.log(f">>> Analysis report saved: {out}")
            messagebox.showinfo("Analysis", f"Saved:\n{out}")
        except Exception as exc:
            logger.exception("Analysis failed")
            messagebox.showerror("Error", f"Analysis failed:\n{exc}")

    def open_web_dashboard(self):
        try:
            self.log(">>> Starting FastAPI server on http://127.0.0.1:8000")
            subprocess.Popen([sys.executable, "-m", "uvicorn", "server:app", "--reload", "--port", "8000"], cwd=os.getcwd())
            webbrowser.open("http://127.0.0.1:5173")
            self.log(">>> Opened React dashboard URL: http://127.0.0.1:5173")
            self.log(">>> If React is not running yet, run: cd web ; npm install ; npm run dev")
        except Exception as exc:
            logger.exception("Web dashboard failed")
            messagebox.showerror("Error", f"Web dashboard failed:\n{exc}")

    def open_seaborn_window(self):
        try:
            files = sorted(glob.glob(os.path.join("data", "clean", "coingecko_clean_*.json")))
            if not files:
                messagebox.showwarning("No Data", "Run RUN SCRAPE + CLEAN first.")
                return

            latest = files[-1]
            with open(latest, "r", encoding="utf-8") as f:
                rows = json.load(f)

            changes = []
            for r in rows:
                v = r.get("change_24h_pct")
                if isinstance(v, (int, float)):
                    changes.append(float(v))

            if not changes:
                messagebox.showerror("Error", "No numeric change_24h_pct found.")
                return

            win = tk.Toplevel(self.root)
            win.title("Seaborn Visualizations")
            win.geometry("950x700")

            frame = tk.Frame(win)
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            fig1 = fig_hist(changes, "24h Change% Distribution", "Change %")
            c1 = FigureCanvasTkAgg(fig1, master=frame)
            c1.get_tk_widget().pack(fill="x", pady=10)
            c1.draw()

            fig2 = fig_box(changes, "24h Change% Boxplot", "Change %")
            c2 = FigureCanvasTkAgg(fig2, master=frame)
            c2.get_tk_widget().pack(fill="x", pady=10)
            c2.draw()
        except Exception as exc:
            logger.exception("Seaborn viz failed")
            messagebox.showerror("Error", f"Seaborn viz failed:\n{exc}")
