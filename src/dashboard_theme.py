"""Single source for dashboard colors.

The same values feed three places: CSS variables (injected into <head> and used by
assets/dashboard.css and inline styles), Plotly figures, and the DataTable, which
cannot read CSS variables. Change a color here, nowhere else.
"""

from dash import html

TOKENS = {
    "bg": "#0f172a",
    "surface": "#1e293b",
    "border": "#334155",
    "border_strong": "#475569",
    "text": "#f8fafc",
    "text_soft": "#e2e8f0",
    "text_2": "#cbd5e1",
    "text_muted": "#94a3b8",
    "primary": "#3b82f6",
    "go": "#22c55e",
    "aes": "#60a5fa",
    "ascon": "#f472b6",
    "aes_strong": "#3b82f6",
    "ascon_strong": "#db2777",
    "ok": "#34d399",
    "warn": "#fbbf24",
    "danger": "#f87171",
    "violet": "#c084fc",
    "guide": "#64748b",
}

# Inter is self-hosted (assets/fonts). "Inter Fallback" is Arial resized to Inter's metrics.
FONT_UI = '"Inter", "Inter Fallback", system-ui, -apple-system, "Segoe UI", sans-serif'

TRANSPARENT = "rgba(0,0,0,0)"
# Legend below the plot: a right-hand legend eats half the width on a phone.
CHART_BASE = {
    "template": "plotly_dark",
    "paper_bgcolor": TRANSPARENT,
    "plot_bgcolor": TRANSPARENT,
    "legend": {"orientation": "h", "yanchor": "top", "y": -0.32, "xanchor": "left", "x": 0},
    "margin": {"l": 40, "r": 20, "t": 50, "b": 120},
}


def chart_layout(**overrides) -> dict:
    return {**CHART_BASE, **overrides}


# One color per algorithm, shared by every chart and table.
ALGORITHM_COLORS = {"AES-GCM": TOKENS["aes"], "AES-GCM-noNI": TOKENS["warn"], "Ascon-128": TOKENS["ascon"]}


def root_css() -> str:
    body = ";".join(f"--{name.replace('_', '-')}:{value}" for name, value in TOKENS.items())
    return f":root{{{body};--font-ui:{FONT_UI}}}"


def section(section_id: str, title: str, children: list, lead: str | None = None) -> html.Section:
    """A page section: real h2, optional one-line lead, body stacked with one gap."""
    head = [html.H2(title, className="section__title")]
    if lead:
        head.append(html.P(lead, className="muted section__lead"))
    return html.Section(
        [html.Header(head, className="section__head"), html.Div(children, className="stack")],
        id=section_id,
        className="section",
    )
