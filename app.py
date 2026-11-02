import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import urllib.parse
import uuid

st.set_page_config(
    page_title="Consignment & Courier Tracker",
    page_icon="📦",
    layout="wide"
)

# Expected columns in Google Sheet
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

# Official Courier Tracking Websites (Fallback if Tracking Link is left blank)
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

@st.cache_resource
def get_worksheet():
    """Connects to Google Sheets using Streamlit Secrets and ensures headers exist."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet_url = st.secrets["sheet_url"]
    sh = client.open_by_url(sheet_url)
    ws = sh.get_worksheet(0)

    # Auto-create header row if the Google Sheet is empty
    existing_headers = ws.row_values(1)
    if existing_headers != COLUMNS:
        if not existing_headers:
            ws.append_row(COLUMNS)
        else:
            ws.update(range_name="A1:K1", values=[COLUMNS])
    return ws

def load_data(ws) -> pd.DataFrame:
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.DataFrame(records)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df.astype(str)

def resolve_tracking_link(courier: str, docket: str, custom_link: str) -> str:
    """Uses the user's custom tracking link if provided; otherwise opens the courier's tracking portal."""
    if custom_link and custom_link.strip():
        link = custom_link.strip()
        return link if link.startswith(("http://", "https://")) else f"https://{link}"
    builder = COURIER_URLS.get(courier, COURIER_URLS["Other"])
    return builder(docket.strip())

# --- Connect to Google Sheet ---
try:
    worksheet = get_worksheet()
    df = load_data(worksheet)
except Exception as e:
    st.error("⚠️ Google Sheets connection not configured yet. Please check your Streamlit Secrets setup.")
    st.stop()

# --- Clean Header ---
st.title("📦 Consignment Command Center")
st.caption("Live Inward & Outward Courier Register — Backed by Google Sheets")

# --- KPI Summary Bar ---
total_count = len(df)
inward_count = len(df[df["direction"] == "Inward"]) if not df.empty else 0
outward_count = len(df[df["direction"] == "Outward"]) if not df.empty else 0
delivered_count = len(df[df["current_status"].str.lower().str.contains("delivered", na=False)]) if not df.empty else 0
active_count = total_count - delivered_count

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Consignments", total_count)
k2.metric("📥 Inward (Sent to Us)", inward_count)
k3.metric("📤 Outward (Dispatched)", outward_count)
k4.metric("🚚 In Transit / Pending", active_count)
k5.metric("✅ Delivered", delivered_count)

# --- 10-Field Consignment Input Form ---
with st.container(border=True):
    st.subheader("Register Consignment")
    with st.form("consignment_entry_form", clear_on_submit=True):
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            direction = st.selectbox("1. Inward / Outward *", ["Inward", "Outward"])
            location = st.text_input("6. Location (Route) *", placeholder="e.g., Pune to Lucknow")

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

        submitted = st.form_submit_button("➕ Save Consignment to Google Sheets", type="primary")

        if submitted:
            if not item_name.strip() or not docket_number.strip():
                st.warning("Please enter both the Item / Consignment Name and the Docket Number.")
            else:
                new_row = [
                    f"c-{uuid.uuid4().hex[:8]}",
                    direction,
                    item_name.strip(),
                    vendor_name.strip(),
                    courier_service,
                    docket_number.strip(),
                    location.strip(),
                    str(dispatch_date),
                    str(expected_date),
                    tracking_link.strip(),
                    current_status.strip()
                ]
                worksheet.append_row(new_row, value_input_option="USER_ENTERED")
                st.toast(f"Saved {item_name} to Google Sheets!")
                st.rerun()

# --- Search & Filter Controls ---
f_col1, f_col2 = st.columns([3, 1])
with f_col1:
    search_query = st.text_input(
        "🔍 Search Consignments",
        placeholder="Filter by item name, vendor, docket number, courier, location, or status..."
    )
with f_col2:
    direction_filter = st.selectbox("Filter Movement", ["All", "Inward", "Outward", "In Transit Only", "Delivered Only"])

filtered_df = df.copy()
if not filtered_df.empty:
    if direction_filter == "Inward":
        filtered_df = filtered_df[filtered_df["direction"] == "Inward"]
    elif direction_filter == "Outward":
        filtered_df = filtered_df[filtered_df["direction"] == "Outward"]
    elif direction_filter == "In Transit Only":
        filtered_df = filtered_df[~filtered_df["current_status"].str.lower().str.contains("delivered", na=False)]
    elif direction_filter == "Delivered Only":
        filtered_df = filtered_df[filtered_df["current_status"].str.lower().str.contains("delivered", na=False)]

    if search_query.strip():
        q = search_query.strip().lower()
        mask = filtered_df.apply(lambda r: q in " ".join(r.values).lower(), axis=1)
        filtered_df = filtered_df[mask]

st.subheader(f"Consignment Register ({len(filtered_df)})")

if filtered_df.empty:
    st.info("No consignments match your current view.")
else:
    # Show newest entries at the top
    for idx, row in filtered_df.iloc[::-1].iterrows():
        sheet_row_number = idx + 2  # Row 1 is headers, DataFrame index starts at 0

        with st.container(border=True):
            c_details, c_route, c_status, c_actions = st.columns([3, 2.3, 2.7, 2.2])

            with c_details:
                badge = "📥 **INWARD**" if row["direction"] == "Inward" else "📤 **OUTWARD**"
                st.markdown(f"{badge} &nbsp;|&nbsp; **{row['item_name']}**")
                st.caption(f"🏢 Vendor: **{row['vendor_name']}** &nbsp;•&nbsp; 🚚 Courier: **{row['courier_service']}**")
                # st.code gives a one-click Copy button for pasting the Docket # on the courier site
                st.code(row["docket_number"], language=None)

            with c_route:
                st.markdown(f"📍 **Location:** {row['location']}")
                st.caption(f"📅 Dispatched: **{row['dispatch_date']}**")
                st.caption(f"🎯 Expected: **{row['expected_date']}**")

            with c_status:
                new_status = st.text_input(
                    "Manual Current Status",
                    value=row["current_status"],
                    key=f"status_{row['id']}"
                )
                if st.button("💾 Save Status", key=f"save_{row['id']}", use_container_width=True):
                    # Column K (11) is current_status
                    worksheet.update_cell(sheet_row_number, 11, new_status.strip())
                    st.toast(f"Status updated for Docket #{row['docket_number']}")
                    st.rerun()

            with c_actions:
                st.write("")  # Vertical alignment spacer
                tracking_url = resolve_tracking_link(
                    row["courier_service"],
                    row["docket_number"],
                    row["tracking_link"]
                )
                # Direct button to open the Courier Website
                st.link_button(
                    f"🚀 Track on {row['courier_service']} ↗",
                    url=tracking_url,
                    use_container_width=True,
                    help=f"Opens {row['courier_service']} tracking page in a new tab"
                )
                if st.button("🗑️ Delete Item", key=f"del_{row['id']}", use_container_width=True):
                    worksheet.delete_rows(sheet_row_number)
                    st.toast(f"Deleted {row['item_name']}")
                    st.rerun()
