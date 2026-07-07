import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="MiPath", page_icon="🎨", layout="wide")

# ═══════════════════════════════════════════════════════════════════════════
# BRAND PALETTE (official — from brand color sheet)
# ═══════════════════════════════════════════════════════════════════════════
GREEN = "#6B9E4E"        # primary accent — buttons, positive metrics, earnings
TAN = "#E9D2C0"          # borders, badges, small-market cluster color
CREAM = "#F4E8DF"        # page background
WHITE = "#FEFEFE"        # card/panel background
TERRACOTTA = "#9B2915"   # cost / debt, secondary accent
MAROON = "#5C1D10"       # dark accent text, major-market cluster color
NEAR_BLACK = "#1C110A"   # primary text

CLUSTER_COLOR_MAP = {
    "Major Arts Markets": MAROON,
    "Competitive Mid-Size Markets": GREEN,
    "Accessible Small Markets": TAN
}

CLUSTER_DEFINITIONS = {
    "Major Arts Markets": "The largest arts economies, with the highest pay and the most competition.",
    "Competitive Mid-Size Markets": "A solid job market, though graduates typically outnumber openings.",
    "Accessible Small Markets": "Fewer jobs overall, but far less competition, and lower cost."
}

st.markdown(f"""
    <style>
    .stApp {{ background-color: {CREAM}; }}
    section[data-testid="stSidebar"] {{ background-color: {WHITE}; }}
    h1, h2, h3 {{
        color: {NEAR_BLACK} !important;
        font-family: Georgia, 'Times New Roman', serif;
    }}
    div[data-testid="stMetricValue"] {{ color: {TERRACOTTA}; }}
    div[data-testid="stMetricLabel"] {{ color: {MAROON}; }}
    .stDataFrame {{ border: 1px solid {TAN}; }}
    hr {{ border-color: {TAN}; }}
    div[data-testid="stExpander"] {{ border: 1px solid {TAN}; border-radius: 6px; }}
    div.stButton > button {{
        background-color: {GREEN}; color: {WHITE}; border: none;
        border-radius: 8px; padding: 0.5rem 2rem; font-size: 15px;
    }}
    div.stButton > button:hover {{ background-color: {MAROON}; color: {WHITE}; }}
    .cluster-card {{
        background-color: {WHITE}; border: 1px solid {TAN}; border-radius: 8px;
        padding: 10px 14px; margin-bottom: 8px;
    }}
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    state_summary = pd.read_csv("state_summary.csv")
    field_state_summary = pd.read_csv("field_state_summary.csv")
    trend_national = pd.read_csv("trend_national.csv")
    field_national = pd.read_csv("field_national.csv")
    state_year_trend = pd.read_csv("state_year_trend.csv")
    return state_summary, field_state_summary, trend_national, field_national, state_year_trend

state_summary, field_state_summary, trend_national, field_national, state_year_trend = load_data()
state_names = dict(zip(state_summary["STABBR"], state_summary["state_full_name"]))

# ═══════════════════════════════════════════════════════════════════════════
# LANDING PAGE GATE
# ═══════════════════════════════════════════════════════════════════════════
if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:
    st.markdown("<div style='height: 8vh'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f"<div style='text-align:center;'>"
            f"<h1 style='font-size:36px;'>🎨 Welcome to MiPath</h1>"
            f"<p style='font-size:16px; color:{MAROON};'>"
            f"See what an arts degree actually leads to, cost, debt, earnings, "
            f"and job demand, before you choose."
            f"</p></div>", unsafe_allow_html=True
        )
        st.markdown("<div style='height: 2vh'></div>", unsafe_allow_html=True)
        _, mid, _ = st.columns([1, 1, 1])
        with mid:
            if st.button("Start", use_container_width=True):
                st.session_state.started = True
                st.rerun()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR — persistent filters, visible across all tabs
# ═══════════════════════════════════════════════════════════════════════════
st.sidebar.markdown(f"<h2 style='font-size:20px;'>🎨 MiPath</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

fields = sorted(field_state_summary["CIPDESC"].dropna().unique())
selected_field = st.sidebar.selectbox("Arts field", fields)

state_options = ["I'm open to any state"] + sorted(state_names.values())
selected_state_name = st.sidebar.selectbox("Your current state", state_options)
home_state_abbr = None
if selected_state_name != "I'm open to any state":
    home_state_abbr = [k for k, v in state_names.items() if v == selected_state_name][0]

year_options = ["2018–2022 average"] + sorted(state_year_trend["year"].unique().tolist())
selected_year = st.sidebar.selectbox("Employment year (Where to Go map)", year_options)

st.sidebar.markdown("---")
st.sidebar.caption("**Market types**")
for cluster, definition in CLUSTER_DEFINITIONS.items():
    color = CLUSTER_COLOR_MAP[cluster]
    st.sidebar.markdown(
        f"<div class='cluster-card'>"
        f"<span style='display:inline-block;width:10px;height:10px;background:{color};"
        f"border-radius:2px;margin-right:6px;'></span>"
        f"<strong style='font-size:12px;'>{cluster}</strong>"
        f"<p style='font-size:11px;color:{MAROON};margin:4px 0 0;'>{definition}</p>"
        f"</div>", unsafe_allow_html=True
    )

# ═══════════════════════════════════════════════════════════════════════════
# HEADER + TABS
# ═══════════════════════════════════════════════════════════════════════════
st.title("🎨 MiPath")
tab1, tab2, tab3 = st.tabs(["1. Explore Fields", "2. Where to Go", "3. Cost & Payoff"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — EXPLORE FIELDS
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Not sure yet? Start here.")
    st.caption("Compare every arts field before narrowing in on one.")

    field_sorted = field_national.sort_values("median_earnings_4yr", ascending=True)
    field_sorted["is_selected"] = field_sorted["CIPDESC"] == selected_field

    fig_earnings = px.bar(
        field_sorted, x="median_earnings_4yr", y="CIPDESC", orientation="h",
        color="is_selected",
        color_discrete_map={True: GREEN, False: TAN},
        text_auto="$.0f",
        title="Median earnings, 4 years after graduation"
    )
    fig_earnings.update_layout(
        showlegend=False, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        font_color=NEAR_BLACK, yaxis_title="", xaxis_title="Median Earnings (4yr)",
        height=420
    )
    st.plotly_chart(fig_earnings, use_container_width=True)

    st.info(f"➡️ Selected in the sidebar: **{selected_field}**. Head to **Where to Go** to see the best states for it.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — WHERE TO GO
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    field_data = field_state_summary[field_state_summary["CIPDESC"] == selected_field].copy()
    field_data = field_data.merge(
        state_summary[["STABBR", "state_full_name", "top_inst_name",
                        "top_inst_net_cost", "control_type"]],
        on="STABBR", how="left"
    )

    if selected_year == "2018–2022 average":
        st.subheader(f"States ranked by opportunity — {selected_field}")
        field_data = field_data.sort_values("jobs_per_grad", ascending=False)
        fig_map = px.choropleth(
            field_data, locations="STABBR", locationmode="USA-states",
            color="jobs_per_grad", scope="usa",
            color_continuous_scale=[[0, TAN], [0.5, GREEN], [1, MAROON]],
            hover_name="state_full_name",
            hover_data={"STABBR": False, "jobs_per_grad": ":.2f",
                         "median_earnings_4yr": ":,.0f"},
            labels={"jobs_per_grad": "Jobs per Grad",
                    "median_earnings_4yr": "Median Earnings (4yr)"}
        )
        map_metric_note = "Colored by jobs per graduate (2018–2022 average) for this field."
    else:
        st.subheader(f"Arts employment by state — {selected_year}")
        year_data = state_year_trend[state_year_trend["year"] == selected_year].merge(
            state_summary[["STABBR", "state_full_name"]], on="STABBR", how="left"
        )
        fig_map = px.choropleth(
            year_data, locations="STABBR", locationmode="USA-states",
            color="arts_employment", scope="usa",
            color_continuous_scale=[[0, TAN], [0.5, GREEN], [1, MAROON]],
            hover_name="state_full_name",
            hover_data={"STABBR": False, "arts_employment": ":,.0f"},
            labels={"arts_employment": "Arts Jobs"}
        )
        map_metric_note = (f"Colored by total arts employment in {selected_year} — "
                             "this view is not specific to your selected field, since BLS "
                             "employment data is by occupation, not field of study.")

    if home_state_abbr:
        fig_map.add_trace(go.Scattergeo(
            locations=[home_state_abbr], locationmode="USA-states",
            marker=dict(size=18, color=NEAR_BLACK, symbol="star"),
            name="Your state", showlegend=True
        ))
    fig_map.update_layout(paper_bgcolor=CREAM, height=440, geo_bgcolor=CREAM)
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption(map_metric_note)

    st.divider()

    spotlight_state = home_state_abbr if home_state_abbr else (
        field_data.iloc[0]["STABBR"] if not field_data.empty else None
    )
    if spotlight_state:
        spotlight_row = field_data[field_data["STABBR"] == spotlight_state].iloc[0]
        spotlight_label = "Your state" if home_state_abbr else "Top-ranked state for this field"
        st.subheader(f"📍 {spotlight_label}: {spotlight_row['state_full_name']}")

        cluster_name = spotlight_row["cluster_label"]
        st.markdown(
            f"<div class='cluster-card'><strong>{cluster_name}</strong>"
            f"<p style='font-size:13px;color:{MAROON};margin:4px 0 0;'>"
            f"{CLUSTER_DEFINITIONS.get(cluster_name, '')}</p></div>",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)
        col1.metric("Jobs per Graduate", f"{spotlight_row['jobs_per_grad']:.2f}")
        col2.metric("Median Earnings (4yr)", f"${spotlight_row['median_earnings_4yr']:,.0f}")

        if pd.notna(spotlight_row.get("top_inst_name")):
            st.write(
                f"**Example school:** {spotlight_row['top_inst_name']} "
                f"({spotlight_row['control_type']}) — largest {selected_field} "
                f"program headcount in {spotlight_row['state_full_name']}, "
                f"net cost ${spotlight_row['top_inst_net_cost']:,.0f}."
            )
            st.caption("Shown as an illustrative example — largest enrollment in this state, not a ranking of program quality.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — COST & PAYOFF
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    field_data3 = field_state_summary[field_state_summary["CIPDESC"] == selected_field].copy()
    target_state = home_state_abbr if home_state_abbr else (
        field_data3.sort_values("jobs_per_grad", ascending=False).iloc[0]["STABBR"]
        if not field_data3.empty else None
    )

    if target_state:
        row = field_data3[field_data3["STABBR"] == target_state].iloc[0]
        state_label = state_names.get(target_state, target_state)

        st.subheader(f"{selected_field}, in {state_label}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Net Cost", f"${row['median_net_cost']:,.0f}")
        col2.metric("Median Debt", f"${row['median_debt']:,.0f}")
        col3.metric("Earnings (4yr)", f"${row['median_earnings_4yr']:,.0f}")

        payoff = row["median_earnings_4yr"] - row["median_debt"]
        direction = "outpace" if payoff >= 0 else "fall short of"
        st.markdown(
            f"<div class='cluster-card'>"
            f"<p style='font-size:14px;color:{NEAR_BLACK};margin:0;'>"
            f"Earnings {direction} debt by "
            f"<strong style='color:{GREEN if payoff >= 0 else TERRACOTTA};'>${abs(payoff):,.0f}</strong> "
            f"within 4 years of graduating.</p></div>",
            unsafe_allow_html=True
        )

        st.divider()
        st.subheader("How this compares nationally")
        nat_row = field_national[field_national["CIPDESC"] == selected_field]
        if not nat_row.empty:
            nat_row = nat_row.iloc[0]
            compare_df = pd.DataFrame({
                "Metric": ["Net Cost", "Median Debt", "Earnings (4yr)"],
                state_label: [row["median_net_cost"], row["median_debt"], row["median_earnings_4yr"]],
                "National Median": [nat_row["median_net_cost"], nat_row["median_debt"], nat_row["median_earnings_4yr"]]
            })
            fig_compare = go.Figure()
            fig_compare.add_trace(go.Bar(
                x=compare_df["Metric"], y=compare_df[state_label],
                name=state_label, marker_color=GREEN
            ))
            fig_compare.add_trace(go.Bar(
                x=compare_df["Metric"], y=compare_df["National Median"],
                name="National Median", marker_color=TAN
            ))
            fig_compare.update_layout(
                barmode="group", plot_bgcolor=WHITE, paper_bgcolor=WHITE,
                font_color=NEAR_BLACK, yaxis_title="Amount (USD)", height=380
            )
            st.plotly_chart(fig_compare, use_container_width=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# LIMITATIONS
# ═══════════════════════════════════════════════════════════════════════════
with st.expander("⚠️ Data limitations — please read"):
    st.write(
        "- Earnings and debt figures reflect students who received federal "
        "financial aid; students who did not are not represented.\n"
        "- BLS employment counts include jobs that may not require a formal "
        "arts degree, so 'jobs per graduate' should be read as a competition "
        "index, not a direct placement rate.\n"
        "- Informal or freelance arts work is not captured in these sources.\n"
        "- Averaged figures span 2018–2022 and include pandemic-era disruption.\n"
        "- The year filter on the Where to Go map shows total arts employment, "
        "not field-specific employment, since BLS data is organized by "
        "occupation, not field of study.\n"
        "- Institution examples reflect enrollment size only, not program "
        "quality or reputation.\n"
        "- Student-level financial aid and scholarship amounts are not "
        "included, since they vary by individual and are not captured in "
        "aggregate program-level data."
    )
