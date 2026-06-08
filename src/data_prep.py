import os
import json
import math
import random
import argparse
from faker import Faker
from PIL import Image

# Setup directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_DIR = os.path.join(DATA_DIR, "json")
IMAGES_DIR = os.path.join(DATA_DIR, "images")

def create_directories():
    """Membuat direktori penyimpanan dataset jika belum ada."""
    os.makedirs(JSON_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    print("Direktori data/json/ dan data/images/ siap.")

def generate_json_dataset(target_size_kb, file_path, seed=42):
    """
    Menghasilkan file JSON dummy yang berisi data transaksi acak
    menggunakan library Faker hingga ukurannya mendekati target_size_kb.
    """
    print(f"Memulai pembuatan JSON: {file_path} (Target: ~{target_size_kb} KB)...")
    fake = Faker()
    fake.seed_instance(seed)
    
    target_bytes = target_size_kb * 1024
    records = []
    
    # Estimasi kasar: 1 record transaksi rata-rata berukuran ~200 bytes
    estimated_count = max(1, target_bytes // 200)
    for _ in range(estimated_count):
        records.append({
            "transaction_id": fake.uuid4(),
            "name": fake.name(),
            "amount": round(fake.pyfloat(left_digits=5, right_digits=2, positive=True, min_value=10, max_value=10000), 2),
            "timestamp": fake.iso8601(),
            "category": fake.random_element(elements=('Retail', 'Grocery', 'Electronics', 'Utilities', 'Entertainment')),
            "status": fake.random_element(elements=('Completed', 'Pending', 'Failed'))
        })
        
    current_json = json.dumps(records, indent=2)
    current_bytes = len(current_json.encode('utf-8'))
    
    # Tambah data jika ukuran masih di bawah target
    while current_bytes < target_bytes:
        batch_size = max(5, int((target_bytes - current_bytes) / 200))
        for _ in range(batch_size):
            records.append({
                "transaction_id": fake.uuid4(),
                "name": fake.name(),
                "amount": round(fake.pyfloat(left_digits=5, right_digits=2, positive=True, min_value=10, max_value=10000), 2),
                "timestamp": fake.iso8601(),
                "category": fake.random_element(elements=('Retail', 'Grocery', 'Electronics', 'Utilities', 'Entertainment')),
                "status": fake.random_element(elements=('Completed', 'Pending', 'Failed'))
            })
        current_json = json.dumps(records, indent=2)
        current_bytes = len(current_json.encode('utf-8'))
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(current_json)
        
    actual_size_kb = os.path.getsize(file_path) / 1024
    print(f"Selesai! JSON berhasil dibuat: {file_path} ({actual_size_kb:.2f} KB)")
    return actual_size_kb

def generate_image_dataset(target_size_kb, file_path, seed=42):
    """
    Menghasilkan file gambar PNG dummy berisi pixel noise acak
    yang ukurannya mendekati target_size_kb secara presisi menggunakan PIL.
    Menggunakan compression level 0 agar proses cepat dan ukuran file tepat.
    """
    print(f"Memulai pembuatan Gambar: {file_path} (Target: ~{target_size_kb} KB)...")
    random.seed(seed)
    
    target_bytes = target_size_kb * 1024
    
    # Setiap pixel RGB berukuran 3 bytes.
    # Kita cari dimensi width x height sehingga (width * height * 3) ~ target_bytes.
    num_pixels = target_bytes // 3
    side_length = int(math.sqrt(num_pixels))
    
    # Regenerate bytes dengan pseudo-random seed agar reproducible
    total_bytes = side_length * side_length * 3
    random_bytes = random.randbytes(total_bytes)
    
    # Buat image dari bytes
    img = Image.frombytes("RGB", (side_length, side_length), random_bytes)
    
    # Save dengan PNG compression_level=0 (tanpa kompresi) agar ukuran file konsisten dan cepat
    img.save(file_path, "PNG", compress_level=0)
    
    actual_size_kb = os.path.getsize(file_path) / 1024
    print(f"Selesai! Gambar berhasil dibuat: {file_path} ({actual_size_kb:.2f} KB)")
    return actual_size_kb

def main():
    parser = argparse.ArgumentParser(description="Script Persiapan Dataset Cipher Benchmark")
    parser.add_argument("--seed", type=int, default=42, help="Seed acak untuk reproduksibilitas (default: 42)")
    args = parser.parse_args()
    
    create_directories()
    
    # Konfigurasi target ukuran berdasarkan interval pengguna:
    # 1. JSON: Kecil (<500KB) -> 100KB, Sedang (500KB-2MB) -> 1000KB, Besar (>2MB) -> 3000KB
    # 2. Gambar: Kecil (<1MB) -> 500KB, Sedang (1MB-6MB) -> 3000KB, Besar (>6MB) -> 8000KB
    
    scenarios = {
        "json": [
            ("small.json", 100),
            ("medium.json", 1000),
            ("large.json", 3000)
        ],
        "image": [
            ("small.png", 500),
            ("medium.png", 3000),
            ("large.png", 8000)
        ]
    }
    
    print("\n=== Menghasilkan Dataset JSON ===")
    for filename, target_kb in scenarios["json"]:
        file_path = os.path.join(JSON_DIR, filename)
        generate_json_dataset(target_kb, file_path, seed=args.seed)
        
    print("\n=== Menghasilkan Dataset Gambar ===")
    for filename, target_kb in scenarios["image"]:
        file_path = os.path.join(IMAGES_DIR, filename)
        generate_image_dataset(target_kb, file_path, seed=args.seed)
        
    print("\nSemua dataset berhasil dipersiapkan dengan sukses!")

if __name__ == "__main__":
    main()
