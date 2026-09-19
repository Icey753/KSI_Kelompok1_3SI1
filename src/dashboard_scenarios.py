from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots

from src.scenarios import run_and_save_scenarios

RESULTS_DIR = Path(__file__).resolve().parent.parent / "output" / "results"
QUICK = {"n_messages": 300, "total_bytes": 2097152, "iterations": 5, "acceleration_sizes": (1024, 65536, 1048576)}

COLORS = {"AES-GCM": "#60a5fa", "AES-GCM-noNI": "#fbbf24", "Ascon-128": "#f472b6"}
CARD_STYLE = {"backgroundColor": "#1e293b", "border": "1px solid #334155", "borderRadius": "18px", "padding": "1.25rem", "marginBottom": "1rem"}
BUTTON_STYLE = {"backgroundColor": "#3b82f6", "color": "#f8fafc", "border": "none", "borderRadius": "10px",
                "padding": "0.6rem 1rem", "cursor": "pointer", "fontWeight": "600"}


def load_scenario(name: str, results_dir=RESULTS_DIR) -> pd.DataFrame | None:
    path = Path(results_dir) / f"{name}.csv"
    return pd.read_csv(path) if path.exists() else None


def _style(fig: go.Figure, **layout) -> go.Figure:
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", **layout)
    return fig


def _placeholder() -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="Belum ada data. Klik 'Jalankan skenario (cepat)' atau jalankan python -m src.scenarios.",
                       showarrow=False, font={"color": "#94a3b8", "size": 14})
    return _style(fig, height=350)


def _size_label(size: int, total: int | None = None) -> str:
    if total is not None and size == total:
        return "Utuh"
    if size >= 1 << 20:
        return f"{size >> 20} MB"
    if size >= 1 << 10:
        return f"{size >> 10} KB"
    return f"{size} B"


def build_small_message_figure(df: pd.DataFrame | None) -> go.Figure:
    if df is None or df.empty:
        return _placeholder()
    fig = go.Figure()
    for algorithm, group in df.groupby("Algorithm", sort=False):
        group = group.sort_values("MessageSizeBytes")
        fig.add_trace(go.Bar(x=[_size_label(s) for s in group["MessageSizeBytes"]], y=group["MessagesPerSec"],
                             name=algorithm, marker_color=COLORS.get(algorithm)))
    fig.update_yaxes(title_text="Pesan per detik (lebih tinggi lebih baik)")
    fig.update_xaxes(title_text="Ukuran satu pesan")
    return _style(fig, barmode="group", height=420)


def build_chunked_figure(df: pd.DataFrame | None) -> go.Figure:
    if df is None or df.empty:
        return _placeholder()
    total = int(df["TotalBytes"].iloc[0])
    first = df["Algorithm"].iloc[0]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Overhead (%) per ukuran chunk", "Median latensi enkripsi (ms)"))
    overhead = df[df["Algorithm"] == first].sort_values("ChunkSizeBytes")
    fig.add_trace(go.Scatter(x=[_size_label(c, total) for c in overhead["ChunkSizeBytes"]], y=overhead["OverheadPct"],
                             mode="lines+markers", name="Overhead (sama untuk semua varian)", line={"color": "#a78bfa"}), row=1, col=1)
    for algorithm, group in df.groupby("Algorithm", sort=False):
        group = group.sort_values("ChunkSizeBytes")
        fig.add_trace(go.Scatter(x=[_size_label(c, total) for c in group["ChunkSizeBytes"]], y=group["EncMedianMs"],
                                 mode="lines+markers", name=algorithm, line={"color": COLORS.get(algorithm)}), row=1, col=2)
    fig.update_yaxes(type="log", row=1, col=1)
    fig.update_xaxes(title_text="Ukuran chunk", row=1, col=1)
    fig.update_xaxes(title_text="Ukuran chunk", row=1, col=2)
    return _style(fig, height=420)


def build_acceleration_figure(df: pd.DataFrame | None) -> go.Figure:
    if df is None or df.empty:
        return _placeholder()
    fig = go.Figure()
    for algorithm, group in df.groupby("Algorithm", sort=False):
        group = group.sort_values("SizeBytes")
        fig.add_trace(go.Bar(x=[_size_label(s) for s in group["SizeBytes"]], y=group["EncMedianMs"],
                             name=algorithm, marker_color=COLORS.get(algorithm)))
    fig.update_yaxes(type="log", title_text="Median latensi enkripsi (ms, skala log)")
    fig.update_xaxes(title_text="Ukuran data")
    return _style(fig, barmode="group", height=420)


def _card(title: str, description: str, graph_id: str, figure: go.Figure) -> html.Div:
    return html.Div(
        [html.H3(title, style={"marginTop": 0}), html.P(description, style={"color": "#94a3b8", "marginTop": 0}),
         dcc.Graph(id=graph_id, figure=figure)],
        style=CARD_STYLE,
    )


def build_scenarios_section() -> html.Div:
    return html.Div(
        [
            html.H2("Skenario Realistis", style={"marginBottom": "0.25rem"}),
            html.Div(
                [
                    html.Button("Jalankan skenario (cepat)", id="scenarios-run", n_clicks=0, style=BUTTON_STYLE),
                    html.Span("  Versi cepat memakai data lebih kecil; gunakan python -m src.scenarios untuk hasil penuh.",
                              style={"color": "#94a3b8"}),
                    html.Div(id="scenarios-status", style={"marginTop": "0.75rem", "color": "#34d399"}),
                ],
                style=CARD_STYLE,
            ),
            _card("Ribuan pesan JSON kecil (gaya API)",
                  "Nonce baru per pesan. Ukuran pesan kecil membuat biaya inisialisasi per panggilan dominan.",
                  "scenarios-small-graph", build_small_message_figure(load_scenario("small_messages"))),
            _card("File besar dienkripsi per chunk",
                  "Setiap chunk membawa tag 16 byte; chunk lebih kecil berarti overhead lebih besar. AD memuat indeks chunk sehingga penukaran urutan dan pemotongan terdeteksi.",
                  "scenarios-chunked-graph", build_chunked_figure(load_scenario("chunked"))),
            _card("Dengan dan tanpa AES-NI",
                  "AES-GCM-noNI mematikan akselerasi hardware untuk meniru perangkat tanpa AES-NI. Ini menjelaskan mengapa hasil berbeda dari literatur IoT.",
                  "scenarios-accel-graph", build_acceleration_figure(load_scenario("acceleration"))),
        ]
    )


def register_scenarios_callbacks(app) -> None:
    @app.callback(
        Output("scenarios-small-graph", "figure"),
        Output("scenarios-chunked-graph", "figure"),
        Output("scenarios-accel-graph", "figure"),
        Output("scenarios-status", "children"),
        Input("scenarios-run", "n_clicks"),
        prevent_initial_call=True,
    )
    def run_scenarios(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        frames = run_and_save_scenarios(**QUICK, results_dir=str(RESULTS_DIR / "quick"))
        return (
            build_small_message_figure(frames["small_messages"]),
            build_chunked_figure(frames["chunked"]),
            build_acceleration_figure(frames["acceleration"]),
            "Skenario cepat selesai. Hasil disimpan ke output/results/quick/ (hasil lengkap di output/results tidak ditimpa).",
        )
