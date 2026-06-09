import base64
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, dash_table, ctx, no_update
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from src.benchmark import run_uploaded_file_benchmark
from src.report import save_benchmark_results

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
RESULTS_DIR = OUTPUT_DIR / "results"
UPLOADS_DIR = OUTPUT_DIR / "uploads"

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
    raw_bytes = base64.b64decode(encoded)
    return header, raw_bytes


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
                            "border": "1px solid #334155",
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
                    "backgroundColor": "#0f172a",
                    "border": "1px solid #334155",
                    "borderRadius": "12px",
                    "padding": "1rem",
                    "marginTop": "1rem",
                    "maxHeight": "280px",
                    "overflowY": "auto",
                },
            ),
        ]
    )


def _build_metric_card(label: str, value: str, accent: str) -> html.Div:
    return html.Div(
        [
            html.Div(label, style={"color": "#94a3b8", "fontSize": "0.85rem", "letterSpacing": "0.04em"}),
            html.Div(value, style={"color": accent, "fontSize": "1.5rem", "fontWeight": "700", "marginTop": "0.35rem"}),
        ],
        style={
            "backgroundColor": "#1e293b",
            "border": "1px solid #334155",
            "borderRadius": "16px",
            "padding": "1.25rem",
            "boxShadow": "0 8px 16px rgba(15, 23, 42, 0.25)",
        },
    )


def _build_metrics_panel(df: pd.DataFrame, state: dict | None) -> html.Div:
    source_label = "CSV benchmark"
    file_name = "-"
    if state:
        source_label = state.get("source_label", source_label)
        file_name = state.get("input_file_name", file_name)

    if df.empty:
        metrics = [
            _build_metric_card("Sumber aktif", source_label, "#60a5fa"),
            _build_metric_card("File aktif", file_name, "#f472b6"),
            _build_metric_card("Rata-rata enc", "0.000 ms", "#34d399"),
            _build_metric_card("Rata-rata dec", "0.000 ms", "#fbbf24"),
            _build_metric_card("Overhead rata-rata", "0.00%", "#c084fc"),
            _build_metric_card("Tamper pass", "0 / 0", "#e2e8f0"),
        ]
        return html.Div(
            metrics,
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
                "gap": "1rem",
                "marginBottom": "1.5rem",
            },
        )

    avg_enc = df["EncLatencyMeanMs"].mean()
    avg_dec = df["DecLatencyMeanMs"].mean()
    avg_overhead = df["OverheadPct"].mean()
    pass_count = int(df["TamperingIntegrityPassed"].fillna(False).astype(bool).sum())
    total_rows = len(df)
    pass_rate = (pass_count / total_rows) * 100 if total_rows else 0.0

    metrics = [
        _build_metric_card("Sumber aktif", source_label, "#60a5fa"),
        _build_metric_card("File aktif", file_name, "#f472b6"),
        _build_metric_card("Rata-rata enc", f"{avg_enc:.3f} ms", "#34d399"),
        _build_metric_card("Rata-rata dec", f"{avg_dec:.3f} ms", "#fbbf24"),
        _build_metric_card("Overhead rata-rata", f"{avg_overhead:.2f}%", "#c084fc"),
        _build_metric_card("Tamper pass", f"{pass_count} / {total_rows} ({pass_rate:.0f}%)", "#e2e8f0"),
    ]

    return html.Div(
        metrics,
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
            "gap": "1rem",
            "marginBottom": "1.5rem",
        },
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
        template="plotly_dark",
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        title=title,
        margin=dict(l=40, r=20, t=50, b=40),
        annotations=[
            dict(
                text=message,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(color="#cbd5e1", size=14),
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
        "AES-GCM": ("#60a5fa", "#3b82f6"),
        "Ascon-128": ("#f472b6", "#db2777"),
    }

    for algorithm, (base_color, accent_color) in palette.items():
        algo_df = df[df["Algorithm"] == algorithm]
        if algo_df.empty:
            continue
        fig.add_trace(
            go.Bar(
                x=algo_df["SizeCategory"].astype(str).str.capitalize(),
                y=algo_df[column],
                name=algorithm,
                marker_color=base_color,
                error_y=dict(type="data", array=algo_df[error_column], visible=True, color=accent_color),
            )
        )

    if not fig.data:
        return _empty_figure(title, "Tidak ada algoritma yang cocok dengan filter aktif.")

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        title=title,
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis_title="Kategori Ukuran",
        yaxis_title=y_axis_title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def _build_overhead_figure(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure("Overhead Ciphertext", "Belum ada data untuk ditampilkan.")

    fig = go.Figure()
    palette = {
        "AES-GCM": "#60a5fa",
        "Ascon-128": "#f472b6",
    }

    for algorithm, color in palette.items():
        algo_df = df[df["Algorithm"] == algorithm]
        if algo_df.empty:
            continue
        fig.add_trace(
            go.Bar(
                x=algo_df["SizeCategory"].astype(str).str.capitalize(),
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
        template="plotly_dark",
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        title="Overhead Ciphertext",
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis_title="Kategori Ukuran",
        yaxis_title="Overhead (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def _artifact_card(algorithm: str, artifact: dict | None, accent: str) -> html.Div:
    if not artifact:
        return html.Div(
            [
                html.H4(algorithm, style={"margin": "0 0 0.5rem 0", "color": accent}),
                html.Div("Jalankan benchmark upload untuk mengaktifkan unduhan."),
            ],
            style={
                "backgroundColor": "#1e293b",
                "border": "1px solid #334155",
                "borderRadius": "16px",
                "padding": "1.25rem",
            },
        )

    return html.Div(
        [
            html.H4(algorithm, style={"margin": "0 0 0.75rem 0", "color": accent}),
            html.Div(f"Ciphertext: {artifact.get('ciphertext_filename', '-')}", style={"marginBottom": "0.4rem"}),
            html.Div(f"Metadata: {artifact.get('metadata_filename', '-')}", style={"marginBottom": "1rem"}),
            html.Div(
                [
                    html.Button(
                        "Unduh Ciphertext",
                        id=f"download-{algorithm.lower().replace('-', '_')}-ciphertext",
                        n_clicks=0,
                        style={
                            "backgroundColor": accent,
                            "color": "#0f172a",
                            "border": "none",
                            "borderRadius": "999px",
                            "padding": "0.7rem 1rem",
                            "fontWeight": "700",
                            "marginRight": "0.75rem",
                            "cursor": "pointer",
                        },
                    ),
                    html.Button(
                        "Unduh Metadata",
                        id=f"download-{algorithm.lower().replace('-', '_')}-metadata",
                        n_clicks=0,
                        style={
                            "backgroundColor": "#0f172a",
                            "color": "#e2e8f0",
                            "border": f"1px solid {accent}",
                            "borderRadius": "999px",
                            "padding": "0.7rem 1rem",
                            "fontWeight": "700",
                            "cursor": "pointer",
                        },
                    ),
                ]
            ),
        ],
        style={
            "backgroundColor": "#1e293b",
            "border": "1px solid #334155",
            "borderRadius": "16px",
            "padding": "1.25rem",
        },
    )


def _build_artifact_panel(state: dict | None) -> html.Div:
    if not state or not state.get("artifacts"):
        return html.Div(
            [
                html.H3("Artefak Enkripsi", style={"margin": "0 0 0.5rem 0"}),
                html.Div("Upload file lalu jalankan benchmark untuk membuat ciphertext dan metadata yang bisa diunduh."),
            ],
            style={
                "backgroundColor": "#111827",
                "border": "1px solid #334155",
                "borderRadius": "18px",
                "padding": "1.5rem",
                "marginBottom": "1.5rem",
            },
        )

    artifacts = state["artifacts"]
    return html.Div(
        [
            html.H3("Artefak Enkripsi", style={"margin": "0 0 1rem 0"}),
            html.Div(
                [
                    _artifact_card("AES-GCM", artifacts.get("AES-GCM"), "#60a5fa"),
                    _artifact_card("Ascon-128", artifacts.get("Ascon-128"), "#f472b6"),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(280px, 1fr))",
                    "gap": "1rem",
                },
            ),
        ],
        style={
            "backgroundColor": "#111827",
            "border": "1px solid #334155",
            "borderRadius": "18px",
            "padding": "1.5rem",
            "marginBottom": "1.5rem",
        },
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
        external_stylesheets=[
            "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
        ],
    )
    app.config.suppress_callback_exceptions = True

    base_state = _build_initial_state(csv_path)
    base_df = _state_to_dataframe(base_state, pd.DataFrame(columns=EXPECTED_COLUMNS))

    app.layout = html.Div(
        style={
            "backgroundColor": "#0f172a",
            "color": "#f8fafc",
            "fontFamily": "'Inter', sans-serif",
            "minHeight": "100vh",
            "padding": "2rem",
        },
        children=[
            dcc.Store(id="upload-state"),
            dcc.Store(id="benchmark-state", data=base_state),
            dcc.Download(id="download-aes-gcm-ciphertext"),
            dcc.Download(id="download-aes-gcm-metadata"),
            dcc.Download(id="download-ascon-128-ciphertext"),
            dcc.Download(id="download-ascon-128-metadata"),
            html.Div(
                style={
                    "background": "linear-gradient(135deg, #1e293b, #0f172a)",
                    "border": "1px solid #334155",
                    "borderRadius": "18px",
                    "padding": "2rem",
                    "marginBottom": "1.5rem",
                    "boxShadow": "0 16px 30px rgba(15, 23, 42, 0.35)",
                },
                children=[
                    html.H1(
                        "AES-GCM vs Ascon-128 Benchmark Dashboard",
                        style={
                            "fontSize": "2.35rem",
                            "fontWeight": "800",
                            "margin": "0 0 0.65rem 0",
                            "background": "linear-gradient(to right, #60a5fa, #f472b6)",
                            "WebkitBackgroundClip": "text",
                            "WebkitTextFillColor": "transparent",
                        },
                    ),
                    html.P(
                        "Dashboard ini mendukung upload langsung file JSON atau gambar, menjalankan benchmark, lalu menyimpan ciphertext dan metadata yang bisa diunduh untuk demo.",
                        style={"color": "#94a3b8", "fontSize": "1.05rem", "maxWidth": "900px", "margin": "0"},
                    ),
                ],
            ),
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(280px, 1fr))",
                    "gap": "1rem",
                    "marginBottom": "1rem",
                },
                children=[
                    html.Div(
                        style={
                            "backgroundColor": "#1e293b",
                            "border": "1px solid #334155",
                            "borderRadius": "16px",
                            "padding": "1.25rem",
                        },
                        children=[
                            html.H3("Upload File", style={"marginTop": 0}),
                            dcc.Upload(
                                id="upload-data",
                                children=html.Div(
                                    [
                                        html.Div("Seret file JSON atau gambar ke sini"),
                                        html.Div("atau klik untuk memilih file", style={"color": "#94a3b8", "fontSize": "0.95rem"}),
                                    ]
                                ),
                                style={
                                    "width": "100%",
                                    "height": "130px",
                                    "lineHeight": "130px",
                                    "borderWidth": "2px",
                                    "borderStyle": "dashed",
                                    "borderColor": "#475569",
                                    "borderRadius": "14px",
                                    "textAlign": "center",
                                    "backgroundColor": "#0f172a",
                                    "color": "#e2e8f0",
                                },
                                multiple=False,
                                accept=".json,.png,.jpg,.jpeg,.webp,.gif,.bmp",
                            ),
                            html.Div(id="upload-status", style={"marginTop": "0.85rem", "color": "#cbd5e1"}),
                        ],
                    ),
                    html.Div(
                        style={
                            "backgroundColor": "#1e293b",
                            "border": "1px solid #334155",
                            "borderRadius": "16px",
                            "padding": "1.25rem",
                        },
                        children=[
                            html.H3("Aksi Benchmark", style={"marginTop": 0}),
                            html.Div(
                                "Setelah file diunggah, tekan tombol di bawah untuk menjalankan AES-GCM dan Ascon-128 pada file yang sama.",
                                style={"color": "#94a3b8", "marginBottom": "1rem"},
                            ),
                            html.Button(
                                "Jalankan Benchmark",
                                id="run-benchmark",
                                n_clicks=0,
                                style={
                                    "backgroundColor": "#22c55e",
                                    "color": "#0f172a",
                                    "border": "none",
                                    "borderRadius": "999px",
                                    "padding": "0.85rem 1.2rem",
                                    "fontWeight": "800",
                                    "cursor": "pointer",
                                },
                            ),
                            html.Div(id="benchmark-status", style={"marginTop": "0.85rem", "color": "#cbd5e1"}),
                        ],
                    ),
                    html.Div(
                        style={
                            "backgroundColor": "#1e293b",
                            "border": "1px solid #334155",
                            "borderRadius": "16px",
                            "padding": "1.25rem",
                        },
                        children=[
                            html.H3("Filter Dashboard", style={"marginTop": 0}),
                            html.Label("Tipe file", style={"display": "block", "marginBottom": "0.5rem", "color": "#cbd5e1"}),
                            dcc.Dropdown(
                                id="file-type-dropdown",
                                options=[
                                    {"label": "JSON", "value": "json"},
                                    {"label": "Gambar", "value": "image"},
                                ],
                                value=_load_selected_file_type(base_state),
                                clearable=False,
                                style={"color": "#0f172a"},
                            ),
                            html.Div(
                                "Grafik dan tabel akan mengikuti dataset aktif. Jika data upload hanya punya satu tipe file, dashboard akan menampilkan data tersebut otomatis.",
                                style={"marginTop": "0.85rem", "color": "#94a3b8", "fontSize": "0.92rem"},
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(id="upload-preview", style={"marginBottom": "1.5rem"}),
            html.Div(id="overview-metrics"),
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
                    "gap": "1rem",
                    "marginBottom": "1rem",
                },
                children=[
                    html.Div(
                        style={
                            "backgroundColor": "#1e293b",
                            "border": "1px solid #334155",
                            "borderRadius": "18px",
                            "padding": "1.25rem",
                        },
                        children=[
                            html.H3("Latensi Enkripsi", style={"marginTop": 0}),
                            dcc.Graph(id="encryption-latency-graph"),
                        ],
                    ),
                    html.Div(
                        style={
                            "backgroundColor": "#1e293b",
                            "border": "1px solid #334155",
                            "borderRadius": "18px",
                            "padding": "1.25rem",
                        },
                        children=[
                            html.H3("Latensi Dekripsi", style={"marginTop": 0}),
                            dcc.Graph(id="decryption-latency-graph"),
                        ],
                    ),
                ],
            ),
            html.Div(
                style={
                    "backgroundColor": "#1e293b",
                    "border": "1px solid #334155",
                    "borderRadius": "18px",
                    "padding": "1.25rem",
                    "marginBottom": "1.5rem",
                },
                children=[
                    html.H3("Overhead Ciphertext", style={"marginTop": 0}),
                    dcc.Graph(id="overhead-graph"),
                ],
            ),
            html.Div(id="artifact-panel"),
            html.Div(
                style={
                    "backgroundColor": "#1e293b",
                    "border": "1px solid #334155",
                    "borderRadius": "18px",
                    "padding": "1.25rem",
                },
                children=[
                    html.H3("Tabel Hasil Benchmark", style={"marginTop": 0}),
                    dash_table.DataTable(
                        id="benchmark-table",
                        columns=[
                            {"name": "Algorithm", "id": "Algorithm"},
                            {"name": "Input File", "id": "InputFileName"},
                            {"name": "File Type", "id": "FileType"},
                            {"name": "Size Category", "id": "SizeCategory"},
                            {"name": "Plaintext (Bytes)", "id": "PlaintextSizeBytes"},
                            {"name": "Ciphertext (Bytes)", "id": "CiphertextSizeBytes"},
                            {"name": "Mean Enc (ms)", "id": "EncLatencyMeanMs"},
                            {"name": "Mean Dec (ms)", "id": "DecLatencyMeanMs"},
                            {"name": "Overhead (Bytes)", "id": "OverheadBytes"},
                            {"name": "Overhead (%)", "id": "OverheadPct"},
                            {"name": "Tamper Test", "id": "TamperingIntegrityPassed"},
                        ],
                        data=base_df.to_dict("records"),
                        style_header={
                            "backgroundColor": "#0f172a",
                            "color": "#cbd5e1",
                            "fontWeight": "bold",
                            "border": "1px solid #334155",
                        },
                        style_cell={
                            "backgroundColor": "#1e293b",
                            "color": "#cbd5e1",
                            "border": "1px solid #334155",
                            "padding": "10px",
                            "fontFamily": "'Inter', sans-serif",
                            "whiteSpace": "normal",
                            "height": "auto",
                        },
                        style_data_conditional=[
                            {
                                "if": {"column_id": "TamperingIntegrityPassed", "filter_query": "{TamperingIntegrityPassed} = True"},
                                "color": "#34d399",
                                "fontWeight": "700",
                            },
                            {
                                "if": {"column_id": "Algorithm", "filter_query": "{Algorithm} = 'AES-GCM'"},
                                "color": "#60a5fa",
                            },
                            {
                                "if": {"column_id": "Algorithm", "filter_query": "{Algorithm} = 'Ascon-128'"},
                                "color": "#f472b6",
                            },
                        ],
                        page_size=10,
                        sort_action="native",
                        filter_action="native",
                        style_table={"overflowX": "auto"},
                    ),
                ],
            ),
        ],
    )

    @app.callback(
        Output("upload-state", "data"),
        Output("upload-preview", "children"),
        Output("upload-status", "children"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        State("upload-data", "last_modified"),
        prevent_initial_call=True,
    )
    def handle_upload(contents, filename, last_modified):
        if not contents or not filename:
            raise PreventUpdate

        header, raw_bytes = _decode_upload(contents)
        file_type = _detect_file_type(filename, header)
        if file_type is None:
            return no_update, no_update, html.Div(
                "Format file tidak didukung. Gunakan JSON, PNG, JPG, JPEG, WEBP, GIF, atau BMP.",
                style={"color": "#f87171"},
            )

        size_bytes = len(raw_bytes)
        size_category = _classify_size(file_type, size_bytes)

        session_dir = UPLOADS_DIR / uuid.uuid4().hex
        session_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _safe_stem(filename) + Path(filename).suffix.lower()
        file_path = session_dir / safe_name
        file_path.write_bytes(raw_bytes)

        preview = _make_preview(contents, filename, file_type, size_bytes)
        status = html.Div(
            [
                html.Div(f"File berhasil diunggah pada {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S')}"),
                html.Div(f"Kategori ukuran: {size_category}"),
            ],
            style={"color": "#34d399", "lineHeight": "1.6"},
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
        prevent_initial_call=True,
    )
    def run_benchmark(n_clicks, upload_state):
        if not n_clicks:
            raise PreventUpdate

        if not upload_state:
            return no_update, html.Div(
                "Unggah file JSON atau gambar terlebih dahulu sebelum menjalankan benchmark.",
                style={"color": "#fbbf24"},
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

        artifact_dir = Path(upload_state["session_dir"]) / "artifacts"
        rows, artifacts = run_uploaded_file_benchmark(
            file_path=file_path,
            file_type=file_type,
            size_category=size_category,
            original_file_name=file_name,
            warm_ups=plan["warm_ups"],
            iterations=plan["iterations"],
            output_dir=str(artifact_dir),
        )

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
                html.Div(f"CSV: {csv_path}"),
            ],
            style={"color": "#34d399", "lineHeight": "1.6"},
        )
        return benchmark_state, status

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

    def _send_file(path: str, filename: str):
        payload = Path(path).read_bytes()
        return dcc.send_bytes(lambda buffer: buffer.write(payload), filename)

    def _send_text(path: str, filename: str):
        text = Path(path).read_text(encoding="utf-8")
        return dcc.send_bytes(lambda buffer: buffer.write(text.encode("utf-8")), filename)

    @app.callback(
        Output("download-aes-gcm-ciphertext", "data"),
        Input("download-aes_gcm-ciphertext", "n_clicks"),
        State("benchmark-state", "data"),
        prevent_initial_call=True,
    )
    def download_aes_gcm_ciphertext(n_clicks, benchmark_state):
        if not n_clicks or not benchmark_state or benchmark_state.get("source") != "upload":
            raise PreventUpdate
        artifact = benchmark_state.get("artifacts", {}).get("AES-GCM")
        if not artifact:
            raise PreventUpdate
        return _send_file(artifact["ciphertext_path"], artifact["ciphertext_filename"])

    @app.callback(
        Output("download-aes-gcm-metadata", "data"),
        Input("download-aes_gcm-metadata", "n_clicks"),
        State("benchmark-state", "data"),
        prevent_initial_call=True,
    )
    def download_aes_gcm_metadata(n_clicks, benchmark_state):
        if not n_clicks or not benchmark_state or benchmark_state.get("source") != "upload":
            raise PreventUpdate
        artifact = benchmark_state.get("artifacts", {}).get("AES-GCM")
        if not artifact:
            raise PreventUpdate
        return _send_text(artifact["metadata_path"], artifact["metadata_filename"])

    @app.callback(
        Output("download-ascon-128-ciphertext", "data"),
        Input("download-ascon_128-ciphertext", "n_clicks"),
        State("benchmark-state", "data"),
        prevent_initial_call=True,
    )
    def download_ascon_128_ciphertext(n_clicks, benchmark_state):
        if not n_clicks or not benchmark_state or benchmark_state.get("source") != "upload":
            raise PreventUpdate
        artifact = benchmark_state.get("artifacts", {}).get("Ascon-128")
        if not artifact:
            raise PreventUpdate
        return _send_file(artifact["ciphertext_path"], artifact["ciphertext_filename"])

    @app.callback(
        Output("download-ascon-128-metadata", "data"),
        Input("download-ascon_128-metadata", "n_clicks"),
        State("benchmark-state", "data"),
        prevent_initial_call=True,
    )
    def download_ascon_128_metadata(n_clicks, benchmark_state):
        if not n_clicks or not benchmark_state or benchmark_state.get("source") != "upload":
            raise PreventUpdate
        artifact = benchmark_state.get("artifacts", {}).get("Ascon-128")
        if not artifact:
            raise PreventUpdate
        return _send_text(artifact["metadata_path"], artifact["metadata_filename"])

    return app
