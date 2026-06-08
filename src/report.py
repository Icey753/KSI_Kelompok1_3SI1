import os
import pandas as pd

# Setup directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
RESULTS_DIR = os.path.join(OUTPUT_DIR, "results")

def save_benchmark_results(results_list: list[dict], filename: str = "benchmark_results.csv") -> str:
    """
    Saves a list of benchmark result dicts to a CSV file in output/results/.
    
    Args:
        results_list (list[dict]): The gathered benchmark results
        filename (str): The name of the CSV file
        
    Returns:
        str: Absolute path to the saved CSV file
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    df = pd.DataFrame(results_list)
    output_path = os.path.join(RESULTS_DIR, filename)
    df.to_csv(output_path, index=False)
    print(f"\nLaporan hasil benchmark berhasil disimpan ke: {output_path}")
    return output_path

if __name__ == "__main__":
    # Self-test
    test_results = [
        {
            "Algorithm": "AES-GCM",
            "FileType": "json",
            "SizeCategory": "small",
            "PlaintextSizeBytes": 1024,
            "CiphertextSizeBytes": 1040,
            "EncLatencyMeanMs": 0.05,
            "EncLatencyStdMs": 0.005,
            "DecLatencyMeanMs": 0.06,
            "DecLatencyStdMs": 0.006,
            "OverheadBytes": 16,
            "OverheadPct": 1.56,
            "TamperingIntegrityPassed": True
        }
    ]
    path = save_benchmark_results(test_results, "test_results.csv")
    assert os.path.exists(path), "Report file was not saved!"
    # clean up test file
    os.unlink(path)
    print("Report self-test completed successfully!")
