import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html, no_update
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots

from src.dashboard_theme import TOKENS, chart_layout, section
from src.sweep import find_crossover, run_and_save_sweep

RESULTS_DIR = Path(__file__).resolve().parent.parent / "output" / "results"
SUMMARY_PATH = RESULTS_DIR / "size_sweep_summary.csv"
ENV_PATH = RESULTS_DIR / "environment.json"


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
                           showarrow=False, font={"color": TOKENS["text_muted"], "size": 14})
        fig.update_layout(**chart_layout())
        return fig

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=("Median latensi enkripsi (ms)", "Rasio Ascon / AES (<1 = Ascon lebih cepat)"))
    for kind, dash, label_at in zip(sorted(summary["Kind"].unique()), ("solid", "dash"), ("top center", "bottom center")):
        sub = summary[summary["Kind"] == kind].sort_values("SizeBytes")
        fig.add_trace(go.Scatter(x=sub["SizeBytes"], y=sub["AesEncMedianMs"], mode="lines+markers",
                                 name=f"AES-GCM ({kind})", line={"color": TOKENS["aes"], "dash": dash}), row=1, col=1)
        fig.add_trace(go.Scatter(x=sub["SizeBytes"], y=sub["AsconEncMedianMs"], mode="lines+markers",
                                 name=f"Ascon-128 ({kind})", line={"color": TOKENS["ascon"], "dash": dash}), row=1, col=1)
        fig.add_trace(go.Scatter(x=sub["SizeBytes"], y=sub["RatioAsconOverAes"], mode="lines+markers",
                                 name=f"Rasio ({kind})", line={"color": TOKENS["violet"], "dash": dash}), row=2, col=1)
        crossover = find_crossover(summary, kind)
        if crossover is not None:
            fig.add_trace(go.Scatter(x=[crossover], y=[1.0], mode="markers+text", text=[f"titik potong ~{crossover / 1024:.0f} KB"],
                                     textposition=label_at, marker={"size": 12, "color": TOKENS["warn"], "symbol": "diamond"},
                                     name=f"Titik potong ({kind})"), row=2, col=1)
    fig.add_hline(y=1.0, line_dash="dot", line_color=TOKENS["guide"], row=2, col=1)
    fig.update_xaxes(type="log")
    fig.update_xaxes(title_text="Ukuran data (byte, skala log)", row=2, col=1)
    fig.update_yaxes(type="log")
    fig.update_annotations(font_size=13)  # subplot titles: 16px overflows a phone
    fig.update_layout(**chart_layout(height=780, margin=dict(l=40, r=20, t=50, b=200)))
    return fig


def build_env_panel(info: dict | None) -> html.Div:
    if not info:
        return html.Div("Info lingkungan belum tersedia. Jalankan python main.py untuk membuat environment.json.",
                        className="status status--warn")
    speedup = info.get("aesni_speedup")
    if speedup and speedup > 1.5:
        note = f"AES-NI mempercepat AES-GCM sekitar {speedup}x pada mesin ini; perangkat tanpa AES-NI tidak mendapat percepatan ini."
    else:
        note = f"Efek AES-NI terukur {speedup}x: hampir tidak ada akselerasi hardware pada mesin ini."
    rows = [("Python", info.get("python")), ("Sistem", info.get("platform")), ("Prosesor", info.get("processor")),
            ("Jumlah CPU", info.get("cpu_count")), ("pycryptodome", info.get("pycryptodome")),
            ("Backend Ascon", info.get("ascon_backend")), ("Varian Ascon", info.get("ascon_variant"))]
    return html.Div(
        [html.Div([html.Span(f"{label}: ", className="muted"), html.Span(str(value))], style={"marginBottom": "0.2rem"})
         for label, value in rows]
        + [html.Div(note, className="status status--warn", style={"marginTop": "0.75rem"})]
    )


def build_analysis_section() -> html.Section:
    return section(
        "analisis",
        "Analisis Ukuran Data dan Lingkungan",
        children=[
            html.Div(
                className="grid grid--split",
                children=[
                    html.Div(
                        [
                            dcc.Download(id="analysis-download"),
                            html.H3("Titik potong latensi Ascon vs AES-GCM", className="card-title"),
                            html.P("Sweep 1 KB sampai 10 MB (JSON dan biner). Dari dashboard dijalankan dengan 20 iterasi; pipeline utama memakai 50.",
                                   className="muted", style={"marginTop": 0}),
                            html.Div(
                                [
                                    html.Button("Jalankan sweep", id="analysis-run-sweep", n_clicks=0, className="btn"),
                                    html.Button("Unduh CSV sweep", id="analysis-download-csv", n_clicks=0, className="btn"),
                                ],
                                className="btn-row",
                            ),
                            html.Div(id="analysis-sweep-status", role="status", className="status status--ok", style={"marginTop": "0.75rem"}),
                            dcc.Loading(dcc.Graph(id="analysis-sweep-graph", figure=build_sweep_figure(load_sweep_summary()))),
                        ],
                        className="card",
                    ),
                    html.Div(
                        [html.H3("Info lingkungan pengujian", className="card-title"),
                         html.Div(id="analysis-env-panel", children=build_env_panel(load_env_info()))],
                        className="card",
                    ),
                ],
            ),
        ],
    )


def register_analysis_callbacks(app) -> None:
    @app.callback(
        Output("analysis-sweep-graph", "figure"),
        Output("analysis-sweep-status", "children"),
        Input("analysis-run-sweep", "n_clicks"),
        running=[(Output("analysis-run-sweep", "disabled"), True, False)],
        prevent_initial_call=True,
    )
    def run_sweep(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        summary = run_and_save_sweep(iterations=20)
        return build_sweep_figure(summary), "Sweep selesai (20 iterasi), disimpan ke output/results/size_sweep_summary.csv. Grafik sudah diperbarui; restart server agar tetap tampil setelah halaman dimuat ulang."

    @app.callback(
        Output("analysis-download", "data"),
        Output("analysis-sweep-status", "children", allow_duplicate=True),
        Input("analysis-download-csv", "n_clicks"),
        prevent_initial_call=True,
    )
    def download_csv(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        if not SUMMARY_PATH.exists():
            return no_update, "Belum ada CSV sweep. Klik 'Jalankan sweep' dulu, lalu unduh."
        return dcc.send_file(str(SUMMARY_PATH)), ""
