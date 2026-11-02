import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime
import urllib.parse
import uuid

st.set_page_config(
    page_title="Consignment Command Center",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom Dark Glassmorphic & Row Color-Coding CSS ---
st.markdown("""
<style>
    /* Main App Dark Theme Background */
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b 0%, #0f172a 45%, #020617 100%);
        color: #f8fafc;
    }

    /* Hide default Streamlit top decoration bar */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        padding: 20px 26px;
        margin-bottom: 22px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.6);
    }
    .hero-title {
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #ffffff;
        margin: 0;
    }
    .hero-subtitle {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 4px;
    }
    .sync-pill {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34d399;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 999px;
    }

    /* Custom KPI Cards */
    .kpi-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 14px;
        padding: 16px 18px;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.1;
    }
    .kpi-all { border-top: 3px solid #6366f1; }
    .kpi-inward { border-top: 3px solid #06b6d4; background: linear-gradient(180deg, rgba(6, 182, 212, 0.08) 0%, rgba(30, 41, 59, 0.7) 100%); }
    .kpi-outward { border-top: 3px solid #f59e0b; background: linear-gradient(180deg, rgba(245, 158, 11, 0.08) 0%, rgba(30, 41, 59, 0.7) 100%); }
    .kpi-transit { border-top: 3px solid #3b82f6; }
    .kpi-overdue { border-top: 3px solid #f43f5e; background: linear-gradient(180deg, rgba(244, 63, 94, 0.15) 0%, rgba(30, 41, 59, 0.75) 100%); }
    .kpi-delivered { border-top: 3px solid #10b981; }

    /* Overdue Alert Banner */
    .overdue-alert-banner {
        background: linear-gradient(90deg, rgba(136, 19, 55, 0.65) 0%, rgba(76, 5, 25, 0.75) 100%);
        border: 1px solid #f43f5e;
        border-left: 6px solid #fb7185;
        border-radius: 12px;
        padding: 14px 20px;
        margin: 16px 0;
        color: #ffe4e6;
        font-size: 0.9rem;
        box-shadow: 0 0 25px rgba(244, 63, 94, 0.25);
    }

    /* ==========================================================
       DYNAMIC ROW COLOR-CODING FOR STREAMLIT CONTAINERS
       ========================================================== */

    /* 1. INWARD ROW (Cyan / Teal Theme) */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.row-inward) {
        background: linear-gradient(90deg, rgba(6, 182, 212, 0.13) 0%, rgba(15, 23, 42, 0.85) 50%, rgba(15, 23, 42, 0.92) 100%) !important;
        border: 1px solid rgba(6, 182, 212, 0.38) !important;
        border-left: 6px solid #06b6d4 !important;
        border-radius: 14px !important;
        box-shadow: 0 6px 20px -6px rgba(6, 182, 212, 0.18) !important;
        padding: 6px 10px !important;
        margin-bottom: 12px !important;
    }

    /* 2. OUTWARD ROW (Amber / Gold Theme) */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.row-outward) {
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.13) 0%, rgba(15, 23, 42, 0.85) 50%, rgba(15, 23, 42, 0.92) 100%) !important;
        border: 1px solid rgba(245, 158, 11, 0.38) !important;
        border-left: 6px solid #f59e0b !important;
        border-radius: 14px !important;
        box-shadow: 0 6px 20px -6px rgba(245, 158, 11, 0.18) !important;
        padding: 6px 10px !important;
        margin-bottom: 12px !important;
    }

    /* 3. OVERDUE ROW (Crimson / Rose Alert Override) */
    @keyframes overduePulse {
        0%, 100% { box-shadow: 0 0 18px rgba(244, 63, 94, 0.28); border-color: rgba(244, 63, 94, 0.75); }
        50% { box-shadow: 0 0 28px rgba(244, 63, 94, 0.55); border-color: #fda4af; }
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.row-overdue) {
        background: linear-gradient(90deg, rgba(225, 29, 72, 0.24) 0%, rgba(69, 10, 26, 0.55) 45%, rgba(15, 23, 42, 0.95) 100%) !important;
        border: 1.5px solid rgba(244, 63, 94, 0.8) !important;
        border-left: 7px solid #f43f5e !important;
        border-radius: 14px !important;
        animation: overduePulse 2.5s infinite ease-in-out;
        padding: 6px 10px !important;
        margin-bottom: 14px !important;
    }

    /* Badges inside rows */
    .badge-inward {
        background: rgba(6, 182, 212, 0.2);
        color: #67e8f9;
        border: 1px solid rgba(6, 182, 212, 0.5);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .badge-outward {
        background: rgba(245, 158, 11, 0.2);
        color: #fcd34d;
        border: 1px solid rgba(245, 158, 11, 0.5);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .badge-overdue {
        background: #e11d48;
        color: #ffffff;
        border: 1px solid #fda4af;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        box-shadow: 0 0 12px rgba(225, 29, 72, 0.6);
    }
    .badge-due-today {
        background: rgba(234, 179, 8, 0.25);
        color: #fde047;
        border: 1px solid rgba(234, 179, 8, 0.6);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
    }
    .badge-delivered {
        background: rgba(16, 185, 129, 0.2);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.5);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
    }
    .badge-courier {
        background: rgba(99, 102, 241, 0.2);
        color: #c7d2fe;
        border: 1px solid rgba(99, 102, 241, 0.45);
        padding: 2px 9px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

COLUMNS = [
    "id",
    "direction",
    "item_name",
    "vendor_name",
    "courier_service",
    "docket_number",
    "location",
    "dispatch_date",
    "expected_date",
    "tracking_link",
    "current_status"
]

COURIER_URLS = {
    "Delhivery": lambda d: f"https://www.delhivery.com/track/package/{urllib.parse.quote(d)}",
    "Blue Dart": lambda d: "https://www.bluedart.com/tracking",
    "DTDC": lambda d: "https://www.dtdc.in/trace.asp",
    "India Post": lambda d: "https://www.indiapost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment.aspx",
    "Safexpress": lambda d: "https://www.safexpress.com/",
    "Trackon": lambda d: "https://trackon.in/",
    "Ecom Express": lambda d: "https://ecomexpress.in/tracking/",
    "Gati": lambda d: "https://www.gati.com/track-by-docket/",
    "Porter": lambda d: "https://porter.in/",
    "FedEx": lambda d: f"https://www.fedex.com/fedextrack/?trknbr={urllib.parse.quote(d)}",
    "DHL": lambda d: f"https://www.dhl.com/in-en/home/tracking.html?tracking-id={urllib.parse.quote(d)}",
    "Other": lambda d: f"https://www.google.com/search?q={urllib.parse.quote(d + ' courier tracking')}"
}

WEBAPP_URL = st.secrets.get("webapp_url", "")

if not WEBAPP_URL:
    st.error("⚠️ Please add `webapp_url` in your Streamlit Cloud Secrets to connect to Google Sheets.")
    st.stop()

@st.cache_data(ttl=15, show_spinner=False)
def fetch_consignments() -> pd.DataFrame:
    response = requests.get(WEBAPP_URL, timeout=15)
    response.raise_for_status()
    data = response.json()
    if not data:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.DataFrame(data)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df.astype(str)

def post_to_sheet(payload: dict):
    response = requests.post(WEBAPP_URL, json=payload, timeout=15)
    response.raise_for_status()
    fetch_consignments.clear()
    return response.json()

def resolve_tracking_link(courier: str, docket: str, custom_link: str) -> str:
    if custom_link and custom_link.strip():
        link = custom_link.strip()
        return link if link.startswith(("http://", "https://")) else f"https://{link}"
    builder = COURIER_URLS.get(courier, COURIER_URLS["Other"])
    return builder(docket.strip())

def parse_clean_date(date_str: str):
    """Safely extracts YYYY-MM-DD from Google Sheets date strings."""
    if not date_str or str(date_str).strip() == "":
        return None
    clean = str(date_str).strip()[:10]
    try:
        return datetime.strptime(clean, "%Y-%m-%d").date()
    except ValueError:
        return None

def evaluate_sla(expected_str: str, current_status: str):
    """Returns (is_overdue, days_diff, clean_expected_str, is_delivered)"""
    is_delivered = "delivered" in str(current_status).lower()
    exp_date = parse_clean_date(expected_str)
    if not exp_date:
        return False, 0, str(expected_str)[:10], is_delivered
    days_diff = (date.today() - exp_date).days
    is_overdue = (days_diff > 0) and (not is_delivered)
    return is_overdue, days_diff, exp_date.strftime("%Y-%m-%d"), is_delivered

# --- Load Data ---
try:
    df = fetch_consignments()
except Exception as e:
    st.error(f"Failed to connect to Google Sheet Web App: {e}")
    st.stop()

# Enrich DataFrame with SLA / Overdue calculations
if not df.empty:
    sla_results = df.apply(
        lambda r: evaluate_sla(r["expected_date"], r["current_status"]),
        axis=1
    )
    df["is_overdue"] = [res[0] for res in sla_results]
    df["days_overdue"] = [res[1] for res in sla_results]
    df["clean_expected"] = [res[2] for res in sla_results]
    df["is_delivered"] = [res[3] for res in sla_results]
    df["clean_dispatch"] = df["dispatch_date"].apply(lambda x: str(x)[:10])
else:
    df["is_overdue"] = []
    df["days_overdue"] = []
    df["clean_expected"] = []
    df["is_delivered"] = []
    df["clean_dispatch"] = []

# --- Clean Top Header Banner ---
st.markdown("""
<div class="hero-banner">
    <div>
        <h1 class="hero-title">📦 Consignment Command Center</h1>
        <p class="hero-subtitle">Inward & Outward Courier Dispatch Register • Color-Coded & SLA Monitored</p>
    </div>
    <div class="sync-pill">● Google Sheets Live Sync</div>
</div>
""", unsafe_allow_html=True)

# --- KPI Summary Bar (6 Engaging Cards) ---
total_count = len(df)
inward_count = int((df["direction"] == "Inward").sum()) if not df.empty else 0
outward_count = int((df["direction"] == "Outward").sum()) if not df.empty else 0
overdue_count = int(df["is_overdue"].sum()) if not df.empty else 0
delivered_count = int(df["is_delivered"].sum()) if not df.empty else 0
active_count = total_count - delivered_count

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.markdown(f"""
    <div class="kpi-card kpi-all">
        <div class="kpi-label" style="color:#818cf8;">Total Tracked</div>
        <div class="kpi-value">{total_count}</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi-card kpi-inward">
        <div class="kpi-label" style="color:#22d3ee;">📥 Inward (Recv)</div>
        <div class="kpi-value">{inward_count}</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class="kpi-card kpi-outward">
        <div class="kpi-label" style="color:#fbbf24;">📤 Outward (Sent)</div>
        <div class="kpi-value">{outward_count}</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""
    <div class="kpi-card kpi-transit">
        <div class="kpi-label" style="color:#60a5fa;">🚚 In Transit</div>
        <div class="kpi-value">{active_count}</div>
    </div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""
    <div class="kpi-card kpi-overdue">
        <div class="kpi-label" style="color:#fb7185;">⚠️ Overdue SLA</div>
        <div class="kpi-value" style="color:#fda4af;">{overdue_count}</div>
    </div>""", unsafe_allow_html=True)
with k6:
    st.markdown(f"""
    <div class="kpi-card kpi-delivered">
        <div class="kpi-label" style="color:#34d399;">✅ Delivered</div>
        <div class="kpi-value">{delivered_count}</div>
    </div>""", unsafe_allow_html=True)

# --- Overdue Alert Banner (Shown automatically when any order is past expected delivery date) ---
if overdue_count > 0:
    st.markdown(f"""
    <div class="overdue-alert-banner">
        <strong>🚨 SLA Breach Alert:</strong> <b>{overdue_count} consignment(s)</b> have passed their Expected Delivery Date and are not yet marked as Delivered. Overdue rows are highlighted in crimson below.
    </div>
    """, unsafe_allow_html=True)

st.write("")

# --- 10-Field Consignment Input Form ---
with st.container(border=True):
    st.markdown("#### 📝 Register New Consignment")
    with st.form("consignment_entry_form", clear_on_submit=True):
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            direction = st.selectbox("1. Inward / Outward *", ["Inward", "Outward"])
            location = st.text_input("6. Location (Route) *", placeholder="e.g., Pune -> Lucknow")

        with col2:
            item_name = st.text_input("2. Item / Consignment Name *", placeholder="e.g., Telemetry Modules")
            dispatch_date = st.date_input("7. Date of Dispatch *", value=date.today())

        with col3:
            vendor_name = st.text_input("3. Vendor Name *", placeholder="e.g., Robu.in")
            expected_date = st.date_input("8. Expected Delivery Date *", value=date.today())

        with col4:
            courier_service = st.selectbox("4. Courier Service *", list(COURIER_URLS.keys()))
            tracking_link = st.text_input("9. Tracking Link (Optional)", placeholder="Paste link or leave blank")

        with col5:
            docket_number = st.text_input("5. Docket / AWB Number *", placeholder="e.g., 78491024812")
            current_status = st.text_input("10. Current Status (Manual) *", value="Dispatched")

        submitted = st.form_submit_button("➕ Save Consignment to Google Sheets", type="primary", use_container_width=True)

        if submitted:
            if not item_name.strip() or not docket_number.strip():
                st.warning("Please enter both the Item / Consignment Name and the Docket Number.")
            else:
                record = {
                    "id": f"c-{uuid.uuid4().hex[:8]}",
                    "direction": direction,
                    "item_name": item_name.strip(),
                    "vendor_name": vendor_name.strip(),
                    "courier_service": courier_service,
                    "docket_number": docket_number.strip(),
                    "location": location.strip(),
                    "dispatch_date": str(dispatch_date),
                    "expected_date": str(expected_date),
                    "tracking_link": tracking_link.strip(),
                    "current_status": current_status.strip()
                }
                with st.spinner("Saving consignment to Google Sheets..."):
                    post_to_sheet({"action": "add", "data": record})
                st.toast(f"Saved {item_name} to Google Sheets!")
                st.rerun()

# --- Search & Color-Coded Filter Bar ---
f_col1, f_col2 = st.columns([2.6, 2.4])
with f_col1:
    search_query = st.text_input(
        "🔍 Search Consignments",
        placeholder="Search by item name, vendor, docket #, courier, route, or status..."
    )
with f_col2:
    view_filter = st.selectbox(
        "Filter View",
        [
            "All Consignments",
            "📥 Inward Only (Cyan)",
            "📤 Outward Only (Amber)",
            "⚠️ Overdue / Delayed Only (Crimson)",
            "🚚 In Transit / Pending",
            "✅ Delivered Only"
        ]
    )

filtered_df = df.copy()
if not filtered_df.empty:
    if view_filter.startswith("📥"):
        filtered_df = filtered_df[filtered_df["direction"] == "Inward"]
    elif view_filter.startswith("📤"):
        filtered_df = filtered_df[filtered_df["direction"] == "Outward"]
    elif view_filter.startswith("⚠️"):
        filtered_df = filtered_df[filtered_df["is_overdue"] == True]
    elif view_filter.startswith("🚚"):
        filtered_df = filtered_df[filtered_df["is_delivered"] == False]
    elif view_filter.startswith("✅"):
        filtered_df = filtered_df[filtered_df["is_delivered"] == True]

    if search_query.strip():
        q = search_query.strip().lower()
        mask = filtered_df.apply(
            lambda r: q in f"{r['item_name']} {r['vendor_name']} {r['courier_service']} {r['docket_number']} {r['location']} {r['current_status']}".lower(),
            axis=1
        )
        filtered_df = filtered_df[mask]

# Legend + Count Header
st.markdown(f"""
<div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; margin: 12px 0 10px 0;">
    <div style="font-size:1.15rem; font-weight:700; color:#f8fafc;">
        Live Consignment Feed ({len(filtered_df)})
    </div>
    <div style="display:flex; gap:10px; align-items:center; font-size:0.75rem;">
        <span class="badge-inward">📥 Cyan = Inward</span>
        <span class="badge-outward">📤 Amber = Outward</span>
        <span class="badge-overdue">⚠️ Crimson Glow = Overdue Past Expected Date</span>
    </div>
</div>
""", unsafe_allow_html=True)

if filtered_df.empty:
    st.info("No consignments match your current filter.")
else:
    # Render newest records first
    for _, row in filtered_df.iloc[::-1].iterrows():
        is_inward = row["direction"] == "Inward"
        is_overdue = bool(row["is_overdue"])
        days_overdue = int(row["days_overdue"])
        is_delivered = bool(row["is_delivered"])

        # CSS Marker class determines the entire row container's color scheme
        if is_overdue:
            row_theme_class = "row-overdue"
        elif is_inward:
            row_theme_class = "row-inward"
        else:
            row_theme_class = "row-outward"

        # Direction Badge HTML
        dir_badge_html = (
            '<span class="badge-inward">📥 INWARD (RECEIVING)</span>'
            if is_inward
            else '<span class="badge-outward">📤 OUTWARD (DISPATCHED)</span>'
        )

        # SLA / Delivery Status Badge HTML
        if is_overdue:
            sla_badge_html = f'<span class="badge-overdue">⚠️ OVERDUE BY {days_overdue} DAY{"S" if days_overdue != 1 else ""}</span>'
        elif is_delivered:
            sla_badge_html = '<span class="badge-delivered">✅ DELIVERED</span>'
        elif days_overdue == 0 and not is_delivered:
            sla_badge_html = '<span class="badge-due-today">⏰ DUE TODAY</span>'
        else:
            days_left = abs(days_overdue)
            sla_badge_html = f'<span style="color:#94a3b8; font-size:0.75rem; font-weight:600;">⏳ {days_left} day{"s" if days_left != 1 else ""} remaining</span>'

        with st.container(border=True):
            # Inject the hidden CSS hook + rich header strip for this row
            st.markdown(f"""
            <div class="{row_theme_class}" style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:8px; padding-bottom:8px; margin-bottom:8px; border-bottom:1px solid rgba(148,163,184,0.15);">
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                    {dir_badge_html}
                    <span class="badge-courier">🚚 {row['courier_service']}</span>
                    <span style="font-size:1.05rem; font-weight:700; color:#ffffff; margin-left:4px;">{row['item_name']}</span>
                </div>
                <div>
                    {sla_badge_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_details, c_route, c_status, c_actions = st.columns([2.8, 2.5, 2.7, 2.0])

            with c_details:
                st.markdown(f"🏢 **Vendor:** {row['vendor_name']}")
                st.caption("Docket / AWB Number (Click copy icon on right):")
                st.code(row["docket_number"], language=None)

            with c_route:
                st.markdown(f"📍 **Route:** `{row['location']}`")
                st.markdown(f"📅 **Dispatched:** {row['clean_dispatch']}")
                if is_overdue:
                    st.markdown(
                        f"🎯 **Expected:** <span style='color:#fda4af; font-weight:800; text-decoration:underline;'>{row['clean_expected']} (PAST DUE)</span>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"🎯 **Expected:** {row['clean_expected']}")

            with c_status:
                new_status = st.text_input(
                    "Current Status (Manual)",
                    value=row["current_status"],
                    key=f"status_{row['id']}"
                )
                if st.button("💾 Save Manual Status", key=f"save_{row['id']}", use_container_width=True):
                    with st.spinner("Updating status in Google Sheets..."):
                        post_to_sheet({
                            "action": "update_status",
                            "id": row["id"],
                            "current_status": new_status.strip()
                        })
                    st.toast(f"Status updated for Docket #{row['docket_number']}")
                    st.rerun()

            with c_actions:
                st.write("")
                tracking_url = resolve_tracking_link(
                    row["courier_service"],
                    row["docket_number"],
                    row["tracking_link"]
                )
                st.link_button(
                    f"🚀 Track on {row['courier_service']} ↗",
                    url=tracking_url,
                    use_container_width=True,
                    help=f"Opens {row['courier_service']} tracking website in a new tab"
                )
                if st.button("🗑️ Delete Record", key=f"del_{row['id']}", use_container_width=True):
                    with st.spinner("Deleting from Google Sheets..."):
                        post_to_sheet({
                            "action": "delete",
                            "id": row["id"]
                        })
                    st.toast(f"Deleted {row['item_name']}")
                    st.rerun()
