import os
import sys
from src.data_prep import create_directories, generate_json_dataset, generate_image_dataset
from src.benchmark import run_single_file_benchmark
from src.report import save_benchmark_results
from src.visualize import generate_static_charts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_DIR = os.path.join(DATA_DIR, "json")
IMAGES_DIR = os.path.join(DATA_DIR, "images")

def check_and_prepare_data():
    """
    Memastikan dataset benchmark telah dibuat.
    Jika belum ada, memanggil generator dataset.
    """
    json_files = ["small.json", "medium.json", "large.json"]
    image_files = ["small.png", "medium.png", "large.png"]
    
    missing_data = False
    
    for f in json_files:
        if not os.path.exists(os.path.join(JSON_DIR, f)):
            missing_data = True
    for f in image_files:
        if not os.path.exists(os.path.join(IMAGES_DIR, f)):
            missing_data = True
            
    if missing_data:
        print("Dataset belum lengkap. Menjalankan persiapan data otomatis...")
        create_directories()
        
        # Generator configurations
        json_scenarios = [("small.json", 100), ("medium.json", 1000), ("large.json", 3000)]
        image_scenarios = [("small.png", 500), ("medium.png", 3000), ("large.png", 8000)]
        
        for name, size in json_scenarios:
            generate_json_dataset(size, os.path.join(JSON_DIR, name))
        for name, size in image_scenarios:
            generate_image_dataset(size, os.path.join(IMAGES_DIR, name))
        print("Persiapan data selesai!\n")
    else:
        print("Dataset terdeteksi lengkap. Melanjutkan ke benchmark...\n")

def main():
    print("=======================================================")
    print("     Mulai Pipeline Cipher Benchmark AES-GCM vs Ascon  ")
    print("=======================================================")
    
    # 1. Pastikan dataset siap
    check_and_prepare_data()
    
    # 2. Skenario Pengujian
    # Catatan: Ascon-128 pure-Python sangat lambat, skip large files dan images
    scenarios = [
        # (file_path, type, size_category)
        (os.path.join(JSON_DIR, "small.json"), "json", "small"),
        (os.path.join(JSON_DIR, "medium.json"), "json", "medium"),
        (os.path.join(JSON_DIR, "large.json"), "json", "large"),
        (os.path.join(IMAGES_DIR, "small.png"), "image", "small"),
        (os.path.join(IMAGES_DIR, "medium.png"), "image", "medium"),
        (os.path.join(IMAGES_DIR, "large.png"), "image", "large"),
    ]
    
    all_results = []
    
    # 3. Jalankan Loop Benchmark
    # Catatan: library ascon 0.0.9 adalah pure-Python sehingga sangat lambat pada file besar.
    # Pipeline tetap dijalankan untuk semua ukuran file, tetapi jumlah iterasi disesuaikan
    # agar seluruh skenario selesai dalam waktu yang masih masuk akal.
    iteration_plan = {
        "small": {"iterations": 30, "warm_ups": 5},
        "medium": {"iterations": 20, "warm_ups": 5},
        "large": {"iterations": 10, "warm_ups": 5},
    }

    for file_path, file_type, size_cat in scenarios:
        if not os.path.exists(file_path):
            print(f"Peringatan: File {file_path} tidak ditemukan, dilewati.")
            continue

        plan = iteration_plan[size_cat]
        iters = plan["iterations"]
        warm = plan["warm_ups"]

        print(f"Menjalankan benchmark dengan {iters} iterasi dan {warm} warm-up runs...")
        file_results = run_single_file_benchmark(file_path, file_type, size_cat, warm_ups=warm, iterations=iters)
        all_results.extend(file_results)
        
    # 4. Simpan CSV Report
    csv_path = save_benchmark_results(all_results)
    
    # 5. Buat Grafik Statis
    generate_static_charts(csv_path)
    
    print("\n=======================================================")
    print("               Pipeline Sukses Selesai!               ")
    print("=======================================================")
    print(f"1. Laporan CSV: output/results/benchmark_results.csv")
    print(f"2. Grafik Statis: output/charts/latency_comparison.png")
    print(f"3. Untuk melihat dashboard interaktif, jalankan:")
    print(f"   python dashboard.py")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
