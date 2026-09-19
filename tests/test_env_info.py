import json

from src.env_info import collect_env_info, save_env_info


def test_collect_env_info_keys_and_speedup():
    info = collect_env_info(aesni_repeats=1)
    for key in ("python", "platform", "processor", "cpu_count", "pycryptodome", "ascon_backend", "ascon_variant", "aesni_speedup"):
        assert key in info
    assert info["aesni_speedup"] > 0


def test_save_env_info_writes_json(tmp_path):
    path = save_env_info(str(tmp_path / "env.json"))
    assert json.loads(open(path, encoding="utf-8").read())["ascon_backend"]
