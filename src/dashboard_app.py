import base64
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, dash_table, no_update
from dash.dash_table.Format import Format, Group, Scheme
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from src.benchmark import run_uploaded_file_benchmark
from src.dashboard_analysis import build_analysis_section, register_analysis_callbacks
from src.dashboard_demo import build_demo_section, register_demo_callbacks
from src.dashboard_scenarios import build_scenarios_section, register_scenarios_callbacks
from src.dashboard_theme import ALGORITHM_COLORS, FONT_UI, TOKENS, chart_layout, root_css
from src.dashboard_safety import MAX_UPLOAD_BYTES, UPLOADS_DIR, is_within_uploads, trusted_upload
from src.report import save_benchmark_results

BASE_DIR = Path(__file__).resolve().parent.parent

EXPECTED_COLUMNS = [
    "Algorithm",
    "InputFileName",
    "FileType",
    "SizeCategory",
    "PlaintextSizeBytes",
    "CiphertextSizeBytes",
    "EncLatencyMeanMs",
    "EncLatencyStdMs",
    "DecLatencyMeanMs",
    "DecLatencyStdMs",
    "OverheadBytes",
    "OverheadPct",
    "TamperingIntegrityPassed",
]

FILE_TYPE_LABELS = {
    "json": "JSON",
    "image": "Gambar",
}

SIZE_ORDER = ["small", "medium", "large"]
CHART_HEIGHT = 400  # px, reserved before the figure arrives, so charts do not shift the page

# Same precision as the metric cards: 3 decimals for ms, 2 for percent.
COUNT = Format(precision=0, scheme=Scheme.fixed, group=Group.yes)
MILLIS = Format(precision=3, scheme=Scheme.fixed)
PERCENT = Format(precision=2, scheme=Scheme.fixed)
SIZE_LABELS = {"small": "Kecil", "medium": "Sedang", "large": "Besar"}


def _safe_stem(file_name: str) -> str:
    stem = Path(file_name).stem or "upload"
    safe_chars = []
    for character in stem:
        if character.isalnum() or character in {"-", "_"}:
            safe_chars.append(character)
        else:
            safe_chars.append("_")
    return "".join(safe_chars).strip("._") or "upload"


def _ensure_expected_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in EXPECTED_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = "" if column == "InputFileName" else pd.NA
    normalized = normalized[EXPECTED_COLUMNS]
    return normalized


def _load_base_dataframe(csv_path: str | None) -> pd.DataFrame:
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return _ensure_expected_columns(df)
    return pd.DataFrame(columns=EXPECTED_COLUMNS)


def _decode_upload(contents: str) -> tuple[str, bytes]:
    header, encoded = contents.split(",", 1)
    raw_bytes = base64.b64decode(encoded, validate=True)
    return header, raw_bytes


def _display_path(path: str) -> str:
    try:
        return Path(path).resolve().relative_to(BASE_DIR).as_posix()
    except ValueError:
        return str(path)


def _rejected(message: str, previous: dict | None):
    """Upload refused: keep whatever was active, and say so."""
    if previous and previous.get("input_file_name"):
        message += f" File sebelumnya ({previous['input_file_name']}) tetap dipakai."
    return no_update, no_update, _error(message)


def _error(message: str) -> html.Div:
    return html.Div(message, role="alert", className="status status--error")


def _detect_file_type(filename: str, header: str) -> str | None:
    suffix = Path(filename).suffix.lower()
    if suffix == ".json" or "application/json" in header:
        return "json"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"} or header.startswith("data:image/"):
        return "image"
    return None


def _classify_size(file_type: str, size_bytes: int) -> str:
    if file_type == "json":
        if size_bytes < 500 * 1024:
            return "small"
        if size_bytes < 2 * 1024 * 1024:
            return "medium"
        return "large"

    if size_bytes < 1 * 1024 * 1024:
        return "small"
    if size_bytes < 6 * 1024 * 1024:
        return "medium"
    return "large"


def _make_preview(contents: str, filename: str, file_type: str, size_bytes: int) -> html.Div:
    file_label = FILE_TYPE_LABELS.get(file_type, file_type.upper())
    meta = html.Div(
        [
            html.Div(f"Nama file: {filename}"),
            html.Div(f"Tipe: {file_label}"),
            html.Div(f"Ukuran: {size_bytes / 1024:.2f} KB"),
        ],
        style={"lineHeight": "1.7"},
    )

    if file_type == "image":
        return html.Div(
            [
                meta,
                html.Div(
                    html.Img(
                        src=contents,
                        style={
                            "maxWidth": "100%",
                            "borderRadius": "12px",
                            "marginTop": "1rem",
                            "border": "1px solid var(--border)",
                        },
                    ),
                    style={"marginTop": "0.75rem"},
                ),
            ]
        )

    header, encoded = contents.split(",", 1)
    preview_text = base64.b64decode(encoded).decode("utf-8", errors="replace")
    preview_text = preview_text[:1200] + ("..." if len(preview_text) > 1200 else "")
    return html.Div(
        [
            meta,
            html.Pre(
                preview_text,
                style={
                    "whiteSpace": "pre-wrap",
                    "backgroundColor": "var(--bg)",
                    "border": "1px solid var(--border)",
                    "borderRadius": "12px",
                    "padding": "1rem",
                    "marginTop": "1rem",
                    "maxHeight": "280px",
                    "overflowY": "auto",
                },
            ),
        ]
    )


def _build_metric_card(label: str, value: str) -> html.Div:
    return html.Div(
        [html.Div(label, className="metric__label"), html.Div(value, className="metric__value")],
        className="card",
    )


def _build_metrics_panel(df: pd.DataFrame, state: dict | None) -> html.Div:
    source_label = "CSV benchmark"
    file_name = "-"
    if state:
        source_label = state.get("source_label", source_label)
        file_name = state.get("input_file_name", file_name)

    if df.empty:
        enc = dec = overhead = tamper = "–"
    else:
        pass_count = int(df["TamperingIntegrityPassed"].fillna(False).astype(bool).sum())
        total_rows = len(df)
        pass_rate = (pass_count / total_rows) * 100 if total_rows else 0.0
        enc = f"{df['EncLatencyMeanMs'].mean():.3f} ms"
        dec = f"{df['DecLatencyMeanMs'].mean():.3f} ms"
        overhead = f"{df['OverheadPct'].mean():.2f}%"
        tamper = f"{pass_count} / {total_rows} ({pass_rate:.0f}%)"

    metrics = [
        _build_metric_card("Rata-rata enkripsi", enc),
        _build_metric_card("Rata-rata dekripsi", dec),
        _build_metric_card("Overhead rata-rata", overhead),
        _build_metric_card("Lolos uji tamper", tamper),
    ]
    return html.Div(
        [
            html.P(
                [
                    "Sumber data: ",
                    html.Strong(source_label),
                    " \u00b7 File aktif: ",
                    html.Strong(file_name),
                ],
                className="source-line",
            ),
            html.Div(metrics, className="grid grid--metrics"),
        ]
    )


def _select_active_dataframe(df: pd.DataFrame, selected_file_type: str | None) -> pd.DataFrame:
    if df.empty:
        return df

    if selected_file_type and selected_file_type in set(df["FileType"].dropna().tolist()):
        filtered = df[df["FileType"] == selected_file_type].copy()
    else:
        filtered = df.copy()

    filtered["SizeCategory"] = pd.Categorical(filtered["SizeCategory"], categories=SIZE_ORDER, ordered=True)
    return filtered.sort_values(["SizeCategory", "Algorithm"])


def _empty_figure(title: str, message: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        **chart_layout(margin=dict(l=40, r=20, t=50, b=40)),
        title=title,
        annotations=[
            dict(
                text=message,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(color=TOKENS["text_2"], size=14),
            )
        ],
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _build_latency_figure(df: pd.DataFrame, column: str, error_column: str, title: str, y_axis_title: str) -> go.Figure:
    if df.empty:
        return _empty_figure(title, "Belum ada data untuk ditampilkan.")

    fig = go.Figure()
    palette = {
        "AES-GCM": (ALGORITHM_COLORS["AES-GCM"], TOKENS["aes_strong"]),
        "Ascon-128": (ALGORITHM_COLORS["Ascon-128"], TOKENS["ascon_strong"]),
    }

    for algorithm, (base_color, accent_color) in palette.items():
        algo_df = df[df["Algorithm"] == algorithm]
        if algo_df.empty:
            continue
        fig.add_trace(
            go.Bar(
                x=algo_df["SizeCategory"].astype(str).map(lambda v: SIZE_LABELS.get(v, v)),
                y=algo_df[column],
                name=algorithm,
                marker_color=base_color,
                error_y=dict(type="data", array=algo_df[error_column], visible=True, color=accent_color),
            )
        )

    if not fig.data:
        return _empty_figure(title, "Tidak ada algoritma yang cocok dengan filter aktif.")

    fig.update_layout(
        **chart_layout(height=CHART_HEIGHT, margin=dict(l=40, r=20, t=20, b=120)),
        xaxis_title="Kategori Ukuran",
        yaxis_title=y_axis_title,
    )
    return fig


def _build_overhead_figure(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure("Overhead Ciphertext", "Belum ada data untuk ditampilkan.")

    fig = go.Figure()
    palette = {
        "AES-GCM": ALGORITHM_COLORS["AES-GCM"],
        "Ascon-128": ALGORITHM_COLORS["Ascon-128"],
    }

    for algorithm, color in palette.items():
        algo_df = df[df["Algorithm"] == algorithm]
        if algo_df.empty:
            continue
        fig.add_trace(
            go.Bar(
                x=algo_df["SizeCategory"].astype(str).map(lambda v: SIZE_LABELS.get(v, v)),
                y=algo_df["OverheadPct"],
                name=algorithm,
                marker_color=color,
                text=[f"{value:.2f}%" for value in algo_df["OverheadPct"]],
                textposition="auto",
            )
        )

    if not fig.data:
        return _empty_figure("Overhead Ciphertext", "Tidak ada algoritma yang cocok dengan filter aktif.")

    fig.update_layout(
        **chart_layout(height=CHART_HEIGHT, margin=dict(l=40, r=20, t=20, b=120)),
        xaxis_title="Kategori Ukuran",
        yaxis_title="Overhead (%)",
    )
    return fig


def _artifact_card(algorithm: str, artifact: dict | None, tone: str) -> html.Div:
    if not artifact:
        return html.Div(
            [
                html.H4(algorithm, className="tone-title", style={"margin": "0 0 0.5rem 0", "fontSize": "1rem"}),
                html.Div("Jalankan benchmark upload untuk mengaktifkan unduhan."),
            ],
            className=f"card tone-{tone}",
        )

    slug = algorithm.lower().replace("-", "_")
    return html.Div(
        [
            html.H4(algorithm, className="tone-title", style={"margin": "0 0 0.75rem 0", "fontSize": "1rem"}),
            html.Div(f"Ciphertext Base64: {artifact.get('ciphertext_filename', '-')}", style={"marginBottom": "0.4rem"}),
            html.Div(f"Metadata: {artifact.get('metadata_filename', '-')}", style={"marginBottom": "1rem"}),
            html.Div(
                [
                    html.Button(
                        "Unduh Ciphertext Base64",
                        id=f"download-{slug}-ciphertext",
                        n_clicks=0,
                        className="btn btn--pill btn--accent",
                    ),
                    html.Button(
                        "Unduh Metadata",
                        id=f"download-{slug}-metadata",
                        n_clicks=0,
                        className="btn btn--pill btn--outline",
                    ),
                ],
                className="btn-row",
            ),
        ],
        className=f"card tone-{tone}",
    )


def _build_artifact_panel(state: dict | None) -> html.Div:
    if not state or not state.get("artifacts"):
        return html.Div()

    artifacts = state["artifacts"]
    return html.Div(
        [
            html.H3("Artefak Enkripsi", className="card-title"),
            html.Div(
                [
                    _artifact_card("AES-GCM", artifacts.get("AES-GCM"), "aes"),
                    _artifact_card("Ascon-128", artifacts.get("Ascon-128"), "ascon"),
                ],
                className="grid grid--pair",
            ),
        ]
    )


def _state_to_dataframe(state: dict | None, fallback_df: pd.DataFrame) -> pd.DataFrame:
    if state and state.get("rows"):
        df = pd.DataFrame(state["rows"])
        return _ensure_expected_columns(df)
    return fallback_df.copy()


def _load_selected_file_type(state: dict | None) -> str:
    if not state:
        return "json"
    return state.get("file_type", "json")


def _build_initial_state(csv_path: str | None) -> dict:
    base_df = _load_base_dataframe(csv_path)
    return {
        "source": "csv",
        "source_label": "CSV benchmark",
        "input_file_name": Path(csv_path).name if csv_path else "benchmark_results.csv",
        "rows": base_df.to_dict("records"),
        "artifacts": {},
        "csv_path": csv_path,
    }


def build_dash_app(csv_path: str | None) -> dash.Dash:
    app = dash.Dash(
        __name__,
        title="Benchmark AES-GCM vs Ascon-128",
        assets_folder=str(BASE_DIR / "assets"),
    )
    app.config.suppress_callback_exceptions = True
    preload = '<link rel="preload" href="/assets/fonts/inter-latin-var.woff2" as="font" type="font/woff2" crossorigin>'
    app.index_string = app.index_string.replace("<html>", '<html lang="id">').replace(
        "</head>", f"{preload}<style>{root_css()}</style></head>"
    )

    base_state = _build_initial_state(csv_path)
    base_df = _state_to_dataframe(base_state, pd.DataFrame(columns=EXPECTED_COLUMNS))

    app.layout = html.Main(
        className="page",
        children=[
            dcc.Store(id="upload-state"),
            dcc.Store(id="benchmark-state", data=base_state),
            dcc.Download(id="download-aes-gcm-ciphertext"),
            dcc.Download(id="download-aes-gcm-metadata"),
            dcc.Download(id="download-ascon-128-ciphertext"),
            dcc.Download(id="download-ascon-128-metadata"),
            html.Header(
                className="hero",
                children=[
                    html.H1("AES-GCM vs Ascon-128 Benchmark Dashboard", className="hero__title"),
                    html.P(
                        "Dashboard ini mendukung upload langsung file JSON atau gambar, menjalankan benchmark, lalu menyimpan ciphertext dan metadata yang bisa diunduh untuk demo.",
                        className="muted",
                        style={"margin": "0"},
                    ),
                    html.Nav(
                        [
                            html.A("Benchmark File", href="#hasil", className="chip"),
                            html.A("Demo Interaktif", href="#demo", className="chip"),
                            html.A("Analisis Ukuran Data", href="#analisis", className="chip"),
                            html.A("Skenario Realistis", href="#skenario", className="chip"),
                        ],
                        className="chips",
                        **{"aria-label": "Lompat ke bagian"},
                    ),
                ],
            ),
            html.Section(
                id="hasil",
                className="section",
                children=[
                    html.Header(html.H2("Benchmark File", className="section__title"), className="section__head"),
                    html.Div(
                        className="stack",
                        children=[
                            html.Div(
                                className="grid grid--pair",
                                children=[
                                    html.Div(
                                        className="card",
                                        children=[
                                            html.H3("Upload File", className="card-title"),
                                            dcc.Upload(
                                                id="upload-data",
                                                children=html.Div(
                                                    [
                                                        html.Div("Seret file ke sini atau klik untuk memilih"),
                                                        html.Div(
                                                            f"JSON atau gambar (PNG, JPG, WEBP, GIF, BMP), maksimal {MAX_UPLOAD_BYTES // 1024 // 1024} MB",
                                                            className="muted muted--sm",
                                                        ),
                                                    ]
                                                ),
                                                className="dropzone",
                                                multiple=False,
                                                accept=".json,.png,.jpg,.jpeg,.webp,.gif,.bmp",
                                                max_size=MAX_UPLOAD_BYTES,
                                            ),
                                            html.Div(id="upload-status", role="status", className="status", style={"marginTop": "0.85rem"}),
                                        ],
                                    ),
                                    html.Div(
                                        className="card",
                                        children=[
                                            html.H3("Aksi Benchmark", className="card-title"),
                                            html.P(
                                                "Setelah file diunggah, tekan tombol di bawah untuk menjalankan AES-GCM dan Ascon-128 pada file yang sama.",
                                                className="muted",
                                                style={"margin": "0 0 1rem"},
                                            ),
                                            html.Button(
                                                "Jalankan Benchmark",
                                                id="run-benchmark",
                                                n_clicks=0,
                                                className="btn btn--pill btn--go",
                                            ),
                                            dcc.Loading(html.Div(id="benchmark-status", role="status", className="status", style={"marginTop": "0.85rem"})),
                                        ],
                                    ),
                                ],
                            ),
                            html.Div(id="upload-preview"),
                            html.Div(
                                className="toolbar",
                                children=[
                                    html.Div(
                                        className="toolbar__filter",
                                        children=[
                                            html.Label("Tipe file", id="file-type-label", className="field-label"),
                                            dcc.Dropdown(
                                                id="file-type-dropdown",
                                                options=[
                                                    {"label": "JSON", "value": "json"},
                                                    {"label": "Gambar", "value": "image"},
                                                ],
                                                value=_load_selected_file_type(base_state),
                                                clearable=False,
                                                style={"color": "var(--bg)"},
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        "Grafik dan tabel mengikuti tipe file yang dipilih. Jika hasil upload hanya punya satu tipe, itu yang ditampilkan.",
                                        className="muted muted--sm toolbar__note",
                                    ),
                                ],
                            ),
                            html.Div(id="overview-metrics"),
                            html.Div(
                                className="grid grid--triple",
                                children=[
                                    html.Div(
                                        className="card",
                                        children=[
                                            html.H3("Latensi Enkripsi", className="card-title"),
                                            html.P("Batang lebih rendah berarti lebih cepat. Garis error: simpangan baku antar iterasi.", className="muted muted--sm", style={"marginTop": 0}),
                                            dcc.Graph(id="encryption-latency-graph", style={"height": f"{CHART_HEIGHT}px"}),
                                        ],
                                    ),
                                    html.Div(
                                        className="card",
                                        children=[
                                            html.H3("Latensi Dekripsi", className="card-title"),
                                            html.P("Sudah termasuk verifikasi tag autentikasi.", className="muted muted--sm", style={"marginTop": 0}),
                                            dcc.Graph(id="decryption-latency-graph", style={"height": f"{CHART_HEIGHT}px"}),
                                        ],
                                    ),
                                    html.Div(
                                        className="card",
                                        children=[
                                            html.H3("Overhead Ciphertext", className="card-title"),
                                            html.P("Tambahan ukuran ciphertext dibanding plaintext, dalam persen. Lebih rendah berarti lebih hemat.", className="muted muted--sm", style={"marginTop": 0}),
                                            dcc.Graph(id="overhead-graph", style={"height": f"{CHART_HEIGHT}px"}),
                                        ],
                                    ),
                                ],
                            ),
                            html.Div(
                                className="card",
                                children=[
                                    html.H3("Tabel Hasil Benchmark", className="card-title"),
                                    dash_table.DataTable(
                        id="benchmark-table",
                        columns=[
                            {"name": "Algoritma", "id": "Algorithm"},
                            {"name": "File input", "id": "InputFileName"},
                            {"name": "Kategori ukuran", "id": "SizeCategory"},
                            {"name": "Plaintext (byte)", "id": "PlaintextSizeBytes", "type": "numeric", "format": COUNT},
                            {"name": "Ciphertext (byte)", "id": "CiphertextSizeBytes", "type": "numeric", "format": COUNT},
                            {"name": "Enkripsi (ms)", "id": "EncLatencyMeanMs", "type": "numeric", "format": MILLIS},
                            {"name": "Dekripsi (ms)", "id": "DecLatencyMeanMs", "type": "numeric", "format": MILLIS},
                            {"name": "Overhead (byte)", "id": "OverheadBytes", "type": "numeric", "format": COUNT},
                            {"name": "Overhead (%)", "id": "OverheadPct", "type": "numeric", "format": PERCENT},
                            {"name": "Uji tamper", "id": "TamperingIntegrityPassed"},
                        ],
                        data=base_df.to_dict("records"),
                        style_header={
                            "backgroundColor": TOKENS["bg"],
                            "color": TOKENS["text_2"],
                            "fontWeight": "bold",
                            "border": f"1px solid {TOKENS['border']}",
                        },
                        style_filter={
                            "backgroundColor": TOKENS["bg"],
                            "color": TOKENS["text"],
                            "border": f"1px solid {TOKENS['border']}",
                        },
                        css=[
                            {"selector": ".dash-filter input", "rule": f"color: {TOKENS['text']} !important; background-color: {TOKENS['bg']} !important;"},
                            {"selector": ".dash-filter input::placeholder", "rule": f"color: {TOKENS['text_muted']} !important; opacity: 1 !important;"},
                            {"selector": ".dash-filter--case", "rule": "display: none !important;"},
                            {"selector": "td, th", "rule": "font-variant-numeric: tabular-nums;"},
                        ],
                        style_cell={
                            "backgroundColor": TOKENS["surface"],
                            "color": TOKENS["text_2"],
                            "border": f"1px solid {TOKENS['border']}",
                            "padding": "10px",
                            "fontFamily": FONT_UI,
                            "whiteSpace": "normal",
                            "height": "auto",
                            "textAlign": "left",
                        },
                        style_header_conditional=[
                            {"if": {"column_type": "numeric"}, "textAlign": "right"},
                        ],
                        style_filter_conditional=[
                            {"if": {"column_type": "numeric"}, "textAlign": "right"},
                        ],
                        style_cell_conditional=[
                            {"if": {"column_type": "numeric"}, "textAlign": "right"},
                        ],
                        style_data_conditional=[
                            {
                                "if": {"column_id": "TamperingIntegrityPassed", "filter_query": "{TamperingIntegrityPassed} = True"},
                                "color": TOKENS["ok"],
                                "fontWeight": "700",
                            },
                            {
                                "if": {"column_id": "Algorithm", "filter_query": "{Algorithm} = 'AES-GCM'"},
                                "color": ALGORITHM_COLORS["AES-GCM"],
                            },
                            {
                                "if": {"column_id": "Algorithm", "filter_query": "{Algorithm} = 'Ascon-128'"},
                                "color": ALGORITHM_COLORS["Ascon-128"],
                            },
                        ],
                        tooltip_header={
                            "EncLatencyMeanMs": "Rata-rata latensi enkripsi, dalam milidetik",
                            "DecLatencyMeanMs": "Rata-rata latensi dekripsi, dalam milidetik",
                            "TamperingIntegrityPassed": "True jika data yang diubah ditolak saat dekripsi",
                        },
                        page_size=10,
                        sort_action="native",
                        filter_action="native",
                        filter_options={"placeholder_text": "Saring...", "case": "insensitive"},
                        style_table={"overflowX": "auto"},
                    ),
                                ],
                            ),
                            html.Div(id="artifact-panel"),
                        ],
                    ),
                ],
            ),
            build_demo_section(),
            build_analysis_section(),
            build_scenarios_section(),
        ],
    )

    @app.callback(
        Output("upload-state", "data"),
        Output("upload-preview", "children"),
        Output("upload-status", "children"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        State("upload-data", "last_modified"),
        State("upload-state", "data"),
        prevent_initial_call=True,
    )
    def handle_upload(contents, filename, last_modified, previous):
        if not contents or not filename:
            raise PreventUpdate

        try:
            header, raw_bytes = _decode_upload(contents)
        except ValueError:
            return _rejected("File rusak atau tidak terbaca. Coba unggah ulang.", previous)
        file_type = _detect_file_type(filename, header)
        if file_type is None:
            return _rejected("Format file tidak didukung. Gunakan JSON, PNG, JPG, JPEG, WEBP, GIF, atau BMP.", previous)

        size_bytes = len(raw_bytes)
        if size_bytes == 0:
            return _rejected("File kosong (0 byte). Pilih file yang berisi data.", previous)
        if size_bytes > MAX_UPLOAD_BYTES:
            return _rejected(
                f"File terlalu besar ({size_bytes / 1024 / 1024:.1f} MB). Batas {MAX_UPLOAD_BYTES // 1024 // 1024} MB.", previous
            )
        size_category = _classify_size(file_type, size_bytes)

        session_dir = UPLOADS_DIR / uuid.uuid4().hex
        session_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _safe_stem(filename) + Path(filename).suffix.lower()
        file_path = session_dir / safe_name
        file_path.write_bytes(raw_bytes)

        preview = _make_preview(contents, filename, file_type, size_bytes)
        status = html.Div(
            f"File berhasil diunggah. Kategori ukuran: {SIZE_LABELS.get(size_category, size_category)}.",
            className="status status--ok",
        )

        upload_state = {
            "source": "upload",
            "source_label": "Upload file",
            "input_file_name": filename,
            "file_name": filename,
            "file_path": str(file_path),
            "session_dir": str(session_dir),
            "file_type": file_type,
            "size_category": size_category,
            "size_bytes": size_bytes,
            "mime_header": header,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "last_modified": last_modified,
        }
        return upload_state, preview, status

    @app.callback(
        Output("benchmark-state", "data"),
        Output("benchmark-status", "children"),
        Input("run-benchmark", "n_clicks"),
        State("upload-state", "data"),
        running=[(Output("run-benchmark", "disabled"), True, False)],
        prevent_initial_call=True,
    )
    def run_benchmark(n_clicks, upload_state):
        if not n_clicks:
            raise PreventUpdate

        upload_state = trusted_upload(upload_state)
        if not upload_state:
            return no_update, html.Div(
                "Unggah file JSON atau gambar terlebih dahulu sebelum menjalankan benchmark.",
                className="status status--warn",
            )

        file_path = upload_state["file_path"]
        file_name = upload_state["input_file_name"]
        file_type = upload_state["file_type"]
        size_category = upload_state["size_category"]

        iteration_plan = {
            "small": {"iterations": 10, "warm_ups": 3},
            "medium": {"iterations": 5, "warm_ups": 1},
            "large": {"iterations": 1, "warm_ups": 0},
        }
        plan = iteration_plan.get(size_category, iteration_plan["small"])

        # ponytail: session dir derived from the validated file, never from client state
        artifact_dir = Path(file_path).parent / "artifacts"
        try:
            rows, artifacts = run_uploaded_file_benchmark(
                file_path=file_path,
                file_type=file_type,
                size_category=size_category,
                original_file_name=file_name,
                warm_ups=plan["warm_ups"],
                iterations=plan["iterations"],
                output_dir=str(artifact_dir),
            )
        except (OSError, ValueError) as error:
            return no_update, _error(f"Benchmark gagal: {error}. Unggah ulang file lalu coba lagi.")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        csv_name = f"{_safe_stem(file_name)}_{timestamp}_benchmark.csv"
        csv_path = save_benchmark_results(rows, filename=csv_name)

        benchmark_state = {
            "source": "upload",
            "source_label": "Upload file",
            "input_file_name": file_name,
            "file_type": file_type,
            "size_category": size_category,
            "rows": rows,
            "artifacts": artifacts,
            "csv_path": csv_path,
            "uploaded_file": upload_state,
            "benchmark_plan": plan,
            "benchmark_generated_at": datetime.now(timezone.utc).isoformat(),
        }

        status = html.Div(
            [
                html.Div("Benchmark selesai dan hasil sudah disimpan ke CSV."),
                html.Div(f"CSV: {_display_path(csv_path)}"),
            ],
            className="status status--ok",
        )
        return benchmark_state, status

    @app.callback(
        Output("file-type-dropdown", "value"),
        Input("benchmark-state", "data"),
        prevent_initial_call=True,
    )
    def sync_file_type(state):
        # A new upload replaces the data; the filter must say what the charts show.
        if not state or state.get("source") != "upload":
            raise PreventUpdate
        return _load_selected_file_type(state)

    @app.callback(
        Output("overview-metrics", "children"),
        Output("encryption-latency-graph", "figure"),
        Output("decryption-latency-graph", "figure"),
        Output("overhead-graph", "figure"),
        Output("benchmark-table", "data"),
        Output("artifact-panel", "children"),
        Input("benchmark-state", "data"),
        Input("file-type-dropdown", "value"),
    )
    def update_dashboard_views(state, selected_file_type):
        df = _state_to_dataframe(state, base_df)
        filtered_df = _select_active_dataframe(df, selected_file_type)

        metrics = _build_metrics_panel(filtered_df, state)
        enc_fig = _build_latency_figure(
            filtered_df,
            column="EncLatencyMeanMs",
            error_column="EncLatencyStdMs",
            title="Rata-rata Latensi Enkripsi",
            y_axis_title="Waktu (ms)",
        )
        dec_fig = _build_latency_figure(
            filtered_df,
            column="DecLatencyMeanMs",
            error_column="DecLatencyStdMs",
            title="Rata-rata Latensi Dekripsi",
            y_axis_title="Waktu (ms)",
        )
        overhead_fig = _build_overhead_figure(filtered_df)
        artifacts_panel = _build_artifact_panel(state if state and state.get("source") == "upload" else None)
        return metrics, enc_fig, dec_fig, overhead_fig, filtered_df.to_dict("records"), artifacts_panel

    def _register_download(algorithm: str, kind: str) -> None:
        slug = algorithm.lower().replace("-", "_")

        @app.callback(
            Output(f"download-{algorithm.lower()}-{kind}", "data"),
            Input(f"download-{slug}-{kind}", "n_clicks"),
            State("benchmark-state", "data"),
            prevent_initial_call=True,
        )
        def download(n_clicks, benchmark_state):
            if not n_clicks or not benchmark_state or benchmark_state.get("source") != "upload":
                raise PreventUpdate
            artifact = (benchmark_state.get("artifacts") or {}).get(algorithm)
            if not artifact:
                raise PreventUpdate
            path = artifact.get(f"{kind}_path")
            # dcc.Store is client-controlled: never serve a path outside the uploads dir
            if not is_within_uploads(path) or not Path(path).is_file():
                raise PreventUpdate
            return dcc.send_file(path, filename=artifact[f"{kind}_filename"])

    for _algorithm in ("AES-GCM", "Ascon-128"):
        for _kind in ("ciphertext", "metadata"):
            _register_download(_algorithm, _kind)

    register_demo_callbacks(app)
    register_analysis_callbacks(app)
    register_scenarios_callbacks(app)
    return app
