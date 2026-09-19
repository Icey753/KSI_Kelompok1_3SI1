from src.benchmark import _build_result_row


def test_row_has_median_ci_iterations_and_samples():
    row = _build_result_row(
        algorithm="AES-GCM",
        file_type="json",
        size_category="small",
        input_file_name="f.json",
        plaintext_size=100,
        ciphertext_size=116,
        enc_times=[1.0, 2.0, 3.0],
        dec_times=[2.0, 2.0, 2.0],
        overhead_bytes=16,
        overhead_pct=16.0,
        tampering_passed=True,
    )
    assert row["Iterations"] == 3
    assert row["EncLatencyMedianMs"] == 2.0
    assert row["DecLatencyCI95Ms"] == 0.0
    assert row["EncLatencyCI95Ms"] > 0
    assert row["_EncSamplesMs"] == [1.0, 2.0, 3.0]
    assert row["_DecSamplesMs"] == [2.0, 2.0, 2.0]
