import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime
import urllib.parse
import uuid

st.set_page_config(
    page_title="Logistic Command Center",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Colorful Light Mode UI Styling ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #f0f4ff 0%, #f8fafc 40%, #ffffff 100%);
        color: #0f172a;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Colorful Top Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, #4f46e5 0%, #0ea5e9 100%);
        border-radius: 16px;
        padding: 18px 24px;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: #ffffff;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.3);
    }
    .hero-title {
        font-size: 1.5rem;
        font-weight: 800;
        margin: 0;
        color: #ffffff !important;
    }
    .hero-subtitle {
        font-size: 0.85rem;
        color: #e0f2fe;
        margin-top: 2px;
    }
    .sync-pill {
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.45);
        color: #ffffff;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 999px;
    }

    /* Colorful Light KPI Cards */
    .kpi-card {
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
        border: 1px solid rgba(15, 23, 42, 0.08);
    }
    .kpi-label {
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .kpi-all { background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%); border-left: 5px solid #4f46e5; color: #312e81; }
    .kpi-inward { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-left: 5px solid #0284c7; color: #0c4a6e; }
    .kpi-outward { background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border-left: 5px solid #d97706; color: #78350f; }
    .kpi-transit { background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-left: 5px solid #2563eb; color: #1e3a8a; }
    .kpi-overdue { background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%); border-left: 5px solid #e11d48; color: #881337; }
    .kpi-delivered { background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-left: 5px solid #059669; color: #064e3b; }

    /* Overdue Alert Strip */
    .overdue-strip {
        background: #fff1f2;
        border: 1px solid #fecdd3;
        border-left: 6px solid #e11d48;
        color: #9f1239;
        padding: 10px 16px;
        border-radius: 10px;
        font-size: 0.88rem;
        margin: 12px 0;
        font-weight: 600;
    }

    /* Legend Pills */
    .legend-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-right: 6px;
    }
    .pill-inward { background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; }
    .pill-outward { background: #fef3c7; color: #b45309; border: 1px solid #fcd34d; }
    .pill-overdue { background: #ffe4e6; color: #be123c; border: 1px solid #fda4af; }
    .pill-delivered { background: #d1fae5; color: #047857; border: 1px solid #6ee7b7; }
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
    "delivery_date",
    "tracking_link",
    "current_status",
    "is_deleted"
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

STATUS_OPTIONS = [
    "Dispatched",
    "In Transit",
    "Reached Local Hub",
    "Out for Delivery",
    "Delivered",
    "Delayed / Exception"
]

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
    if custom_link and str(custom_link).strip():
        link = str(custom_link).strip()
        return link if link.startswith(("http://", "https://")) else f"https://{link}"
    builder = COURIER_URLS.get(courier, COURIER_URLS["Other"])
    return builder(str(docket).strip())

def parse_clean_date(date_str: str):
    if not date_str or str(date_str).strip() in ("", "None", "nan"):
        return None
    clean = str(date_str).strip()[:10]
    try:
        return datetime.strptime(clean, "%Y-%m-%d").date()
    except ValueError:
        return None

def evaluate_row(row):
    status_str = str(row.get("current_status", "")).lower()
    deliv_str = str(row.get("delivery_date", "")).strip()[:10]
    is_delivered = ("delivered" in status_str) or bool(parse_clean_date(deliv_str))
    exp_date = parse_clean_date(row.get("expected_date", ""))
    if not exp_date:
        return False, 0, is_delivered
    days_diff = (date.today() - exp_date).days
    is_overdue = (days_diff > 0) and (not is_delivered)
    return is_overdue, days_diff, is_delivered

# --- Load & Filter Active (Non-Deleted) Consignments ---
try:
    raw_df = fetch_consignments()
except Exception as e:
    st.error(f"Failed to connect to Google Sheet Web App: {e}")
    st.stop()

# Filter out rows that were soft-deleted on the frontend (they remain in Google Sheets)
if not raw_df.empty:
    df = raw_df[~raw_df["is_deleted"].str.strip().str.upper().isin(["TRUE", "1", "YES"])].copy()
else:
    df = pd.DataFrame(columns=COLUMNS)

if not df.empty:
    eval_res = df.apply(evaluate_row, axis=1)
    df["is_overdue"] = [r[0] for r in eval_res]
    df["days_overdue"] = [r[1] for r in eval_res]
    df["is_delivered"] = [r[2] for r in eval_res]
    df["clean_dispatch"] = df["dispatch_date"].apply(lambda x: str(x).strip()[:10])
    df["clean_expected"] = df["expected_date"].apply(lambda x: str(x).strip()[:10])
    df["clean_delivery"] = df["delivery_date"].apply(
        lambda x: str(x).strip()[:10] if str(x).strip() not in ("", "None", "nan") else "—"
    )
    df["resolved_url"] = df.apply(
        lambda r: resolve_tracking_link(r["courier_service"], r["docket_number"], r["tracking_link"]),
        axis=1
    )
    df["sla_tag"] = df.apply(
        lambda r: f"⚠️ Overdue ({r['days_overdue']}d)" if r["is_overdue"]
        else ("✅ Delivered" if r["is_delivered"] else "🚚 On Schedule"),
        axis=1
    )

# --- Top Banner ---
st.markdown("""
<div class="hero-banner">
    <div>
        <h1 class="hero-title">Logistic Command Center</h1>
    </div>
    <div class="sync-pill">● Connected to Google Sheets</div>
</div>
""", unsafe_allow_html=True)

# --- KPI Cards ---
total_count = len(df)
inward_count = int((df["direction"] == "Inward").sum()) if not df.empty else 0
outward_count = int((df["direction"] == "Outward").sum()) if not df.empty else 0
overdue_count = int(df["is_overdue"].sum()) if not df.empty else 0
delivered_count = int(df["is_delivered"].sum()) if not df.empty else 0
active_count = total_count - delivered_count

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.markdown(f'<div class="kpi-card kpi-all"><div class="kpi-label">Total Active</div><div class="kpi-value">{total_count}</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card kpi-inward"><div class="kpi-label">📥 Inward (Recv)</div><div class="kpi-value">{inward_count}</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card kpi-outward"><div class="kpi-label">📤 Outward (Sent)</div><div class="kpi-value">{outward_count}</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card kpi-transit"><div class="kpi-label">🚚 In Transit</div><div class="kpi-value">{active_count}</div></div>', unsafe_allow_html=True)
with k5:
    st.markdown(f'<div class="kpi-card kpi-overdue"><div class="kpi-label">⚠️ Overdue</div><div class="kpi-value">{overdue_count}</div></div>', unsafe_allow_html=True)
with k6:
    st.markdown(f'<div class="kpi-card kpi-delivered"><div class="kpi-label">✅ Delivered</div><div class="kpi-value">{delivered_count}</div></div>', unsafe_allow_html=True)

if overdue_count > 0:
    st.markdown(
        f'<div class="overdue-strip">🚨 <b>{overdue_count} consignment(s)</b> are past their Expected Delivery Date and are highlighted in <b>Rose Red</b> in the table below.</div>',
        unsafe_allow_html=True
    )

st.write("")

# --- Collapsible Add New Consignment Form (Keeps Table Front-and-Center) ---
with st.expander("➕ Register New Consignment (Click to Expand / Collapse)", expanded=(total_count == 0)):
    with st.form("add_consignment_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            direction = st.selectbox("1. Movement Type *", ["Inward", "Outward"])
            item_name = st.text_input("2. Item / Consignment Name *", placeholder="e.g., Telemetry Modules")
            vendor_name = st.text_input("3. Vendor / Recipient Name *", placeholder="e.g., Robu.in")
        with c2:
            courier_service = st.selectbox("4. Courier Service *", list(COURIER_URLS.keys()))
            docket_number = st.text_input("5. Docket / AWB Number *", placeholder="e.g., 78491024812")
            location = st.text_input("6. Location (Route) *", placeholder="e.g., Pune -> Lucknow")
        with c3:
            dispatch_date = st.date_input("7. Date of Dispatch *", value=date.today())
            expected_date = st.date_input("8. Expected Delivery Date *", value=date.today())
            has_deliv = st.checkbox("Already Delivered? (Set Delivery Date)")
        with c4:
            delivery_date_val = st.date_input("9. Actual Delivery Date (If Delivered)", value=date.today())
            tracking_link = st.text_input("10. Tracking Link (Optional)", placeholder="Leave blank for auto courier link")
            current_status = st.text_input("11. Current Status (Manual) *", value="Dispatched")

        submitted = st.form_submit_button("✅ Save Consignment to Google Sheets", type="primary", use_container_width=True)
        if submitted:
            if not item_name.strip() or not docket_number.strip():
                st.warning("Please enter both Item Name and Docket Number.")
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
                    "delivery_date": str(delivery_date_val) if has_deliv else "",
                    "tracking_link": tracking_link.strip(),
                    "current_status": "Delivered" if has_deliv and current_status == "Dispatched" else current_status.strip(),
                    "is_deleted": "FALSE"
                }
                with st.spinner("Saving to Google Sheets..."):
                    post_to_sheet({"action": "add", "data": record})
                st.toast(f"Added {item_name}!")
                st.rerun()

# --- Search & Filter Controls ---
f1, f2 = st.columns([3, 1.5])
with f1:
    search_query = st.text_input("🔍 Quick Search Table", placeholder="Type item, vendor, docket #, courier, location, or status...")
with f2:
    view_filter = st.selectbox(
        "Filter Rows",
        [
            "All Active Consignments",
            "📥 Inward Only (Sky Blue)",
            "📤 Outward Only (Warm Amber)",
            "⚠️ Overdue Only (Rose Red)",
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

    # Show newest entries at top of table
    filtered_df = filtered_df.iloc[::-1].reset_index(drop=True)

# --- Compact Color-Coded Tabular View ---
st.markdown("""
<div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; margin: 6px 0 8px 0;">
    <div style="font-size:1.1rem; font-weight:800; color:#1e293b;">
        📋 Consignment Tracking Table <span style="font-size:0.82rem; font-weight:500; color:#64748b;">(Click any row's checkbox on the left to Edit Details, Add Delivery Date, or Hide)</span>
    </div>
    <div>
        <span class="legend-pill pill-inward">📥 Inward Row</span>
        <span class="legend-pill pill-outward">📤 Outward Row</span>
        <span class="legend-pill pill-overdue">⚠️ Overdue (Past Expected Date)</span>
    </div>
</div>
""", unsafe_allow_html=True)

if filtered_df.empty:
    st.info("No consignments match your current filter.")
else:
    display_cols = [
        "direction",
        "item_name",
        "vendor_name",
        "courier_service",
        "docket_number",
        "location",
        "clean_dispatch",
        "clean_expected",
        "clean_delivery",
        "current_status",
        "sla_tag",
        "resolved_url"
    ]
    table_df = filtered_df[display_cols].copy()

    # Color-code each row based on Overdue vs Inward vs Outward
    def style_table_rows(row_series):
        idx = row_series.name
        is_ovd = bool(filtered_df.loc[idx, "is_overdue"])
        direction_val = filtered_df.loc[idx, "direction"]

        if is_ovd:
            # Rose Red highlight for overdue orders
            return ["background-color: #ffe4e6; color: #9f1239; font-weight: 600;"] * len(row_series)
        elif direction_val == "Inward":
            # Soft Sky Cyan for Inward
            return ["background-color: #e0f2fe; color: #0c4a6e;"] * len(row_series)
        else:
            # Soft Warm Amber for Outward
            return ["background-color: #fef3c7; color: #78350f;"] * len(row_series)

    styled_table = table_df.style.apply(style_table_rows, axis=1)

    selection_event = st.dataframe(
        styled_table,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "direction": st.column_config.TextColumn("Type", width="small"),
            "item_name": st.column_config.TextColumn("Item / Consignment", width="medium"),
            "vendor_name": st.column_config.TextColumn("Vendor", width="medium"),
            "courier_service": st.column_config.TextColumn("Courier", width="small"),
            "docket_number": st.column_config.TextColumn("Docket #", width="small"),
            "location": st.column_config.TextColumn("Location", width="small"),
            "clean_dispatch": st.column_config.TextColumn("Dispatched", width="small"),
            "clean_expected": st.column_config.TextColumn("Expected", width="small"),
            "clean_delivery": st.column_config.TextColumn("Delivered On", width="small"),
            "current_status": st.column_config.TextColumn("Current Status", width="medium"),
            "sla_tag": st.column_config.TextColumn("SLA State", width="small"),
            "resolved_url": st.column_config.LinkColumn(
                "Track Portal",
                display_text="🚀 Track ↗",
                width="small"
            )
        }
    )

    # --- Edit / Add Delivery Date / Soft-Delete Panel ---
    st.markdown("---")
    st.markdown("#### ✏️ Edit Consignment Details, Add Delivery Date, or Remove from View")

    # Determine which item is selected (via table click or dropdown selector)
    selected_rows = selection_event.selection.rows if selection_event and selection_event.selection else []
    options_map = {
        f"[{r['direction']}] {r['item_name']} — Docket #{r['docket_number']} ({r['courier_service']})": idx
        for idx, r in filtered_df.iterrows()
    }
    option_labels = list(options_map.keys())
    default_idx = selected_rows[0] if selected_rows else 0

    chosen_label = st.selectbox(
        "Selected Consignment (Click a row in the table above or pick from this list):",
        options=option_labels,
        index=default_idx
    )
    selected_row = filtered_df.loc[options_map[chosen_label]]

    with st.container(border=True):
        top_bar_col1, top_bar_col2, top_bar_col3 = st.columns([2.5, 1.5, 1.2])
        with top_bar_col1:
            st.markdown(f"**Editing:** `{selected_row['item_name']}` &nbsp;|&nbsp; **Docket #:** `{selected_row['docket_number']}`")
        with top_bar_col2:
            st.link_button(
                f"🚀 Open {selected_row['courier_service']} Tracking Page ↗",
                url=selected_row["resolved_url"],
                use_container_width=True
            )
        with top_bar_col3:
            if st.button("🗑️ Remove from List (Keep in Sheet)", key=f"soft_del_{selected_row['id']}", use_container_width=True):
                with st.spinner("Hiding from frontend (keeping record in Google Sheets)..."):
                    post_to_sheet({"action": "soft_delete", "id": selected_row["id"]})
                st.toast(f"Removed '{selected_row['item_name']}' from view (data preserved in Google Sheet).")
                st.rerun()

        with st.form(key=f"edit_form_{selected_row['id']}"):
            e1, e2, e3, e4 = st.columns(4)

            with e1:
                edit_direction = st.selectbox(
                    "Inward / Outward",
                    ["Inward", "Outward"],
                    index=0 if selected_row["direction"] == "Inward" else 1
                )
                edit_item = st.text_input("Item / Consignment Name", value=selected_row["item_name"])
                edit_vendor = st.text_input("Vendor Name", value=selected_row["vendor_name"])

            with e2:
                courier_list = list(COURIER_URLS.keys())
                c_idx = courier_list.index(selected_row["courier_service"]) if selected_row["courier_service"] in courier_list else 0
                edit_courier = st.selectbox("Courier Service", courier_list, index=c_idx)
                edit_docket = st.text_input("Docket / AWB Number", value=selected_row["docket_number"])
                edit_location = st.text_input("Location (Route)", value=selected_row["location"])

            with e3:
                disp_dt = parse_clean_date(selected_row["dispatch_date"]) or date.today()
                exp_dt = parse_clean_date(selected_row["expected_date"]) or date.today()
                existing_deliv_dt = parse_clean_date(selected_row["delivery_date"])

                edit_dispatch = st.date_input("Date of Dispatch", value=disp_dt)
                edit_expected = st.date_input("Expected Delivery Date", value=exp_dt)
                record_delivery = st.checkbox(
                    "✅ Record / Update Actual Delivery Date",
                    value=(existing_deliv_dt is not None)
                )

            with e4:
                edit_delivery_date = st.date_input(
                    "Actual Delivery Date",
                    value=existing_deliv_dt or date.today()
                )
                edit_link = st.text_input("Tracking Link", value=selected_row["tracking_link"])
                edit_status = st.text_input(
                    "Current Status (Manual)",
                    value=selected_row["current_status"],
                    help="Tip: Setting a Delivery Date or typing 'Delivered' marks this shipment as completed."
                )

            save_changes = st.form_submit_button("💾 Save Updated Details to Google Sheets", type="primary", use_container_width=True)
            if save_changes:
                final_status = edit_status.strip()
                if record_delivery and "delivered" not in final_status.lower():
                    final_status = f"Delivered ({edit_delivery_date})"

                updated_data = {
                    "id": selected_row["id"],
                    "direction": edit_direction,
                    "item_name": edit_item.strip(),
                    "vendor_name": edit_vendor.strip(),
                    "courier_service": edit_courier,
                    "docket_number": edit_docket.strip(),
                    "location": edit_location.strip(),
                    "dispatch_date": str(edit_dispatch),
                    "expected_date": str(edit_expected),
                    "delivery_date": str(edit_delivery_date) if record_delivery else "",
                    "tracking_link": edit_link.strip(),
                    "current_status": final_status,
                    "is_deleted": "FALSE"
                }
                with st.spinner("Updating record in Google Sheets..."):
                    post_to_sheet({
                        "action": "edit",
                        "id": selected_row["id"],
                        "data": updated_data
                    })
                st.toast(f"Updated '{edit_item}' in Google Sheets!")
                st.rerun()
