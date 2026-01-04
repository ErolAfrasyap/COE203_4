import json
import os
import glob
import logging
import tkinter as tk
from tkinter import messagebox, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from viz_seaborn import fig_hist, fig_box
from scrape_and_clean import run_scrape_and_clean

logger = logging.getLogger(__name__)

class CryptoAnalyticsApp:
    def __init__(self, root, limit=50):
        self.root = root
        self.limit = limit

        self.root.title("Crypto Analytics System v4 (Scrape+Clean Test UI)")
        self.root.geometry("900x600")

        top = tk.Frame(root)
        top.pack(fill="x", padx=10, pady=10)

        tk.Button(top, text="RUN SCRAPE + CLEAN", command=self.run_scrapy, width=25).pack(side="left")
        tk.Button(top, text="Clear Log", command=self.clear_log, width=12).pack(side="left", padx=10)
        tk.Button(top, text="SEABORN VIZ", command=self.open_seaborn_window, width=12).pack(side="left")

        self.txt = scrolledtext.ScrolledText(root, height=28)
        self.txt.pack(fill="both", expand=True, padx=10, pady=10)

        self.log("UI ready. Click RUN SCRAPE + CLEAN.")

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
            self.log("=== CLEANING STEPS (README'ye koy) ===")
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

    def open_seaborn_window(self):
        try:
            self.log(f">>> CWD: {os.getcwd()}")

            files = sorted(glob.glob(os.path.join("data", "clean", "coingecko_clean_*.json")))
            self.log(f">>> Clean files found: {len(files)}")

            if not files:
                messagebox.showwarning("No Data", "Önce RUN SCRAPE + CLEAN çalıştır.")
                return

            latest = files[-1]
            self.log(f">>> Using latest: {latest}")

            with open(latest, "r", encoding="utf-8") as f:
                rows = json.load(f)

            changes = []
            for r in rows:
                v = r.get("change_24h_pct")
                if isinstance(v, (int, float)):
                    changes.append(float(v))

            self.log(f">>> Numeric change_24h_pct count: {len(changes)}")

            if not changes:
                messagebox.showerror("Error", "change_24h_pct boş veya sayısal değil. cleaning.py parse_percent kontrol et.")
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

            self.log(f">>> Seaborn charts created from: {latest}")
        except Exception as exc:
            logger.exception("Seaborn viz failed")
            messagebox.showerror("Error", f"Seaborn viz failed:\n{exc}")
