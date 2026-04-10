"""
Network Monitoring Dashboard — Streamlit Frontend
"""

import time
from datetime import datetime

import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ─── Configuration ────────────────────────────────────────────────────────────
DEFAULT_API_URL = "http://localhost:8000"

# ─── Page Setup ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NetMonitor",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "**Network Monitoring Utility** — Real-time async network node dashboard",
    },
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Base & Background ───────────────────────────────── */
[data-testid="stAppViewContainer"] {
  background: linear-gradient(160deg, #0d0f1a 0%, #0a0c16 60%, #080a14 100%);
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0d1117 0%, #10141f 100%);
  border-right: 1px solid #1e2d3d;
}
[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

/* ── Global Text ─────────────────────────────────────── */
h1, h2, h3, h4 { color: #e6edf3 !important; }
p, li { color: #8b949e; }

/* ── Metric Cards ────────────────────────────────────── */
[data-testid="metric-container"] {
  background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
  border: 1px solid #21262d;
  border-radius: 12px;
  padding: 18px 20px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  transition: transform 0.2s, box-shadow 0.2s;
}
[data-testid="metric-container"]:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
[data-testid="stMetricLabel"] {
  color: #7d8590 !important;
  font-size: 0.75rem !important;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
[data-testid="stMetricValue"] {
  color: #e6edf3 !important;
  font-size: 2rem !important;
  font-weight: 700;
}

/* ── Tabs ────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {
  color: #7d8590;
  font-weight: 500;
  letter-spacing: 0.04em;
  padding: 10px 20px;
  transition: color 0.2s;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  color: #58a6ff !important;
  border-bottom: 2px solid #58a6ff;
}
[data-testid="stTabs"] [role="tablist"] {
  border-bottom: 1px solid #21262d;
  gap: 4px;
}

/* ── Buttons ─────────────────────────────────────────── */
.stButton > button {
  background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
  color: #fff !important;
  border: none !important;
  border-radius: 8px;
  font-weight: 600;
  padding: 0.45rem 1.1rem;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(46,160,67,0.3);
}
.stButton > button:hover {
  background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%) !important;
  box-shadow: 0 4px 16px rgba(46,160,67,0.5) !important;
  transform: translateY(-1px);
}
.stButton > button[kind="secondary"] {
  background: linear-gradient(135deg, #b62324 0%, #da3633 100%) !important;
  box-shadow: 0 2px 8px rgba(218,54,51,0.3) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: linear-gradient(135deg, #da3633 0%, #f85149 100%) !important;
  box-shadow: 0 4px 16px rgba(218,54,51,0.5) !important;
}

/* ── Inputs ──────────────────────────────────────────── */
[data-testid="stTextInput"] > div > div > input,
[data-testid="stNumberInput"] > div > div > input,
[data-testid="stSelectbox"] > div > div {
  background: #161b22 !important;
  border: 1px solid #30363d !important;
  border-radius: 8px !important;
  color: #e6edf3 !important;
}
[data-testid="stTextInput"] > div > div > input:focus,
[data-testid="stNumberInput"] > div > div > input:focus {
  border-color: #58a6ff !important;
  box-shadow: 0 0 0 3px rgba(88,166,255,0.15) !important;
}
label { color: #7d8590 !important; font-size: 0.82rem !important; }

/* ── Slider ──────────────────────────────────────────── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
  background: #58a6ff !important;
}

/* ── Forms ───────────────────────────────────────────── */
[data-testid="stForm"] {
  background: #0d1117;
  border: 1px solid #21262d;
  border-radius: 10px;
  padding: 16px;
}

/* ── Scrollbar ───────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0d0f1a; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #58a6ff; }

/* ── Divider ─────────────────────────────────────────── */
hr { border-color: #21262d !important; margin: 12px 0; }

/* ── Status Badges ───────────────────────────────────── */
.badge-online {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 10px;
  background: rgba(46,160,67,0.15);
  color: #3fb950;
  border: 1px solid rgba(63,185,80,0.3);
  border-radius: 20px;
  font-size: 0.76rem; font-weight: 700; letter-spacing: 0.06em;
}
.badge-offline {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 10px;
  background: rgba(248,81,73,0.15);
  color: #f85149;
  border: 1px solid rgba(248,81,73,0.3);
  border-radius: 20px;
  font-size: 0.76rem; font-weight: 700; letter-spacing: 0.06em;
}
.badge-unknown {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 10px;
  background: rgba(139,148,158,0.12);
  color: #7d8590;
  border: 1px solid rgba(139,148,158,0.25);
  border-radius: 20px;
  font-size: 0.76rem; font-weight: 700; letter-spacing: 0.06em;
}

/* ── Pulse Dots ──────────────────────────────────────── */
@keyframes pulse-green { 0%,100%{box-shadow:0 0 0 0 rgba(63,185,80,0.5)} 50%{box-shadow:0 0 0 5px rgba(63,185,80,0)} }
@keyframes pulse-red   { 0%,100%{box-shadow:0 0 0 0 rgba(248,81,73,0.5)} 50%{box-shadow:0 0 0 5px rgba(248,81,73,0)} }
.dot-online  { display:inline-block; width:7px; height:7px; border-radius:50%; background:#3fb950; animation:pulse-green 2s ease-in-out infinite; }
.dot-offline { display:inline-block; width:7px; height:7px; border-radius:50%; background:#f85149; animation:pulse-red 2s ease-in-out infinite; }
.dot-unknown { display:inline-block; width:7px; height:7px; border-radius:50%; background:#7d8590; }

/* ── Node Table ──────────────────────────────────────── */
.node-table {
  width: 100%; border-collapse: separate; border-spacing: 0 5px;
}
.node-table thead th {
  color: #7d8590; font-size: 0.73rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.1em;
  padding: 8px 16px; border-bottom: 1px solid #21262d;
}
.node-table tbody tr {
  background: linear-gradient(90deg,#161b22 0%,#1c2128 100%);
  transition: background 0.15s;
}
.node-table tbody tr:hover {
  background: linear-gradient(90deg,#1c2128 0%,#21262d 100%);
}
.node-table td {
  padding: 13px 16px; font-size: 0.88rem; color: #c9d1d9;
  border-top: 1px solid rgba(33,38,45,0.8); border-bottom: 1px solid rgba(33,38,45,0.8);
}
.node-table td:first-child { border-left: 1px solid rgba(33,38,45,0.8); border-radius: 8px 0 0 8px; }
.node-table td:last-child  { border-right: 1px solid rgba(33,38,45,0.8); border-radius: 0 8px 8px 0; }

/* ── Log Table ───────────────────────────────────────── */
.log-table {
  width: 100%; border-collapse: collapse;
}
.log-table thead th {
  color: #7d8590; font-size: 0.73rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.1em;
  padding: 10px 14px; border-bottom: 1px solid #21262d;
}
.log-table tbody tr { border-bottom: 1px solid #161b22; transition: background 0.12s; }
.log-table tbody tr:hover { background: rgba(88,166,255,0.04); }
.log-table td { padding: 10px 14px; font-size: 0.84rem; color: #8b949e; }

/* ── Section Card ────────────────────────────────────── */
.section-card {
  background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
  border: 1px solid #21262d;
  border-radius: 12px;
  padding: 20px 22px;
  margin-bottom: 16px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.3);
}
.section-title {
  font-size: 0.8rem !important; font-weight: 700 !important;
  color: #7d8590 !important; text-transform: uppercase; letter-spacing: 0.12em;
  margin: 0 0 16px 0;
}

/* ── App Header ──────────────────────────────────────── */
.app-header {
  background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
  border: 1px solid #21262d;
  border-radius: 14px;
  padding: 20px 28px;
  margin-bottom: 24px;
  display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 4px 28px rgba(0,0,0,0.35);
}
.app-title { font-size: 1.55rem; font-weight: 800; color: #e6edf3; margin: 0; letter-spacing: -0.02em; }
.app-subtitle { font-size: 0.82rem; color: #7d8590; margin: 5px 0 0; }
.api-ok  { color: #3fb950; font-size: 0.8rem; font-weight: 700; }
.api-err { color: #f85149; font-size: 0.8rem; font-weight: 700; }
.refresh-badge {
  display: inline-block;
  background: rgba(88,166,255,0.1);
  border: 1px solid rgba(88,166,255,0.2);
  border-radius: 20px;
  padding: 3px 12px;
  font-size: 0.75rem; color: #58a6ff;
  margin-top: 6px;
}

/* ── Sidebar Branding ────────────────────────────────── */
.sidebar-brand { text-align: center; padding: 8px 0 16px; }
.brand-icon { font-size: 2.6rem; margin-bottom: 4px; }
.brand-name { font-size: 1.05rem; font-weight: 800; color: #e6edf3; letter-spacing: -0.01em; }
.brand-sub  { font-size: 0.72rem; color: #484f58; margin-top: 2px; }
.sidebar-section-label {
  font-size: 0.72rem; font-weight: 700; color: #484f58;
  text-transform: uppercase; letter-spacing: 0.12em;
  margin: 20px 0 10px; padding: 0 2px;
}

/* ── Empty State ─────────────────────────────────────── */
.empty-state { text-align: center; padding: 56px 24px; }
.empty-icon  { font-size: 3.2rem; margin-bottom: 14px; }
.empty-text  { font-size: 0.92rem; color: #484f58; line-height: 1.6; }

/* ── Mini Progress Bar ───────────────────────────────── */
.uptime-bar-wrap { background: #21262d; border-radius: 4px; height: 6px; overflow: hidden; margin-top: 4px; }
.uptime-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg,#238636,#3fb950); }

/* ── Misc ────────────────────────────────────────────── */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
[data-testid="stAlert"] { border-radius: 10px; border: none; }
</style>
""",
    unsafe_allow_html=True,
)

# ─── Session State ────────────────────────────────────────────────────────────
if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL
if "refresh_sec" not in st.session_state:
    st.session_state.refresh_sec = 10
if "log_limit" not in st.session_state:
    st.session_state.log_limit = 100

# ─── Auto-Refresh ─────────────────────────────────────────────────────────────
refresh_count = st_autorefresh(
    interval=st.session_state.refresh_sec * 1000,
    limit=None,
    key="netmon_refresh",
)

# ─── API Helpers ──────────────────────────────────────────────────────────────

def _get(path: str, params: dict | None = None) -> tuple[object, bool]:
    try:
        r = requests.get(
            f"{st.session_state.api_url}{path}",
            params=params,
            timeout=5,
        )
        r.raise_for_status()
        return r.json(), True
    except Exception:
        return None, False


def _post(path: str, payload: dict) -> tuple[dict | None, int | None]:
    try:
        r = requests.post(
            f"{st.session_state.api_url}{path}",
            json=payload,
            timeout=5,
        )
        return r.json() if r.content else None, r.status_code
    except Exception:
        return None, None


def _delete(path: str) -> bool:
    try:
        r = requests.delete(f"{st.session_state.api_url}{path}", timeout=5)
        return r.status_code == 204
    except Exception:
        return False


def get_nodes() -> tuple[list, bool]:
    data, ok = _get("/nodes")
    return (data or []), ok


def get_logs(limit: int = 100) -> list:
    data, _ = _get("/logs", params={"limit": limit})
    return data or []


# ─── Format Helpers ───────────────────────────────────────────────────────────

def status_badge(status: str) -> str:
    if status == "ONLINE":
        return '<span class="badge-online"><span class="dot-online"></span>ONLINE</span>'
    if status == "OFFLINE":
        return '<span class="badge-offline"><span class="dot-offline"></span>OFFLINE</span>'
    return '<span class="badge-unknown"><span class="dot-unknown"></span>UNKNOWN</span>'


def fmt_latency(lat: float | None) -> str:
    if lat is None:
        return '<span style="color:#484f58">—</span>'
    if lat < 80:
        color, label = "#3fb950", "fast"
    elif lat < 250:
        color, label = "#d29922", "ok"
    else:
        color, label = "#f85149", "slow"
    return (
        f'<span style="color:{color};font-weight:700">{lat:.1f}<span '
        f'style="font-size:0.72rem;color:{color}88;font-weight:500"> ms</span></span> '
        f'<span style="font-size:0.7rem;color:#484f58">({label})</span>'
    )


def fmt_dt(ts: str | None, short: bool = False) -> str:
    if not ts:
        return '<span style="color:#484f58">Never</span>'
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        fmt = dt.strftime("%H:%M:%S") if short else dt.strftime("%Y-%m-%d&nbsp;%H:%M:%S")
        return f'<span style="color:#7d8590;font-family:monospace;font-size:0.83rem">{fmt}</span>'
    except ValueError:
        return f'<span style="color:#484f58">{ts}</span>'


def uptime_bar(online: int, total: int) -> str:
    pct = (online / total * 100) if total else 0
    color = "#3fb950" if pct >= 80 else "#d29922" if pct >= 50 else "#f85149"
    return (
        f'<div class="uptime-bar-wrap">'
        f'<div class="uptime-bar-fill" style="width:{pct:.0f}%;background:linear-gradient(90deg,{color}88,{color})"></div>'
        f"</div>"
    )


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="brand-icon">🌐</div>
          <div class="brand-name">NetMonitor</div>
          <div class="brand-sub">Async Network Utility</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Connection Settings ────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section-label">⚙️ Connection</div>', unsafe_allow_html=True)
    api_url_input = st.text_input(
        "API Base URL",
        value=st.session_state.api_url,
        key="_api_url_in",
        placeholder="http://localhost:8000",
    )
    if api_url_input != st.session_state.api_url:
        st.session_state.api_url = api_url_input.rstrip("/")

    st.markdown('<div class="sidebar-section-label">🔄 Auto-Refresh</div>', unsafe_allow_html=True)
    refresh_val = st.slider("Interval (seconds)", 5, 60, st.session_state.refresh_sec, step=5)
    if refresh_val != st.session_state.refresh_sec:
        st.session_state.refresh_sec = refresh_val

    st.markdown("---")

    # ── Add Node Form ──────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section-label">➕ Add New Node</div>', unsafe_allow_html=True)
    with st.form("add_node_form", clear_on_submit=True):
        new_addr = st.text_input(
            "Host / IP Address",
            placeholder="e.g. 192.168.1.1 or google.com",
        )
        new_port = st.number_input(
            "Port (optional, 0 = none)",
            min_value=0,
            max_value=65535,
            value=0,
            step=1,
        )
        add_btn = st.form_submit_button("Add Node", use_container_width=True)

        if add_btn:
            addr = new_addr.strip()
            if not addr:
                st.warning("Enter a host address.")
            else:
                payload: dict = {"address": addr}
                if new_port > 0:
                    payload["port"] = int(new_port)
                _, code = _post("/nodes", payload)
                if code == 201:
                    st.success(f"Added **{addr}**")
                elif code == 409:
                    st.error("Node already exists.")
                elif code is None:
                    st.error("Cannot reach API.")
                else:
                    st.error(f"Error {code}")

    st.markdown("---")

    # ── Log Limit ──────────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section-label">📋 Logs</div>', unsafe_allow_html=True)
    log_limit_val = st.selectbox("Max log entries", [50, 100, 200, 500, 1000], index=1)
    st.session_state.log_limit = log_limit_val

    st.markdown("---")
    now_str = datetime.now().strftime("%H:%M:%S")
    st.markdown(
        f'<div style="text-align:center">'
        f'<span class="refresh-badge">Refresh #{refresh_count} · {now_str}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

# ─── Fetch Data ───────────────────────────────────────────────────────────────
nodes, api_ok = get_nodes()
logs = get_logs(limit=st.session_state.log_limit)

# ─── Header ───────────────────────────────────────────────────────────────────
total = len(nodes)
online = sum(1 for n in nodes if n["last_status"] == "ONLINE")
offline = sum(1 for n in nodes if n["last_status"] == "OFFLINE")
unknown = total - online - offline

api_html = (
    '<span class="api-ok">● API Connected</span>'
    if api_ok
    else '<span class="api-err">● API Unreachable</span>'
)
progress_html = uptime_bar(online, total) if total else ""

st.markdown(
    f"""
    <div class="app-header">
      <div>
        <p class="app-title">🌐 Network Monitor</p>
        <p class="app-subtitle">Real-time async network node monitoring dashboard</p>
      </div>
      <div style="text-align:right">
        {api_html}
        <div style="color:#484f58;font-size:0.72rem;margin-top:4px">{st.session_state.api_url}</div>
        <div style="margin-top:8px;min-width:140px">{progress_html}</div>
        <div style="font-size:0.72rem;color:#484f58;margin-top:3px">{online}/{total} nodes online</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not api_ok:
    st.error(
        "Cannot reach the FastAPI backend. Make sure it is running, then check the API URL in the sidebar."
    )

# ─── Metric Row ───────────────────────────────────────────────────────────────
latencies = [n["last_latency"] for n in nodes if n.get("last_latency") is not None]
avg_lat = sum(latencies) / len(latencies) if latencies else None
min_lat = min(latencies) if latencies else None
log_count = len(logs)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Nodes", total)
c2.metric("Online", online)
c3.metric("Offline", offline)
c4.metric("Unknown", unknown)
c5.metric("Avg Latency", f"{avg_lat:.1f} ms" if avg_lat is not None else "N/A")
c6.metric("Log Events", log_count)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_dash, tab_logs, tab_manage = st.tabs(
    ["📊  Dashboard", "📋  Event Logs", "🔧  Manage Nodes"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Dashboard
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    if not nodes:
        st.markdown(
            """
            <div class="empty-state">
              <div class="empty-icon">📡</div>
              <div class="empty-text">No nodes are being monitored yet.<br>
              Add your first node using the sidebar on the left.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # ── Node Table ─────────────────────────────────────────────────────────
        rows_html = ""
        for node in nodes:
            port_str = (
                f'<span style="color:#58a6ff;font-size:0.82rem">:{node["port"]}</span>'
                if node.get("port")
                else ""
            )
            addr_cell = (
                f'<span style="color:#e6edf3;font-family:monospace">'
                f'{node["address"]}</span>{port_str}'
            )
            rows_html += f"""
            <tr>
              <td><span style="color:#484f58;font-size:0.8rem">#{node['id']}</span></td>
              <td>{addr_cell}</td>
              <td>{status_badge(node["last_status"])}</td>
              <td>{fmt_latency(node.get("last_latency"))}</td>
              <td>{fmt_dt(node.get("last_check_at"))}</td>
              <td>{fmt_dt(node.get("created_at"))}</td>
            </tr>
            """

        st.markdown(
            f"""
            <div class="section-card">
              <p class="section-title">📡 Monitored Nodes</p>
              <table class="node-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Address</th>
                    <th>Status</th>
                    <th>Latency</th>
                    <th>Last Check</th>
                    <th>Added</th>
                  </tr>
                </thead>
                <tbody>{rows_html}</tbody>
              </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Status Summary Cards ───────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            online_nodes = [n for n in nodes if n["last_status"] == "ONLINE"]
            items = "".join(
                f'<div style="padding:4px 0;border-bottom:1px solid #21262d;font-family:monospace;font-size:0.82rem;color:#c9d1d9">'
                f'<span class="dot-online" style="margin-right:8px"></span>{n["address"]}</div>'
                for n in online_nodes
            ) or '<span style="color:#484f58;font-size:0.85rem">None</span>'
            st.markdown(
                f'<div class="section-card">'
                f'<p class="section-title">🟢 Online Nodes ({online})</p>'
                f"{items}</div>",
                unsafe_allow_html=True,
            )

        with col_b:
            offline_nodes = [n for n in nodes if n["last_status"] == "OFFLINE"]
            items = "".join(
                f'<div style="padding:4px 0;border-bottom:1px solid #21262d;font-family:monospace;font-size:0.82rem;color:#c9d1d9">'
                f'<span class="dot-offline" style="margin-right:8px"></span>{n["address"]}</div>'
                for n in offline_nodes
            ) or '<span style="color:#484f58;font-size:0.85rem">None</span>'
            st.markdown(
                f'<div class="section-card">'
                f'<p class="section-title">🔴 Offline Nodes ({offline})</p>'
                f"{items}</div>",
                unsafe_allow_html=True,
            )

        with col_c:
            if latencies:
                lat_sorted = sorted(latencies)
                items_lat = "".join(
                    f'<div style="padding:5px 0;border-bottom:1px solid #21262d;'
                    f'display:flex;justify-content:space-between;align-items:center">'
                    f'<span style="font-family:monospace;font-size:0.8rem;color:#c9d1d9">{n["address"]}</span>'
                    f'{fmt_latency(n.get("last_latency"))}</div>'
                    for n in sorted(nodes, key=lambda x: x.get("last_latency") or 9999)
                    if n.get("last_latency") is not None
                )
                extra = (
                    f'<div style="margin-top:12px;padding-top:8px;border-top:1px solid #21262d">'
                    f'<span style="color:#484f58;font-size:0.75rem">MIN </span>'
                    f'<span style="color:#3fb950;font-weight:700">{min_lat:.1f} ms</span>'
                    f'&nbsp;&nbsp;<span style="color:#484f58;font-size:0.75rem">AVG </span>'
                    f'<span style="color:#d29922;font-weight:700">{avg_lat:.1f} ms</span>'
                    f"</div>"
                )
                st.markdown(
                    f'<div class="section-card">'
                    f'<p class="section-title">⚡ Latency Breakdown</p>'
                    f"{items_lat}{extra}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="section-card">'
                    '<p class="section-title">⚡ Latency Breakdown</p>'
                    '<span style="color:#484f58;font-size:0.85rem">No latency data yet.</span>'
                    "</div>",
                    unsafe_allow_html=True,
                )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Event Logs
# ══════════════════════════════════════════════════════════════════════════════
with tab_logs:
    if not logs:
        st.markdown(
            """
            <div class="empty-state">
              <div class="empty-icon">📋</div>
              <div class="empty-text">No status change events recorded yet.<br>
              Events appear here when a node transitions between ONLINE and OFFLINE.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # ── Summary strip ──────────────────────────────────────────────────────
        recoveries = sum(
            1 for l in logs if l["old_status"] == "OFFLINE" and l["new_status"] == "ONLINE"
        )
        outages = sum(
            1 for l in logs if l["old_status"] == "ONLINE" and l["new_status"] == "OFFLINE"
        )
        lc1, lc2, lc3 = st.columns(3)
        lc1.metric("Total Events", len(logs))
        lc2.metric("Recoveries", recoveries)
        lc3.metric("Outages", outages)
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Log table ──────────────────────────────────────────────────────────
        rows_html = ""
        for log in logs:
            old_s = log["old_status"]
            new_s = log["new_status"]

            if old_s == "OFFLINE" and new_s == "ONLINE":
                arrow = '<span style="color:#3fb950;font-size:1rem">↑</span>'
                row_hl = "background:rgba(46,160,67,0.04)"
            elif old_s == "ONLINE" and new_s == "OFFLINE":
                arrow = '<span style="color:#f85149;font-size:1rem">↓</span>'
                row_hl = "background:rgba(248,81,73,0.04)"
            else:
                arrow = '<span style="color:#7d8590">→</span>'
                row_hl = ""

            rows_html += f"""
            <tr style="{row_hl}">
              <td><span style="color:#484f58;font-size:0.78rem">#{log['id']}</span></td>
              <td><span style="color:#7d8590;font-size:0.82rem">Node&nbsp;{log['node_id']}</span></td>
              <td>{status_badge(old_s)}</td>
              <td style="text-align:center">{arrow}</td>
              <td>{status_badge(new_s)}</td>
              <td>{fmt_dt(log.get("timestamp"))}</td>
            </tr>
            """

        st.markdown(
            f"""
            <div class="section-card">
              <p class="section-title">📋 Status Change Events</p>
              <table class="log-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Node</th>
                    <th>From</th>
                    <th style="text-align:center">Dir</th>
                    <th>To</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>{rows_html}</tbody>
              </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Manage Nodes
# ══════════════════════════════════════════════════════════════════════════════
with tab_manage:
    if not nodes:
        st.markdown(
            """
            <div class="empty-state">
              <div class="empty-icon">🔧</div>
              <div class="empty-text">No nodes to manage.<br>
              Add nodes using the sidebar.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="color:#7d8590;font-size:0.85rem;margin-bottom:16px">'
            "Select a node to remove it from monitoring. This action is permanent."
            "</div>",
            unsafe_allow_html=True,
        )

        for node in nodes:
            port_str = f":{node['port']}" if node.get("port") else ""
            node_label = f"{node['address']}{port_str}"

            col_id, col_addr, col_status, col_lat, col_btn = st.columns(
                [0.6, 3, 1.5, 1.5, 1.2]
            )

            with col_id:
                st.markdown(
                    f'<div style="padding:10px 0;color:#484f58;font-size:0.8rem">#{node["id"]}</div>',
                    unsafe_allow_html=True,
                )

            with col_addr:
                st.markdown(
                    f'<div style="padding:10px 0;font-family:monospace;color:#e6edf3;font-size:0.9rem">'
                    f"{node_label}</div>",
                    unsafe_allow_html=True,
                )

            with col_status:
                st.markdown(
                    f'<div style="padding:10px 0">{status_badge(node["last_status"])}</div>',
                    unsafe_allow_html=True,
                )

            with col_lat:
                lat_html = fmt_latency(node.get("last_latency"))
                st.markdown(
                    f'<div style="padding:10px 0">{lat_html}</div>',
                    unsafe_allow_html=True,
                )

            with col_btn:
                if st.button("Delete", key=f"del_{node['id']}", type="secondary"):
                    if _delete(f"/nodes/{node['id']}"):
                        st.toast(f"Node **{node['address']}** removed.", icon="🗑️")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error(f"Failed to delete node {node['id']}")

            st.markdown(
                '<div style="border-bottom:1px solid #1c2128;margin:2px 0"></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Danger zone: delete all ────────────────────────────────────────────
        with st.expander("⚠️ Danger Zone"):
            st.markdown(
                '<div style="color:#f85149;font-size:0.85rem;margin-bottom:12px">'
                "Deleting all nodes will permanently remove them and all associated logs."
                "</div>",
                unsafe_allow_html=True,
            )
            confirm = st.checkbox("I understand this cannot be undone")
            if st.button("Delete All Nodes", type="secondary", disabled=not confirm):
                failed = 0
                for node in nodes:
                    if not _delete(f"/nodes/{node['id']}"):
                        failed += 1
                if failed == 0:
                    st.toast("All nodes deleted.", icon="🗑️")
                else:
                    st.warning(f"{failed} node(s) could not be deleted.")
                time.sleep(0.5)
                st.rerun()
