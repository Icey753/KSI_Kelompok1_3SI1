import os

from src.dashboard_app import build_dash_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "output", "results", "benchmark_results.csv")

if not os.path.exists(CSV_PATH):
    print(f"Peringatan: CSV benchmark belum ditemukan di {CSV_PATH}.")
    print("Dashboard tetap bisa dibuka untuk upload file langsung.")
    CSV_PATH = None

app = build_dash_app(CSV_PATH)

if __name__ == "__main__":
    print("\n=======================================================")
    print("Launching Dash Dashboard...")
    print("Akses dashboard interaktif di browser Anda:")
    print("http://127.0.0.1:8050/")
    print("=======================================================\n")
    app.run(debug=True, port=8050)
