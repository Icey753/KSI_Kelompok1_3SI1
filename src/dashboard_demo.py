import base64
import json
from pathlib import Path

from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from src.aead import ALGORITHMS
from src.demo_tools import (
    TAMPER_TARGETS,
    image_encryption_demo,
    nonce_reuse_demo,
    roundtrip_demo,
    tamper_demo,
)

DEFAULT_SAMPLE = json.dumps(
    {"transaction_id": "TRX-0001", "name": "Contoh Pengguna", "amount": 125000.5, "status": "Completed"}
).encode("utf-8")

CARD_STYLE = {
    "backgroundColor": "#1e293b",
    "border": "1px solid #334155",
    "borderRadius": "16px",
    "padding": "1.25rem",
}
MONO = {"fontFamily": "monospace", "fontSize": "0.85rem", "color": "#cbd5e1", "wordBreak": "break-all"}
BUTTON_STYLE = {
    "backgroundColor": "#3b82f6",
    "color": "#f8fafc",
    "border": "none",
    "borderRadius": "10px",
    "padding": "0.6rem 1rem",
    "cursor": "pointer",
    "fontWeight": "600",
}
INPUT_STYLE = {"width": "100%", "backgroundColor": "#0f172a", "color": "#f8fafc", "border": "1px solid #334155",
               "borderRadius": "8px", "padding": "0.5rem", "boxSizing": "border-box"}


def load_plaintext(upload_state: dict | None) -> tuple[bytes, str]:
    if upload_state and upload_state.get("file_path"):
        path = Path(upload_state["file_path"])
        if path.exists():
            return path.read_bytes(), f"file upload: {upload_state.get('input_file_name', path.name)}"
    return DEFAULT_SAMPLE, "data contoh bawaan (upload file untuk memakai data sendiri)"


def _verdict(text: str, ok: bool) -> html.Div:
    color = "#34d399" if ok else "#f87171"
    return html.Div(text, style={"fontSize": "1.25rem", "fontWeight": "800", "color": color, "marginBottom": "0.5rem"})


def _line(label: str, value) -> html.Div:
    return html.Div([html.Span(f"{label}: ", style={"color": "#94a3b8"}), html.Span(str(value), style=MONO)],
                    style={"marginBottom": "0.25rem"})


def render_tamper(result: dict) -> html.Div:
    rejected = result["rejected"]
    verdict = (
        "DITOLAK: integritas terjaga, plaintext tidak dikembalikan"
        if rejected
        else "DITERIMA: BAHAYA, data yang diubah lolos verifikasi"
    )
    return html.Div(
        [
            _verdict(verdict, rejected),
            _line("Algoritma", result["algorithm"]),
            _line("Bagian yang diubah", f"{result['target']} (byte ke-{result['byte_index']}, 1 bit dibalik)"),
            _line("Kontrol (tanpa perubahan) berhasil", "ya" if result["control_ok"] else "tidak"),
            _line("Ciphertext (16 byte awal)", result["ciphertext_preview_hex"]),
            _line("Authentication tag", result["tag_hex"]),
        ]
    )


def render_roundtrip(result: dict) -> html.Div:
    match = result["match"]
    return html.Div(
        [
            _verdict("Hash SHA-256 SAMA: data kembali utuh" if match else "Hash BERBEDA: dekripsi gagal", match),
            _line("Algoritma", result["algorithm"]),
            _line("Key (demo, acak)", result["key_hex"]),
            _line("Nonce", result["nonce_hex"]),
            _line("Ukuran", f"{result['plaintext_bytes']} B plaintext, {result['ciphertext_bytes']} B ciphertext+tag"),
            _line("Ciphertext (32 byte awal)", result["ciphertext_preview_hex"]),
            _line("SHA-256 sebelum enkripsi", result["sha256_before"]),
            _line("SHA-256 sesudah dekripsi", result["sha256_after"]),
        ]
    )


def render_nonce_reuse(results: list[dict]) -> html.Div:
    cards = []
    for result in results:
        cards.append(
            html.Div(
                [
                    _verdict(f"{result['algorithm']}: bocor {result['leaked_bytes']} dari {result['compared_bytes']} byte", False),
                    _line("Persentase bocor", f"{result['leak_fraction'] * 100:.0f}%"),
                    _line("Ciphertext A XOR B (32 byte awal)", result["ciphertext_xor_hex"]),
                    _line("Plaintext B berhasil dipulihkan dari A", "ya" if result["recovered_matches_b"] else "tidak"),
                    _line("Hasil pemulihan", result["recovered_preview"]),
                ],
                style={**CARD_STYLE, "backgroundColor": "#0f172a"},
            )
        )
    return html.Div(cards, style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))", "gap": "1rem"})


def _data_uri(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def render_images(result: dict) -> html.Div:
    def figure(title: str, png: bytes) -> html.Div:
        return html.Div(
            [html.Div(title, style={"color": "#94a3b8", "marginBottom": "0.4rem"}),
             html.Img(src=_data_uri(png), style={"maxWidth": "100%", "borderRadius": "8px", "imageRendering": "pixelated"})]
        )

    return html.Div(
        [
            html.Div(
                [figure("Gambar asli", result["original_png"]), figure("Ciphertext dirender sebagai piksel", result["cipher_png"])],
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))", "gap": "1rem"},
            ),
            _line("Ukuran tampilan", f"{result['width']} x {result['height']} piksel (thumbnail)"),
            _line("SHA-256 ciphertext", result["ciphertext_sha256"]),
        ]
    )


def _panel(title: str, description: str, controls: list, button_id: str, button_label: str, result_id: str) -> html.Div:
    return html.Div(
        [
            html.H3(title, style={"marginTop": 0}),
            html.P(description, style={"color": "#94a3b8", "marginTop": 0}),
            *controls,
            html.Button(button_label, id=button_id, n_clicks=0, style={**BUTTON_STYLE, "marginTop": "0.75rem"}),
            html.Div(id=result_id, style={"marginTop": "1rem"}),
        ],
        style=CARD_STYLE,
    )


def build_demo_section() -> html.Div:
    return html.Div(
        [
            html.H2("Demo Interaktif", style={"marginBottom": "0.25rem"}),
            html.P(
                "Demo memakai file yang diunggah di atas; bila belum ada, dipakai data contoh. Key dan nonce dibuat acak setiap klik.",
                style={"color": "#94a3b8", "marginTop": 0},
            ),
            html.Div(
                [
                    html.Span("Algoritma: ", style={"marginRight": "0.5rem"}),
                    dcc.RadioItems(id="demo-algorithm", options=list(ALGORITHMS), value=ALGORITHMS[0], inline=True,
                                   inputStyle={"marginRight": "0.3rem", "marginLeft": "1rem"}),
                ],
                style={**CARD_STYLE, "marginBottom": "1rem"},
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(340px, 1fr))", "gap": "1rem", "marginBottom": "1.5rem"},
                children=[
                    _panel(
                        "1. Uji tamper (perubahan data)",
                        "Balik 1 bit pada bagian yang dipilih lalu coba dekripsi. AEAD harus menolaknya.",
                        [
                            dcc.Dropdown(id="demo-tamper-target", options=[{"label": t, "value": t} for t in TAMPER_TARGETS],
                                         value="ciphertext", clearable=False, style={"color": "#0f172a", "marginBottom": "0.5rem"}),
                            dcc.Input(id="demo-tamper-byte", type="number", min=0, step=1, value=0, style=INPUT_STYLE),
                        ],
                        "demo-tamper-run", "Ubah 1 bit lalu dekripsi", "demo-tamper-result",
                    ),
                    _panel(
                        "2. Enkripsi lalu dekripsi balik",
                        "Bukti data kembali utuh: bandingkan hash SHA-256 sebelum dan sesudah.",
                        [],
                        "demo-roundtrip-run", "Enkripsi dan dekripsi", "demo-roundtrip-result",
                    ),
                    _panel(
                        "3. Bahaya nonce dipakai ulang",
                        "Dua pesan dienkripsi dengan key dan nonce yang sama, lalu XOR ciphertext dibandingkan dengan XOR plaintext. Kedua algoritma dijalankan.",
                        [
                            dcc.Input(id="demo-nonce-text-a", type="text", value="Transfer Rp 5.000.000 ke rekening A", style={**INPUT_STYLE, "marginBottom": "0.5rem"}),
                            dcc.Input(id="demo-nonce-text-b", type="text", value="Transfer Rp 9.999.999 ke rekening B", style=INPUT_STYLE),
                        ],
                        "demo-nonce-run", "Jalankan demo nonce reuse", "demo-nonce-result",
                    ),
                    _panel(
                        "4. Gambar asli vs ciphertext",
                        "Piksel gambar yang diunggah dienkripsi, lalu ciphertext-nya dirender sebagai gambar. Hanya untuk file gambar.",
                        [],
                        "demo-image-run", "Enkripsi gambar", "demo-image-result",
                    ),
                ],
            ),
        ]
    )


def _warn(message: str) -> html.Div:
    return html.Div(message, style={"color": "#fbbf24"})


def _run_image_demo(algorithm, upload_state) -> html.Div:
    if not upload_state or upload_state.get("file_type") != "image":
        return _warn("Unggah file gambar (PNG/JPG/WEBP/GIF/BMP) di bagian upload terlebih dahulu.")
    try:
        result = image_encryption_demo(algorithm, upload_state["file_path"])
    except (OSError, ValueError) as error:
        return _warn(f"Gambar tidak bisa dibaca: {error}")
    return render_images(result)


def _source_note(source: str) -> html.Div:
    return html.Div(f"Sumber: {source}", style={"color": "#94a3b8", "marginBottom": "0.5rem"})


def register_demo_callbacks(app) -> None:
    @app.callback(
        Output("demo-tamper-result", "children"),
        Input("demo-tamper-run", "n_clicks"),
        State("demo-algorithm", "value"),
        State("demo-tamper-target", "value"),
        State("demo-tamper-byte", "value"),
        State("upload-state", "data"),
        prevent_initial_call=True,
    )
    def run_tamper(n_clicks, algorithm, target, byte_index, upload_state):
        if not n_clicks:
            raise PreventUpdate
        plaintext, source = load_plaintext(upload_state)
        try:
            result = tamper_demo(algorithm, plaintext, target, int(byte_index or 0))
        except ValueError as error:
            return _warn(str(error))
        return html.Div([_source_note(source), render_tamper(result)])

    @app.callback(
        Output("demo-roundtrip-result", "children"),
        Input("demo-roundtrip-run", "n_clicks"),
        State("demo-algorithm", "value"),
        State("upload-state", "data"),
        prevent_initial_call=True,
    )
    def run_roundtrip(n_clicks, algorithm, upload_state):
        if not n_clicks:
            raise PreventUpdate
        plaintext, source = load_plaintext(upload_state)
        return html.Div([_source_note(source), render_roundtrip(roundtrip_demo(algorithm, plaintext))])

    @app.callback(
        Output("demo-nonce-result", "children"),
        Input("demo-nonce-run", "n_clicks"),
        State("demo-nonce-text-a", "value"),
        State("demo-nonce-text-b", "value"),
        prevent_initial_call=True,
    )
    def run_nonce_reuse(n_clicks, text_a, text_b):
        if not n_clicks:
            raise PreventUpdate
        if not text_a or not text_b:
            return _warn("Isi kedua pesan terlebih dahulu.")
        if text_a == text_b:
            return _warn("Isi dua pesan yang berbeda; pesan identik menghasilkan ciphertext identik.")
        a, b = text_a.encode("utf-8"), text_b.encode("utf-8")
        return render_nonce_reuse([nonce_reuse_demo(algorithm, a, b) for algorithm in ALGORITHMS])

    @app.callback(
        Output("demo-image-result", "children"),
        Input("demo-image-run", "n_clicks"),
        State("demo-algorithm", "value"),
        State("upload-state", "data"),
        prevent_initial_call=True,
    )
    def run_image(n_clicks, algorithm, upload_state):
        if not n_clicks:
            raise PreventUpdate
        return _run_image_demo(algorithm, upload_state)
