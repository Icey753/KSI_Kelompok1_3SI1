import os
from src.visualize import build_dash_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "output", "results", "benchmark_results.csv")

if not os.path.exists(CSV_PATH):
    print(f"Error: File hasil benchmark tidak ditemukan di {CSV_PATH}.")
    print("Silakan jalankan pipeline utama terlebih dahulu dengan perintah: python main.py")
    exit(1)

app = build_dash_app(CSV_PATH)

if __name__ == "__main__":
    print("\n=======================================================")
    print("Launching Dash Dashboard...")
    print("Akses dashboard interaktif di browser Anda:")
    print("👉 http://127.0.0.1:8050/")
    print("=======================================================\n")
    app.run(debug=True, port=8050)
