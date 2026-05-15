from __future__ import annotations

import json
from html import escape
from statistics import mean

from app.services.allocator_service import build_service


SERVICE = build_service()


def _service_lookup() -> dict[str, dict]:
    return {service["serviceId"]: service for service in SERVICE.services}


def _verdict_class(verdict: str) -> str:
    return {
        "healthy": "healthy",
        "watch": "watch",
        "breach": "breach",
    }[verdict]


def _score_bars(service: dict) -> str:
    metrics = [
        ("Burn rate", min(100.0, (service["consumedMinutes"] / service["monthlyBudgetMinutes"]) * 100)),
        ("Projected burn", min(130.0, (service["projectedConsumedMinutes"] / service["monthlyBudgetMinutes"]) * 100)),
        ("Dependency pressure", float(service["dependencyPressure"])),
        ("Change failure rate", float(service["changeFailureRatePct"]) * 3.5),
    ]
    rows = []
    for label, raw_value in metrics:
        value = max(0.0, min(100.0, raw_value))
        tone = "good" if value < 55 else "watch" if value < 80 else "hot"
        rows.append(
            f"""
            <div class="meter-row">
              <div class="meter-head">
                <span>{escape(label)}</span>
                <span>{round(raw_value, 1)}%</span>
              </div>
              <div class="meter-track"><div class="meter-fill {tone}" style="width: {value:.1f}%"></div></div>
            </div>
            """
        )
    return "".join(rows)


def _shell(title: str, subtitle: str, current: str, body: str) -> str:
    summary = SERVICE.summary()
    nav_items = [
        ("/", "Overview", "overview"),
        ("/allocations", "Allocation Queue", "allocations"),
        ("/service-matrix", "Service Matrix", "matrix"),
        ("/methodology", "Methodology", "methodology"),
    ]
    sidebar = "".join(
        f"""
        <a class="side-link {'active' if key == current else ''}" href="{href}">
          <span>{escape(label)}</span>
        </a>
        """
        for href, label, key in nav_items
    )
    tabs = "".join(
        f"""<a class="tab-pill {'active' if key == current else ''}" href="{href}">{escape(label)}</a>"""
        for href, label, key in nav_items
    )
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(title)}</title>
    <style>
      :root {{
        color-scheme: dark;
        --bg: #04070d;
        --panel: rgba(9, 16, 28, 0.9);
        --panel-soft: rgba(255, 255, 255, 0.035);
        --line: rgba(255, 255, 255, 0.07);
        --text: #f5f7fd;
        --muted: #96a9c6;
        --cyan: #72c3ff;
        --blue: #4f7fff;
        --green: #49d79e;
        --amber: #f6c46a;
        --red: #ff7987;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Inter, "Segoe UI", system-ui, sans-serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(114, 195, 255, 0.14), transparent 24%),
          radial-gradient(circle at top right, rgba(246, 196, 106, 0.1), transparent 18%),
          linear-gradient(180deg, #02050a 0%, #050912 100%);
      }}
      a {{ color: inherit; }}
      .shell {{
        min-height: 100vh;
        display: grid;
        grid-template-columns: 248px minmax(0, 1fr);
      }}
      .sidebar {{
        background: rgba(0, 0, 0, 0.3);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(16px);
        padding: 24px 18px;
        display: flex;
        flex-direction: column;
      }}
      .brand {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 10px 18px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      }}
      .brand-mark {{
        width: 40px;
        height: 40px;
        border-radius: 12px;
        display: grid;
        place-items: center;
        background: linear-gradient(135deg, #0c97c2, #4f7fff);
        color: white;
        font-weight: 900;
        box-shadow: 0 0 18px rgba(79, 127, 255, 0.28);
      }}
      .brand strong {{
        display: block;
        font-size: 14px;
      }}
      .brand span {{
        display: block;
        margin-top: 4px;
        color: var(--cyan);
        font-size: 10px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
      }}
      nav {{
        margin-top: 18px;
      }}
      .side-link {{
        display: block;
        padding: 13px 14px;
        border-radius: 14px;
        color: #8195b4;
        text-decoration: none;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        transition: all 150ms ease;
      }}
      .side-link.active {{
        color: var(--cyan);
        background: rgba(114, 195, 255, 0.08);
        border: 1px solid rgba(114, 195, 255, 0.16);
      }}
      .side-link:hover {{
        color: var(--text);
        background: rgba(255, 255, 255, 0.04);
      }}
      .meta {{
        margin-top: auto;
        padding: 16px 12px 8px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
      }}
      .meta dt {{
        color: #687c98;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        margin-bottom: 4px;
      }}
      .meta dd {{
        margin: 0 0 14px;
        font-size: 12px;
        font-weight: 700;
      }}
      .topbar {{
        height: 72px;
        position: sticky;
        top: 0;
        z-index: 2;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 34px;
        background: rgba(0, 0, 0, 0.34);
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(16px);
      }}
      .status-chip {{
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 9px 14px;
        border-radius: 999px;
        border: 1px solid rgba(114, 195, 255, 0.14);
        background: rgba(114, 195, 255, 0.05);
        color: #b3ddff;
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.18em;
      }}
      .status-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--cyan);
        box-shadow: 0 0 12px rgba(114, 195, 255, 0.84);
      }}
      .topbar-right {{
        display: flex;
        align-items: center;
        gap: 22px;
      }}
      .meta-block {{
        display: flex;
        flex-direction: column;
        align-items: flex-end;
      }}
      .meta-block span {{
        color: #6d809b;
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.15em;
      }}
      .meta-block strong {{
        margin-top: 4px;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
      }}
      .action-pill {{
        display: inline-flex;
        align-items: center;
        padding: 12px 16px;
        border-radius: 999px;
        color: white;
        text-decoration: none;
        background: linear-gradient(135deg, #0f8fbf, #4f7fff);
        box-shadow: 0 0 20px rgba(79, 127, 255, 0.24);
        font-size: 10px;
        font-weight: 900;
        letter-spacing: 0.18em;
        text-transform: uppercase;
      }}
      .wrap {{
        max-width: 1280px;
        margin: 0 auto;
        padding: 34px;
      }}
      .hero {{
        border: 1px solid var(--line);
        border-radius: 28px;
        padding: 28px;
        background:
          linear-gradient(180deg, rgba(9, 16, 28, 0.96), rgba(6, 11, 20, 0.94)),
          radial-gradient(circle at top right, rgba(246, 196, 106, 0.12), transparent 25%);
        box-shadow: 0 26px 60px rgba(0, 0, 0, 0.34);
      }}
      .hero-eyebrow {{
        margin-bottom: 18px;
        color: var(--cyan);
        font-size: 11px;
        letter-spacing: 0.28em;
        text-transform: uppercase;
        font-weight: 800;
      }}
      h1 {{
        margin: 0;
        font-size: clamp(38px, 5vw, 70px);
        line-height: 0.92;
        font-family: Georgia, "Times New Roman", serif;
        letter-spacing: -0.04em;
      }}
      .hero-subtitle {{
        margin-top: 14px;
        max-width: 860px;
        color: var(--muted);
        font-size: 19px;
        line-height: 1.55;
      }}
      .hero-strip {{
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        margin-top: 24px;
      }}
      .hero-kpi {{
        min-width: 180px;
        padding: 14px 16px;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: rgba(255, 255, 255, 0.03);
      }}
      .hero-kpi .k {{
        color: #6f83a0;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-weight: 800;
      }}
      .hero-kpi .v {{
        margin-top: 6px;
        font-size: 28px;
        font-weight: 800;
      }}
      .hero-callout {{
        margin-top: 18px;
        padding: 18px 20px;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: rgba(2, 8, 17, 0.62);
      }}
      .hero-callout strong {{
        display: block;
        color: var(--amber);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        margin-bottom: 8px;
      }}
      .hero-callout p {{
        margin: 0;
        color: #dce7fb;
        font-size: 17px;
        line-height: 1.5;
      }}
      .tab-row {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 20px;
      }}
      .tab-pill {{
        display: inline-flex;
        align-items: center;
        text-decoration: none;
        padding: 10px 14px;
        border-radius: 999px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.03);
        color: #afc0d8;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.12em;
      }}
      .tab-pill.active {{
        color: var(--amber);
        border-color: rgba(246, 196, 106, 0.18);
        background: rgba(246, 196, 106, 0.08);
      }}
      .page-section {{
        margin-top: 24px;
        border-radius: 26px;
        border: 1px solid var(--line);
        background: var(--panel);
        overflow: hidden;
        box-shadow: 0 24px 54px rgba(0, 0, 0, 0.24);
      }}
      .section-head {{
        padding: 20px 24px 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      }}
      .section-head strong {{
        display: block;
        color: var(--cyan);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        margin-bottom: 10px;
      }}
      .section-head h2 {{
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 24px;
        letter-spacing: -0.03em;
      }}
      .section-head p {{
        margin: 10px 0 0;
        color: var(--muted);
        font-size: 15px;
        line-height: 1.55;
      }}
      .section-body {{
        padding: 24px;
      }}
      .stats-grid {{
        display: grid;
        gap: 18px;
        grid-template-columns: repeat(4, minmax(0, 1fr));
      }}
      .stat-card {{
        border-radius: 20px;
        padding: 18px 18px 20px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(0, 0, 0, 0.08));
      }}
      .stat-card .label {{
        color: #71839d;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-weight: 800;
      }}
      .stat-card .value {{
        margin-top: 10px;
        font-size: 36px;
        font-weight: 900;
      }}
      .stat-card .sub {{
        margin-top: 10px;
        color: var(--muted);
        font-size: 14px;
        line-height: 1.45;
      }}
      .insight-grid {{
        display: grid;
        gap: 18px;
        grid-template-columns: 1.35fr 1fr;
      }}
      .panel {{
        border-radius: 22px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: rgba(4, 9, 18, 0.55);
        padding: 22px;
      }}
      .panel h3 {{
        margin: 0 0 16px;
        font-size: 18px;
      }}
      .panel-grid {{
        display: grid;
        gap: 14px;
      }}
      .metric-card {{
        padding: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.028);
      }}
      .metric-card .micro {{
        color: #6f83a0;
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-weight: 800;
      }}
      .metric-card .title {{
        margin-top: 8px;
        font-size: 15px;
        font-weight: 800;
      }}
      .metric-card .desc {{
        margin-top: 8px;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.5;
      }}
      .meter-row + .meter-row {{ margin-top: 14px; }}
      .meter-head {{
        display: flex;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 8px;
        color: #cfe0f7;
        font-size: 12px;
        font-weight: 700;
      }}
      .meter-track {{
        height: 10px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.05);
        overflow: hidden;
      }}
      .meter-fill {{
        height: 100%;
        border-radius: 999px;
      }}
      .meter-fill.good {{
        background: linear-gradient(90deg, #1e7fc7, #49d79e);
        box-shadow: 0 0 18px rgba(73, 215, 158, 0.2);
      }}
      .meter-fill.watch {{
        background: linear-gradient(90deg, #2f82ff, #f6c46a);
        box-shadow: 0 0 18px rgba(246, 196, 106, 0.18);
      }}
      .meter-fill.hot {{
        background: linear-gradient(90deg, #d14d6c, #ff7987);
        box-shadow: 0 0 18px rgba(255, 121, 135, 0.2);
      }}
      .service-grid {{
        display: grid;
        gap: 16px;
      }}
      .service-card {{
        border-radius: 22px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: rgba(4, 9, 18, 0.6);
        overflow: hidden;
      }}
      .service-top {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto auto;
        gap: 18px;
        align-items: center;
        padding: 20px 22px;
      }}
      .service-card h3 {{
        margin: 0;
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.03em;
      }}
      .service-card .meta {{
        margin-top: 8px;
        color: var(--muted);
        font-size: 13px;
      }}
      .tag {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 8px 12px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: 900;
        letter-spacing: 0.16em;
        text-transform: uppercase;
      }}
      .healthy {{
        color: var(--green);
        background: rgba(73, 215, 158, 0.12);
        border: 1px solid rgba(73, 215, 158, 0.14);
      }}
      .watch {{
        color: var(--amber);
        background: rgba(246, 196, 106, 0.12);
        border: 1px solid rgba(246, 196, 106, 0.14);
      }}
      .breach {{
        color: var(--red);
        background: rgba(255, 121, 135, 0.12);
        border: 1px solid rgba(255, 121, 135, 0.14);
      }}
      .score-stack {{
        text-align: right;
      }}
      .score-stack .micro {{
        color: #6f83a0;
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-weight: 800;
      }}
      .score-stack .value {{
        margin-top: 6px;
        font-size: 28px;
        font-weight: 900;
      }}
      .service-bottom {{
        padding: 18px 22px 22px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        background: rgba(255, 255, 255, 0.02);
      }}
      .two-col {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
      }}
      .pill-stack {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }}
      .source-pill {{
        display: inline-flex;
        align-items: center;
        padding: 8px 10px;
        border-radius: 999px;
        background: rgba(114, 195, 255, 0.09);
        color: var(--cyan);
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }}
      .table-shell {{
        overflow: hidden;
        border-radius: 22px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: rgba(4, 9, 18, 0.58);
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
      }}
      th, td {{
        padding: 16px 18px;
        text-align: left;
        vertical-align: top;
      }}
      thead th {{
        color: #7385a0;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        font-weight: 900;
        background: rgba(255, 255, 255, 0.035);
      }}
      tbody tr + tr td {{
        border-top: 1px solid rgba(255, 255, 255, 0.05);
      }}
      tbody tr:hover td {{
        background: rgba(114, 195, 255, 0.03);
      }}
      .subtext {{
        margin-top: 6px;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.45;
      }}
      .code-panel {{
        border-radius: 22px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(2, 6, 12, 0.92);
        padding: 18px 20px 20px;
      }}
      .code-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 12px;
        margin-bottom: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      }}
      .code-head span {{
        color: var(--cyan);
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.18em;
      }}
      .lights {{
        display: flex;
        gap: 7px;
      }}
      .lights i {{
        display: block;
        width: 9px;
        height: 9px;
        border-radius: 50%;
      }}
      .lights i:nth-child(1) {{ background: rgba(255, 121, 135, 0.7); }}
      .lights i:nth-child(2) {{ background: rgba(246, 196, 106, 0.7); }}
      .lights i:nth-child(3) {{ background: rgba(73, 215, 158, 0.7); }}
      pre {{
        margin: 0;
        white-space: pre-wrap;
        overflow: auto;
        color: #dce8fb;
        font-size: 13px;
        line-height: 1.6;
        font-family: "Cascadia Code", Consolas, monospace;
      }}
      .footer-strip {{
        display: flex;
        justify-content: space-between;
        gap: 16px;
        margin-top: 18px;
        padding: 4px 2px 10px;
        color: #6d809b;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.16em;
      }}
      .footer-strip strong {{
        color: #b8c9de;
      }}
      @media (max-width: 1080px) {{
        .shell {{ grid-template-columns: 1fr; }}
        .sidebar {{ display: none; }}
        .stats-grid,
        .insight-grid,
        .two-col {{ grid-template-columns: 1fr; }}
        .service-top {{ grid-template-columns: 1fr; align-items: start; }}
      }}
    </style>
  </head>
  <body>
    <div class="shell">
      <aside class="sidebar">
        <div class="brand">
          <div class="brand-mark">EB</div>
          <div>
            <strong>Error Budget Allocator</strong>
            <span>Instance: REL-PRIME</span>
          </div>
        </div>
        <nav>{sidebar}</nav>
        <dl class="meta">
          <dt>Reliability mode</dt>
          <dd>Budget arbitration</dd>
          <dt>Lead pressure</dt>
          <dd>{summary["breachCount"]} breach / {summary["watchCount"]} watch</dd>
          <dt>Projected overrun</dt>
          <dd>{summary["projectedOverrunMinutes"]} minutes</dd>
        </dl>
      </aside>
      <main>
        <header class="topbar">
          <div class="status-chip"><span class="status-dot"></span>Burn telemetry live</div>
          <div class="topbar-right">
            <div class="meta-block">
              <span>Control lane</span>
              <strong>Reliability / SLO</strong>
            </div>
            <div class="meta-block">
              <span>Watch pressure</span>
              <strong>{summary["watchCount"]} services</strong>
            </div>
            <a class="action-pill" href="/docs">Open API docs</a>
          </div>
        </header>
        <div class="wrap">
          <section class="hero">
            <div class="hero-eyebrow">Error Budget Allocator</div>
            <h1>{escape(title)}</h1>
            <p class="hero-subtitle">{escape(subtitle)}</p>
            <div class="hero-strip">
              <div class="hero-kpi"><div class="k">Services in scope</div><div class="v">{summary["serviceCount"]}</div></div>
              <div class="hero-kpi"><div class="k">Projected overrun</div><div class="v">{summary["projectedOverrunMinutes"]}</div></div>
              <div class="hero-kpi"><div class="k">Average projected burn</div><div class="v">{summary["averageProjectedPct"]}%</div></div>
              <div class="hero-kpi"><div class="k">Hottest service</div><div class="v" style="font-size:22px">{escape(summary["hottestService"])}</div></div>
            </div>
            <div class="hero-callout">
              <strong>Lead recommendation</strong>
              <p>{escape(summary["leadRecommendation"])}</p>
            </div>
            <div class="tab-row">{tabs}</div>
          </section>
          {body}
          <div class="footer-strip">
            <span><strong>Discipline:</strong> Error budget governance</span>
            <span><strong>Bias:</strong> Operator-first / CI-ready</span>
            <span><strong>Focus:</strong> Burn, overrun, dependency pressure</span>
          </div>
        </div>
      </main>
    </div>
  </body>
</html>"""


def render_overview() -> str:
    summary = SERVICE.summary()
    catalog = SERVICE.service_catalog()
    raw_services = _service_lookup()
    owner_rows = SERVICE.owner_allocations()
    owner_cards = "".join(
        f"""
        <div class="metric-card">
          <div class="micro">{escape(item["owner"])}</div>
          <div class="title">{item["averageProjectedBurnPct"]}% projected burn</div>
          <div class="desc">{item["serviceCount"]} services · {item["projectedOverrunMinutes"]}m projected overrun</div>
        </div>
        """
        for item in owner_rows[:3]
    )
    cards = []
    for row in catalog[:4]:
        raw = raw_services[row["serviceId"]]
        cards.append(
            f"""
            <div class="service-card">
              <div class="service-top">
                <div>
                  <h3>{escape(row["name"])}</h3>
                  <div class="meta">{escape(row["owner"])} · {escape(row["tier"])} · {escape(row["environment"])} · SLO {escape(row["sloTarget"])}</div>
                </div>
                <span class="tag {_verdict_class(row["verdict"])}">{escape(row["verdict"])}</span>
                <div class="score-stack">
                  <div class="micro">Risk score</div>
                  <div class="value">{row["riskScore"]}</div>
                </div>
              </div>
              <div class="service-bottom">
                <div class="two-col">
                  <div>{_score_bars(raw)}</div>
                  <div class="panel-grid">
                    <div class="metric-card">
                      <div class="micro">Budget posture</div>
                      <div class="title">{row["remainingMinutes"]}m left · {row["projectedOverrunMinutes"]}m projected overrun</div>
                      <div class="desc">{escape(row["topConcern"])}</div>
                    </div>
                    <div class="metric-card">
                      <div class="micro">Next move</div>
                      <div class="title">{row["burnPct"]}% live burn · {row["projectedBurnPct"]}% projected</div>
                      <div class="desc">{escape(row["nextAction"])}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            """
        )
    body = f"""
      <section class="page-section">
        <div class="section-head">
          <strong>Reliability overview</strong>
          <h2>Budget headroom, burn pressure, and who should give up margin first.</h2>
          <p>The allocator is not just watching raw burn. It is deciding which healthy services can lend budget and which risky lanes need to slow down.</p>
        </div>
        <div class="section-body">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="label">Monthly budget</div>
              <div class="value">{summary["totalBudgetMinutes"]}m</div>
              <div class="sub">Combined error-budget allowance across the current service fleet.</div>
            </div>
            <div class="stat-card">
              <div class="label">Consumed</div>
              <div class="value">{summary["consumedMinutes"]}m</div>
              <div class="sub">Live burn already spent before projected deployment and dependency pressure lands.</div>
            </div>
            <div class="stat-card">
              <div class="label">Projected burn</div>
              <div class="value">{summary["projectedConsumedMinutes"]}m</div>
              <div class="sub">Where the fleet lands if the current pace and failure profile continue.</div>
            </div>
            <div class="stat-card">
              <div class="label">Breach lanes</div>
              <div class="value">{summary["breachCount"]}</div>
              <div class="sub">Services already close enough to the wall that budget reallocation should happen now.</div>
            </div>
          </div>
          <div class="insight-grid" style="margin-top: 20px;">
            <div class="panel">
              <h3>Owner allocation posture</h3>
              <div class="panel-grid">{owner_cards}</div>
            </div>
            <div class="panel">
              <h3>Operator notes</h3>
              <div class="panel-grid">
                <div class="metric-card">
                  <div class="micro">Why this matters</div>
                  <div class="title">A tier-0 lane can burn the whole month in one bad release train.</div>
                  <div class="desc">That is why the allocator keeps dependency pressure, incidents, and rollout risk in the same frame.</div>
                </div>
                <div class="metric-card">
                  <div class="micro">Headroom strategy</div>
                  <div class="title">Healthy services should lend budget intentionally, not by accident.</div>
                  <div class="desc">Surplus margin becomes useful only when it is visible enough to move before a freeze becomes mandatory.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section class="page-section">
        <div class="section-head">
          <strong>Burn board</strong>
          <h2>The allocator keeps the hottest lanes at the top.</h2>
          <p>Every row shows where budget is disappearing, why, and whether the right answer is to slow down, borrow headroom, or prepare a freeze.</p>
        </div>
        <div class="section-body">
          <div class="service-grid">
            {"".join(cards)}
          </div>
        </div>
      </section>
    """
    return _shell(
        "Reliability overview",
        "Allocating error-budget burn across services, dependencies, and deployment windows.",
        "overview",
        body,
    )


def render_allocation_queue() -> str:
    queue = SERVICE.allocation_queue()
    raw_services = _service_lookup()
    cards = []
    for row in queue:
        raw = raw_services[row["serviceId"]]
        sources = row["sourceCandidates"]
        source_markup = "".join(
            f'<span class="source-pill">{escape(item["name"])} · {item["lendableMinutes"]}m</span>'
            for item in sources
        ) or '<span class="source-pill">No healthy donor yet</span>'
        cards.append(
            f"""
            <div class="service-card">
              <div class="service-top">
                <div>
                  <h3>{escape(row["name"])}</h3>
                  <div class="meta">{escape(row["owner"])} · {escape(row["tier"])} · {escape(raw["deployWindowRisk"])} deploy window risk</div>
                </div>
                <span class="tag {_verdict_class(row["verdict"])}">{escape(row["verdict"])}</span>
                <div class="score-stack">
                  <div class="micro">Borrow target</div>
                  <div class="value">{row["budgetShiftMinutes"]}m</div>
                </div>
              </div>
              <div class="service-bottom">
                <div class="two-col">
                  <div class="panel-grid">
                    <div class="metric-card">
                      <div class="micro">Primary concern</div>
                      <div class="title">{escape(row["topConcern"])}</div>
                      <div class="desc">{escape(row["nextAction"])}</div>
                    </div>
                    <div class="metric-card">
                      <div class="micro">Healthy source candidates</div>
                      <div class="pill-stack">{source_markup}</div>
                    </div>
                  </div>
                  <div>{_score_bars(raw)}</div>
                </div>
              </div>
            </div>
            """
        )
    body = f"""
      <section class="page-section">
        <div class="section-head">
          <strong>Allocation queue</strong>
          <h2>Who needs budget help first.</h2>
          <p>The allocator prioritizes services that are most likely to breach error-budget policy before the month closes, then shows which healthier lanes can lend margin.</p>
        </div>
        <div class="section-body">
          <div class="service-grid">
            {"".join(cards)}
          </div>
        </div>
      </section>
    """
    return _shell(
        "Allocation queue",
        "The services most likely to need budget relief, rollback discipline, or a temporary freeze.",
        "allocations",
        body,
    )


def render_service_matrix() -> str:
    rows = "".join(
        f"""
        <tr>
          <td>
            <strong>{escape(item["name"])}</strong>
            <div class="subtext">{escape(item["owner"])} · {escape(item["tier"])}</div>
          </td>
          <td>{item["burnPct"]}%</td>
          <td>{item["projectedBurnPct"]}%</td>
          <td>{item["remainingMinutes"]}m</td>
          <td>{item["dependencyPressure"]}</td>
          <td>{item["criticalIncidents"]}</td>
          <td><span class="tag {_verdict_class(item["verdict"])}">{escape(item["verdict"])}</span></td>
        </tr>
        """
        for item in SERVICE.burn_matrix()
    )
    body = f"""
      <section class="page-section">
        <div class="section-head">
          <strong>Service matrix</strong>
          <h2>One table for burn, overrun, and dependency pressure.</h2>
          <p>This is the compact surface that platform and SRE leads can scan when they need to decide whether to ship, slow down, or borrow headroom.</p>
        </div>
        <div class="section-body">
          <div class="table-shell">
            <table>
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Live burn</th>
                  <th>Projected burn</th>
                  <th>Remaining</th>
                  <th>Dependency pressure</th>
                  <th>Critical incidents</th>
                  <th>Verdict</th>
                </tr>
              </thead>
              <tbody>{rows}</tbody>
            </table>
          </div>
        </div>
      </section>
    """
    return _shell(
        "Service matrix",
        "Inventory view for burn rate, projected overrun, remaining budget, and dependency pressure.",
        "matrix",
        body,
    )


def render_burn_methodology() -> str:
    payload = json.dumps(SERVICE.sample_payload(), indent=2)
    body = f"""
      <section class="page-section">
        <div class="section-head">
          <strong>Methodology</strong>
          <h2>How budget allocation pressure gets scored.</h2>
          <p>The allocator deliberately mixes burn pace with deployment and dependency context so a stable-looking service does not hide behind clean aggregates.</p>
        </div>
        <div class="section-body">
          <div class="insight-grid">
            <div class="panel">
              <h3>Scoring factors</h3>
              <div class="panel-grid">
                <div class="metric-card">
                  <div class="micro">Burn posture</div>
                  <div class="title">Live burn and projected burn carry the heaviest weight.</div>
                  <div class="desc">A service that is already consuming budget too quickly should be visible before the incident review asks why nobody slowed it down.</div>
                </div>
                <div class="metric-card">
                  <div class="micro">Dependency pressure</div>
                  <div class="title">Shared-service fragility changes the meaning of every lost minute.</div>
                  <div class="desc">A tier-0 service with dependency drag deserves different treatment than a self-contained backend with the same burn percentage.</div>
                </div>
                <div class="metric-card">
                  <div class="micro">Change risk</div>
                  <div class="title">Failure-prone release windows should not keep spending like healthy lanes.</div>
                  <div class="desc">Change failure rate, deploy window risk, and stale recovery drills all push the score higher.</div>
                </div>
              </div>
            </div>
            <div class="panel">
              <div class="code-panel">
                <div class="code-head">
                  <span>/api/sample</span>
                  <div class="lights"><i></i><i></i><i></i></div>
                </div>
                <pre><code>{escape(payload)}</code></pre>
              </div>
            </div>
          </div>
        </div>
      </section>
    """
    return _shell(
        "Methodology",
        "How the allocator turns burn, overrun, and change pressure into a decision surface.",
        "methodology",
        body,
    )


def render_api_summary() -> str:
    payload = json.dumps(SERVICE.sample_payload(), indent=2)
    body = f"""
      <section class="page-section">
        <div class="section-head">
          <strong>API summary</strong>
          <h2>Structured outputs for CI, SRE reviews, and reliability planning.</h2>
          <p>The payload is designed to feed deployment gates, reliability reviews, and budget arbitration workflows without losing the operator explanation layer.</p>
        </div>
        <div class="section-body">
          <div class="insight-grid">
            <div class="panel">
              <h3>Why the payload matters</h3>
              <div class="panel-grid">
                <div class="metric-card">
                  <div class="micro">Release governance</div>
                  <div class="title">Block deploys when projected burn crosses the line.</div>
                  <div class="desc">A pipeline can stop risky change windows when breach lanes are already consuming shared margin.</div>
                </div>
                <div class="metric-card">
                  <div class="micro">Owner planning</div>
                  <div class="title">Show which teams should lend budget and which teams should slow down.</div>
                  <div class="desc">Owner allocations make headroom visible before the monthly review becomes reactive.</div>
                </div>
                <div class="metric-card">
                  <div class="micro">Incident follow-through</div>
                  <div class="title">Keep error-budget decisions tied to the incident and deploy history that caused them.</div>
                  <div class="desc">The allocator is more useful when burn posture and narrative stay in the same record.</div>
                </div>
              </div>
            </div>
            <div class="panel">
              <div class="code-panel">
                <div class="code-head">
                  <span>/api/sample</span>
                  <div class="lights"><i></i><i></i><i></i></div>
                </div>
                <pre><code>{escape(payload)}</code></pre>
              </div>
            </div>
          </div>
        </div>
      </section>
    """
    return _shell(
        "API summary",
        "The allocator emits structured burn and budget decisions that can plug into broader reliability workflows.",
        "methodology",
        body,
    )
