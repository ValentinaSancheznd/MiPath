import streamlit as st
import pandas as pd

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="MiPath",
    page_icon="🎨",
    layout="wide"
)

# ═══════════════════════════════════════════════════════════════════════════
# BRAND STYLING — dark green / black, matching the PPT template
# NOTE: placeholder hex values pulled from the cluster chart color_map.
# Swap these for your exact PPT hex codes if they differ.
# ═══════════════════════════════════════════════════════════════════════════
DARK_GREEN = "#3B5C2A"
MID_GREEN = "#6B9E4E"
LIGHT_GREEN = "#B8D4A0"
NEAR_BLACK = "#1A1A1A"
CREAM_BG = "#FAF6ED"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {CREAM_BG};
    }}
    h1, h2, h3 {{
        color: {DARK_GREEN} !important;
        font-family: Georgia, 'Times New Roman', serif;
    }}
    .stButton>button, .stSelectbox label, .stMultiselect label {{
        color: {NEAR_BLACK};
    }}
    div[data-testid="stMetricValue"] {{
        color: {DARK_GREEN};
    }}
    div[data-testid="stMetricLabel"] {{
        color: {NEAR_BLACK};
    }}
    .stDataFrame {{
        border: 1px solid {LIGHT_GREEN};
    }}
    hr {{
        border-color: {LIGHT_GREEN};
    }}
    div[data-testid="stExpander"] {{
        border: 1px solid {LIGHT_GREEN};
        border-radius: 6px;
    }}
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# LOAD DATA
# Both files come straight from the Colab pipeline (build_arts_market_data).
# No cleaning happens here — this app only reads, filters, and displays.
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    state_summary = pd.read_csv("state_summary.csv")
    field_state_summary = pd.read_csv("field_state_summary.csv")
    return state_summary, field_state_summary

state_summary, field_state_summary = load_data()

# ═══════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════
st.title("🎨 MiPath")
st.write(
    "A data-driven look at cost, debt, earnings, and job opportunity "
    "for visual and performing arts programs across the U.S."
)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: FIELD SELECTION (required)
# ═══════════════════════════════════════════════════════════════════════════
st.subheader("1. What arts field are you interested in?")

fields = sorted(field_state_summary["CIPDESC"].dropna().unique())
selected_field = st.selectbox("Arts field", fields)

field_data = field_state_summary[field_state_summary["CIPDESC"] == selected_field].copy()

# National benchmark, calculated live — not stored as a separate file
national_median_earnings = field_data["median_earnings_4yr"].median()
national_median_cost = field_data["median_net_cost"].median()
national_median_roi = field_data["median_roi_5yr"].median()

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: OPTIONAL HOME STATE
# ═══════════════════════════════════════════════════════════════════════════
st.subheader("2. Where are you now? (optional)")

state_names = dict(zip(state_summary["STABBR"], state_summary["state_full_name"]))
state_options = ["I'm open to any state"] + sorted(state_names.values())
selected_state_name = st.selectbox("Your current state", state_options)

home_state_abbr = None
if selected_state_name != "I'm open to any state":
    home_state_abbr = [k for k, v in state_names.items() if v == selected_state_name][0]

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# RESULTS: RANKED STATES FOR THIS FIELD
# ═══════════════════════════════════════════════════════════════════════════
st.subheader(f"States ranked by opportunity — {selected_field}")

field_data = field_data.merge(
    state_summary[["STABBR", "state_full_name", "top_inst_name",
                    "top_inst_net_cost", "control_type"]],
    on="STABBR", how="left"
)

field_data = field_data.sort_values("jobs_per_grad", ascending=False)

display_cols = field_data[[
    "state_full_name", "cluster_label", "median_earnings_4yr",
    "median_net_cost", "median_roi_5yr", "jobs_per_grad"
]].rename(columns={
    "state_full_name": "State",
    "cluster_label": "Market Type",
    "median_earnings_4yr": "Median Earnings (4yr)",
    "median_net_cost": "Median Net Cost",
    "median_roi_5yr": "Median ROI (5yr)",
    "jobs_per_grad": "Jobs per Graduate"
})

st.dataframe(
    display_cols.style.format({
        "Median Earnings (4yr)": "${:,.0f}",
        "Median Net Cost": "${:,.0f}",
        "Median ROI (5yr)": "${:,.0f}",
        "Jobs per Graduate": "{:.2f}"
    }),
    use_container_width=True,
    hide_index=True
)

st.caption(
    f"National median for {selected_field}: "
    f"${national_median_earnings:,.0f} earnings · "
    f"${national_median_cost:,.0f} cost · "
    f"${national_median_roi:,.0f} ROI (5yr)"
)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# SPOTLIGHT: HOME STATE OR TOP STATE
# ═══════════════════════════════════════════════════════════════════════════
spotlight_state = home_state_abbr if home_state_abbr else field_data.iloc[0]["STABBR"]
spotlight_row = field_data[field_data["STABBR"] == spotlight_state].iloc[0]

spotlight_label = "Your state" if home_state_abbr else "Top-ranked state for this field"
st.subheader(f"📍 {spotlight_label}: {spotlight_row['state_full_name']}")

col1, col2, col3 = st.columns(3)
col1.metric("Market Type", spotlight_row["cluster_label"])
col2.metric("Jobs per Graduate", f"{spotlight_row['jobs_per_grad']:.2f}")
col3.metric("Median ROI (5yr)", f"${spotlight_row['median_roi_5yr']:,.0f}")

if pd.notna(spotlight_row.get("top_inst_name")):
    st.write(
        f"**Example institution:** {spotlight_row['top_inst_name']} "
        f"({spotlight_row['control_type']}) — "
        f"largest arts program headcount in {spotlight_row['state_full_name']}, "
        f"with a net cost of ${spotlight_row['top_inst_net_cost']:,.0f}."
    )
    st.caption(
        "Shown as an illustrative example — the institution with the largest "
        "arts program enrollment in this state, not a ranking of program quality."
    )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# LIMITATIONS — always visible, not buried
# ═══════════════════════════════════════════════════════════════════════════
with st.expander("⚠️ Data limitations — please read"):
    st.write(
        "- Earnings and debt figures reflect students who received federal "
        "financial aid; students who did not are not represented.\n"
        "- BLS employment counts include jobs that may not require a formal "
        "arts degree, so 'jobs per graduate' should be read as a competition "
        "index, not a direct placement rate.\n"
        "- Informal or freelance arts work is not captured in these sources.\n"
        "- Figures are averaged across 2018–2022 and include pandemic-era "
        "disruption in arts employment.\n"
        "- Institution examples reflect enrollment size only, not program "
        "quality or reputation.\n"
        "- Student-level financial aid and scholarship amounts are not "
        "included, since they vary by individual and are not captured in "
        "aggregate program-level data."
    )
