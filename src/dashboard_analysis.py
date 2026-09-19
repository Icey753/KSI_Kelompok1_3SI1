import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots

from src.sweep import find_crossover, run_and_save_sweep

RESULTS_DIR = Path(__file__).resolve().parent.parent / "output" / "results"
SUMMARY_PATH = RESULTS_DIR / "size_sweep_summary.csv"
ENV_PATH = RESULTS_DIR / "environment.json"

AES_COLOR = "#60a5fa"
ASCON_COLOR = "#f472b6"
CARD_STYLE = {"backgroundColor": "#1e293b", "border": "1px solid #334155", "borderRadius": "18px", "padding": "1.25rem"}
BUTTON_STYLE = {"backgroundColor": "#3b82f6", "color": "#f8fafc", "border": "none", "borderRadius": "10px",
                "padding": "0.6rem 1rem", "cursor": "pointer", "fontWeight": "600", "marginRight": "0.75rem"}


def load_sweep_summary(path=SUMMARY_PATH) -> pd.DataFrame | None:
    path = Path(path)
    return pd.read_csv(path) if path.exists() else None


def load_env_info(path=ENV_PATH) -> dict | None:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def build_sweep_figure(summary: pd.DataFrame | None) -> go.Figure:
    if summary is None or summary.empty:
        fig = go.Figure()
        fig.add_annotation(text="Belum ada data sweep. Klik 'Jalankan sweep' atau jalankan python -m src.sweep.",
                           showarrow=False, font={"color": "#94a3b8", "size": 14})
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=("Median latensi enkripsi (ms)", "Rasio Ascon / AES (<1 = Ascon lebih cepat)"))
    for kind, dash in zip(sorted(summary["Kind"].unique()), ("solid", "dash")):
        sub = summary[summary["Kind"] == kind].sort_values("SizeBytes")
        fig.add_trace(go.Scatter(x=sub["SizeBytes"], y=sub["AesEncMedianMs"], mode="lines+markers",
                                 name=f"AES-GCM ({kind})", line={"color": AES_COLOR, "dash": dash}), row=1, col=1)
        fig.add_trace(go.Scatter(x=sub["SizeBytes"], y=sub["AsconEncMedianMs"], mode="lines+markers",
                                 name=f"Ascon-128 ({kind})", line={"color": ASCON_COLOR, "dash": dash}), row=1, col=1)
        fig.add_trace(go.Scatter(x=sub["SizeBytes"], y=sub["RatioAsconOverAes"], mode="lines+markers",
                                 name=f"Rasio ({kind})", line={"color": "#a78bfa", "dash": dash}), row=2, col=1)
        crossover = find_crossover(summary, kind)
        if crossover is not None:
            fig.add_trace(go.Scatter(x=[crossover], y=[1.0], mode="markers+text", text=[f"titik potong ~{crossover / 1024:.0f} KB"],
                                     textposition="top center", marker={"size": 12, "color": "#fbbf24", "symbol": "diamond"},
                                     name=f"Titik potong ({kind})"), row=2, col=1)
    fig.add_hline(y=1.0, line_dash="dot", line_color="#64748b", row=2, col=1)
    fig.update_xaxes(type="log")
    fig.update_xaxes(title_text="Ukuran data (byte, skala log)", row=2, col=1)
    fig.update_yaxes(type="log")
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=650)
    return fig


def build_env_panel(info: dict | None) -> html.Div:
    if not info:
        return html.Div("Info lingkungan belum tersedia. Jalankan python main.py untuk membuat environment.json.",
                        style={"color": "#fbbf24"})
    speedup = info.get("aesni_speedup")
    if speedup and speedup > 1.5:
        note = f"AES-NI mempercepat AES-GCM sekitar {speedup}x pada mesin ini; perangkat tanpa AES-NI tidak mendapat percepatan ini."
    else:
        note = f"Efek AES-NI terukur {speedup}x: hampir tidak ada akselerasi hardware pada mesin ini."
    rows = [("Python", info.get("python")), ("Sistem", info.get("platform")), ("Prosesor", info.get("processor")),
            ("Jumlah CPU", info.get("cpu_count")), ("pycryptodome", info.get("pycryptodome")),
            ("Backend Ascon", info.get("ascon_backend")), ("Varian Ascon", info.get("ascon_variant"))]
    return html.Div(
        [html.Div([html.Span(f"{label}: ", style={"color": "#94a3b8"}), html.Span(str(value))], style={"marginBottom": "0.2rem"})
         for label, value in rows]
        + [html.Div(note, style={"marginTop": "0.75rem", "color": "#fbbf24"})]
    )


def build_analysis_section() -> html.Div:
    return html.Div(
        [
            html.H2("Analisis Ukuran Data dan Lingkungan", style={"marginBottom": "0.25rem"}),
            dcc.Download(id="analysis-download"),
            html.Div(
                [
                    html.H3("Titik potong latensi Ascon vs AES-GCM", style={"marginTop": 0}),
                    html.P("Sweep 1 KB sampai 10 MB (JSON dan biner). Dari dashboard dijalankan dengan 20 iterasi; pipeline utama memakai 50.",
                           style={"color": "#94a3b8", "marginTop": 0}),
                    html.Button("Jalankan sweep", id="analysis-run-sweep", n_clicks=0, style=BUTTON_STYLE),
                    html.Button("Unduh CSV sweep", id="analysis-download-csv", n_clicks=0, style=BUTTON_STYLE),
                    html.Div(id="analysis-sweep-status", style={"marginTop": "0.75rem", "color": "#34d399"}),
                    dcc.Loading(dcc.Graph(id="analysis-sweep-graph", figure=build_sweep_figure(load_sweep_summary()))),
                ],
                style={**CARD_STYLE, "marginBottom": "1rem"},
            ),
            html.Div(
                [html.H3("Info lingkungan pengujian", style={"marginTop": 0}),
                 html.Div(id="analysis-env-panel", children=build_env_panel(load_env_info()))],
                style={**CARD_STYLE, "marginBottom": "1.5rem"},
            ),
        ]
    )


def register_analysis_callbacks(app) -> None:
    @app.callback(
        Output("analysis-sweep-graph", "figure"),
        Output("analysis-sweep-status", "children"),
        Input("analysis-run-sweep", "n_clicks"),
        prevent_initial_call=True,
    )
    def run_sweep(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        summary = run_and_save_sweep(iterations=20)
        return build_sweep_figure(summary), "Sweep selesai (20 iterasi) dan disimpan ke output/results/size_sweep_summary.csv."

    @app.callback(
        Output("analysis-download", "data"),
        Input("analysis-download-csv", "n_clicks"),
        prevent_initial_call=True,
    )
    def download_csv(n_clicks):
        if not n_clicks or not SUMMARY_PATH.exists():
            raise PreventUpdate
        return dcc.send_file(str(SUMMARY_PATH))
