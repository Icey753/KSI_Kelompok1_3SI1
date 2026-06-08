from src.benchmark import run_single_file_benchmark


if __name__ == "__main__":
    results = run_single_file_benchmark(
        "data/images/large.png",
        "image",
        "large",
        warm_ups=0,
        iterations=1,
    )
    for row in results:
        print(row)
