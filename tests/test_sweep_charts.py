import pandas as pd

from src.sweep_charts import generate_boxplot, generate_sweep_chart


def test_sweep_chart_written(tmp_path):
    csv = tmp_path / "summary.csv"
    pd.DataFrame(
        {
            "Kind": ["json"] * 3,
            "SizeBytes": [1024, 16384, 262144],
            "AesEncMedianMs": [0.07, 0.10, 1.0],
            "AsconEncMedianMs": [0.02, 0.09, 2.5],
            "RatioAsconOverAes": [0.29, 0.9, 2.5],
            "EncPValue": [0.001, 0.02, 0.0001],
        }
    ).to_csv(csv, index=False)
    out = generate_sweep_chart(str(csv), str(tmp_path / "charts" / "sweep.png"))
    assert (tmp_path / "charts" / "sweep.png").stat().st_size > 1000
    assert out.endswith("sweep.png")


def test_boxplot_written(tmp_path):
    csv = tmp_path / "raw.csv"
    records = [
        {"Algorithm": alg, "InputFileName": "a.json", "Op": "enc", "Iteration": i, "LatencyMs": v + i * 0.01}
        for alg, v in (("AES-GCM", 1.0), ("Ascon-128", 2.0))
        for i in range(10)
    ]
    pd.DataFrame(records).to_csv(csv, index=False)
    generate_boxplot(str(csv), str(tmp_path / "box.png"))
    assert (tmp_path / "box.png").stat().st_size > 1000
