import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="MiPath", page_icon=":compass:", layout="wide")

# ═══════════════════════════════════════════════════════════════════════════
# BRAND PALETTE (official — from brand color sheet). No color outside this
# list should appear anywhere in the app, including alerts and charts.
# ═══════════════════════════════════════════════════════════════════════════
GREEN = "#6B9E4E"
TAN = "#E9D2C0"
CREAM = "#F4E8DF"
WHITE = "#FEFEFE"
TERRACOTTA = "#9B2915"
MAROON = "#5C1D10"
NEAR_BLACK = "#1C110A"

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
EMP_TIER_COLOR_MAP = {
    "Low employment": TAN,
    "Medium employment": GREEN,
    "High employment": MAROON
}
RED_GRADIENT = [[0, TAN], [0.5, TERRACOTTA], [1, MAROON]]

st.markdown(f"""
    <style>
    .stApp {{ background-color: {CREAM}; }}
    section[data-testid="stSidebar"] {{ background-color: {WHITE}; }}
    h1, h2, h3 {{ color: {NEAR_BLACK} !important; font-family: Georgia, serif; }}
    div[data-testid="stMetricValue"] {{ color: {TERRACOTTA}; }}
    div[data-testid="stMetricLabel"] {{ color: {MAROON}; }}
    .stDataFrame {{ border: 1px solid {TAN}; }}
    hr {{ border-color: {TAN}; }}
    div[data-testid="stExpander"] {{ border: 1px solid {TAN}; border-radius: 6px; }}
    button[kind="primary"] {{
        background-color: {GREEN} !important; color: {WHITE} !important;
        border: none !important;
    }}
    button[kind="secondary"] {{
        background-color: {WHITE} !important; color: {MAROON} !important;
        border: 1px solid {TAN} !important;
    }}
    .info-box {{
        background-color: {TAN}; border-radius: 8px; padding: 10px 14px;
        color: {NEAR_BLACK}; font-size: 14px; margin: 8px 0;
    }}
    .cluster-card {{
        background-color: {WHITE}; border: 1px solid {TAN}; border-radius: 8px;
        padding: 10px 14px; margin-bottom: 8px;
    }}
    .filter-note {{ font-size: 12px; color: {MAROON}; font-style: italic; }}
    </style>
""", unsafe_allow_html=True)


def style_fig(fig, height=420, showlegend=True):
    """Applies consistent transparent/cream background and palette to any figure."""
    fig.update_layout(
        plot_bgcolor=CREAM, paper_bgcolor=CREAM,
        font_color=NEAR_BLACK, height=height, showlegend=showlegend,
        margin=dict(t=40, b=20, l=10, r=10)
    )
    return fig


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
            f"<h1 style='font-size:36px;'>Welcome to MiPath</h1>"
            f"<p style='font-size:16px; color:{MAROON};'>"
            f"See what an arts degree actually leads to, cost, debt, earnings, "
            f"and job demand, before you choose."
            f"</p></div>", unsafe_allow_html=True
        )
        st.markdown("<div style='height: 2vh'></div>", unsafe_allow_html=True)
        _, mid, _ = st.columns([1, 1, 1])
        with mid:
            if st.button("Start", use_container_width=True, type="primary"):
                st.session_state.started = True
                st.rerun()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# ACTIVE TAB STATE — custom nav so filters can react to which tab is open
# ═══════════════════════════════════════════════════════════════════════════
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Explore Fields"

st.title("MiPath")

nav_cols = st.columns(3)
tab_defs = ["Explore Fields", "Where to Go", "Cost & Payoff"]
for i, name in enumerate(tab_defs):
    with nav_cols[i]:
        is_active = st.session_state.active_tab == name
        if st.button(f"{i+1}. {name}", key=f"nav_{name}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.active_tab = name
            st.rerun()

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR — only shows filters relevant to the active tab
# ═══════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("### MiPath")
st.sidebar.markdown("---")

fields = sorted(field_state_summary["CIPDESC"].dropna().unique())
selected_field = st.sidebar.selectbox("Field of study", fields)

if st.session_state.active_tab in ("Where to Go", "Cost & Payoff"):
    state_options = ["I'm open to any state"] + sorted(state_names.values())
    selected_state_name = st.sidebar.selectbox("Preferred state", state_options)
else:
    selected_state_name = "I'm open to any state"
    st.sidebar.markdown("<p class='filter-note'>Preferred state — available on Where to Go and Cost & Payoff</p>",
                          unsafe_allow_html=True)

home_state_abbr = None
if selected_state_name != "I'm open to any state":
    home_state_abbr = [k for k, v in state_names.items() if v == selected_state_name][0]

if st.session_state.active_tab == "Where to Go":
    year_slider_options = ["2018-2022 average"] + sorted(state_year_trend["year"].unique().tolist())
    selected_year = st.sidebar.select_slider("Employment year", options=year_slider_options)
else:
    selected_year = "2018-2022 average"
    st.sidebar.markdown("<p class='filter-note'>Employment year — available on Where to Go</p>",
                          unsafe_allow_html=True)

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
# TAB 1 — EXPLORE FIELDS
# ═══════════════════════════════════════════════════════════════════════════
if st.session_state.active_tab == "Explore Fields":
    st.subheader("Not sure yet? Start here.")
    st.caption("Compare every arts field before narrowing in on one.")

    field_sorted = field_national.sort_values("median_earnings_4yr", ascending=True).reset_index(drop=True)
    line_widths = [3 if f == selected_field else 0 for f in field_sorted["CIPDESC"]]
    line_colors = [NEAR_BLACK if f == selected_field else "rgba(0,0,0,0)" for f in field_sorted["CIPDESC"]]

    fig_earnings = go.Figure(go.Bar(
        x=field_sorted["median_earnings_4yr"], y=field_sorted["CIPDESC"],
        orientation="h",
        marker=dict(
            color=field_sorted["median_earnings_4yr"],
            colorscale=RED_GRADIENT, showscale=False,
            line=dict(width=line_widths, color=line_colors)
        ),
        text=field_sorted["median_earnings_4yr"].apply(lambda x: f"${x:,.0f}"),
        textposition="outside",
        hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>"
    ))
    fig_earnings = style_fig(fig_earnings, height=420, showlegend=False)
    fig_earnings.update_layout(yaxis_title="", xaxis_title="Median earnings (4yr)")
    st.plotly_chart(fig_earnings, use_container_width=True)

    st.markdown(
        f"<div class='info-box'>Selected in the sidebar: <strong>{selected_field}</strong>. "
        f"Go to <strong>Where to Go</strong> to see the best states for it.</div>",
        unsafe_allow_html=True
    )

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — WHERE TO GO
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "Where to Go":
    field_data = field_state_summary[field_state_summary["CIPDESC"] == selected_field].copy()
    field_data = field_data.merge(
        state_summary[["STABBR", "state_full_name", "top_inst_name",
                        "top_inst_net_cost", "control_type"]],
        on="STABBR", how="left"
    )

    if selected_year == "2018-2022 average":
        st.subheader(f"States ranked by opportunity — {selected_field}")
        fig_map = px.choropleth(
            field_data, locations="STABBR", locationmode="USA-states",
            color="cluster_label", scope="usa",
            color_discrete_map=CLUSTER_COLOR_MAP,
            hover_name="state_full_name",
            hover_data={"STABBR": False, "jobs_per_grad": ":.2f"},
            labels={"cluster_label": "Market type", "jobs_per_grad": "Jobs per grad"}
        )
        map_metric_note = "Colored by market type (2018-2022 average) for this field."
        rank_col, rank_label = "jobs_per_grad", "Jobs per graduate"
        rank_source = field_data
    else:
        st.subheader(f"Arts employment by state — {selected_year}")
        year_data = state_year_trend[state_year_trend["year"] == selected_year].merge(
            state_summary[["STABBR", "state_full_name"]], on="STABBR", how="left"
        )
        year_data["emp_tier"] = pd.qcut(
            year_data["arts_employment"], q=3,
            labels=["Low employment", "Medium employment", "High employment"],
            duplicates="drop"
        )
        fig_map = px.choropleth(
            year_data, locations="STABBR", locationmode="USA-states",
            color="emp_tier", scope="usa",
            color_discrete_map=EMP_TIER_COLOR_MAP,
            hover_name="state_full_name",
            hover_data={"STABBR": False, "arts_employment": ":,.0f"},
            labels={"emp_tier": "Employment level", "arts_employment": "Arts jobs"}
        )
        map_metric_note = (f"Colored by total arts employment in {selected_year}. Not field-specific — "
                             "BLS employment data is organized by occupation, not field of study.")
        rank_col, rank_label = "arts_employment", "Arts jobs"
        rank_source = year_data

    # Highlight preferred state with a bold outline instead of a marker
    if home_state_abbr:
        highlight_df = pd.DataFrame({"STABBR": [home_state_abbr], "val": [1]})
        fig_map.add_trace(go.Choropleth(
            locations=highlight_df["STABBR"], locationmode="USA-states",
            z=highlight_df["val"], colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False, marker_line_color=NEAR_BLACK, marker_line_width=3,
            hoverinfo="skip"
        ))

    fig_map.update_layout(paper_bgcolor=CREAM, height=440, geo_bgcolor=CREAM,
                            legend_title_text="")
    fig_map.update_geos(bgcolor=CREAM)
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption(map_metric_note)

    # Bar chart: states with the most opportunity/jobs, below the map
    st.subheader(f"Top 10 states — {rank_label}")
    top10 = rank_source.sort_values(rank_col, ascending=False).head(10).sort_values(rank_col)
    bar_colors = [MAROON if s == home_state_abbr else GREEN for s in top10["STABBR"]]
    fig_bar = go.Figure(go.Bar(
        x=top10[rank_col], y=top10["state_full_name"], orientation="h",
        marker_color=bar_colors,
        text=top10[rank_col].apply(lambda x: f"{x:,.2f}" if rank_col == "jobs_per_grad" else f"{x:,.0f}"),
        textposition="outside",
        hovertemplate="%{y}<extra></extra>"
    ))
    fig_bar = style_fig(fig_bar, height=360, showlegend=False)
    fig_bar.update_layout(yaxis_title="", xaxis_title=rank_label)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # Spotlight — handles the case where the preferred state has no data
    # for this specific field, instead of crashing.
    spotlight_state, spotlight_label, field_missing_note = None, None, None
    if home_state_abbr:
        home_subset = field_data[field_data["STABBR"] == home_state_abbr]
        if not home_subset.empty:
            spotlight_state = home_state_abbr
            spotlight_label = "Your preferred state"
        else:
            field_missing_note = (f"{state_names.get(home_state_abbr, home_state_abbr)} "
                                    f"doesn't have data for {selected_field} in this dataset. "
                                    f"Showing the top-ranked state instead.")
    if spotlight_state is None and not field_data.empty:
        spotlight_state = field_data.sort_values("jobs_per_grad", ascending=False).iloc[0]["STABBR"]
        spotlight_label = "Top-ranked state for this field"

    if field_missing_note:
        st.markdown(f"<div class='info-box'>{field_missing_note}</div>", unsafe_allow_html=True)

    if spotlight_state:
        spotlight_row = field_data[field_data["STABBR"] == spotlight_state].iloc[0]
        st.subheader(f"{spotlight_label}: {spotlight_row['state_full_name']}")

        cluster_name = spotlight_row["cluster_label"]
        st.markdown(
            f"<div class='cluster-card'><strong>{cluster_name}</strong>"
            f"<p style='font-size:13px;color:{MAROON};margin:4px 0 0;'>"
            f"{CLUSTER_DEFINITIONS.get(cluster_name, '')}</p></div>",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)
        col1.metric("Jobs per graduate", f"{spotlight_row['jobs_per_grad']:.2f}")
        col2.metric("Median earnings (4yr)", f"${spotlight_row['median_earnings_4yr']:,.0f}")

        if pd.notna(spotlight_row.get("top_inst_name")):
            st.write(
                f"**Example school:** {spotlight_row['top_inst_name']} "
                f"({spotlight_row['control_type']}) — largest {selected_field} "
                f"program headcount in {spotlight_row['state_full_name']}, "
                f"net cost ${spotlight_row['top_inst_net_cost']:,.0f}."
            )
            st.caption("Shown as an illustrative example — largest enrollment in this state, not a ranking of program quality.")
    else:
        st.markdown(f"<div class='info-box'>No data available for {selected_field} in any state.</div>",
                     unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — COST & PAYOFF
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "Cost & Payoff":
    field_data3 = field_state_summary[field_state_summary["CIPDESC"] == selected_field].copy()

    target_state, missing_note = None, None
    if home_state_abbr:
        home_subset3 = field_data3[field_data3["STABBR"] == home_state_abbr]
        if not home_subset3.empty:
            target_state = home_state_abbr
        else:
            missing_note = (f"{state_names.get(home_state_abbr, home_state_abbr)} "
                              f"doesn't have data for {selected_field}. Showing the "
                              f"top-ranked state instead.")
    if target_state is None and not field_data3.empty:
        target_state = field_data3.sort_values("jobs_per_grad", ascending=False).iloc[0]["STABBR"]

    if missing_note:
        st.markdown(f"<div class='info-box'>{missing_note}</div>", unsafe_allow_html=True)

    if target_state:
        row = field_data3[field_data3["STABBR"] == target_state].iloc[0]
        state_label = state_names.get(target_state, target_state)

        st.subheader(f"{selected_field}, in {state_label}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Net cost", f"${row['median_net_cost']:,.0f}")
        col2.metric("Median debt", f"${row['median_debt']:,.0f}")
        col3.metric("Earnings (4yr)", f"${row['median_earnings_4yr']:,.0f}")

        payoff = row["median_earnings_4yr"] - row["median_debt"]
        direction = "outpace" if payoff >= 0 else "fall short of"
        payoff_color = GREEN if payoff >= 0 else TERRACOTTA
        st.markdown(
            f"<div class='cluster-card'>"
            f"<p style='font-size:14px;color:{NEAR_BLACK};margin:0;'>"
            f"Earnings {direction} debt by "
            f"<strong style='color:{payoff_color};'>${abs(payoff):,.0f}</strong> "
            f"within 4 years of graduating.</p></div>",
            unsafe_allow_html=True
        )

        st.divider()
        st.subheader("How this compares nationally")
        nat_row = field_national[field_national["CIPDESC"] == selected_field]
        if not nat_row.empty:
            nat_row = nat_row.iloc[0]
            fig_compare = go.Figure()
            fig_compare.add_trace(go.Bar(
                x=["Net Cost", "Median Debt", "Earnings (4yr)"],
                y=[row["median_net_cost"], row["median_debt"], row["median_earnings_4yr"]],
                name=state_label, marker_color=GREEN
            ))
            fig_compare.add_trace(go.Bar(
                x=["Net Cost", "Median Debt", "Earnings (4yr)"],
                y=[nat_row["median_net_cost"], nat_row["median_debt"], nat_row["median_earnings_4yr"]],
                name="National median", marker_color=TAN
            ))
            fig_compare.update_layout(barmode="group", legend=dict(orientation="h", yanchor="bottom", y=1.02))
            fig_compare = style_fig(fig_compare, height=380)
            fig_compare.update_layout(yaxis_title="Amount (USD)")
            st.plotly_chart(fig_compare, use_container_width=True)
    else:
        st.markdown(f"<div class='info-box'>No data available for {selected_field} in any state.</div>",
                     unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# LIMITATIONS
# ═══════════════════════════════════════════════════════════════════════════
with st.expander("Data limitations — please read"):
    st.write(
        "- Earnings and debt figures reflect students who received federal "
        "financial aid; students who did not are not represented.\n"
        "- BLS employment counts include jobs that may not require a formal "
        "arts degree, so 'jobs per graduate' should be read as a competition "
        "index, not a direct placement rate.\n"
        "- Informal or freelance arts work is not captured in these sources.\n"
        "- Averaged figures span 2018-2022 and include pandemic-era disruption.\n"
        "- The year filter on the Where to Go map shows total arts employment, "
        "not field-specific employment, since BLS data is organized by "
        "occupation, not field of study.\n"
        "- Institution examples reflect enrollment size only, not program "
        "quality or reputation.\n"
        "- Student-level financial aid and scholarship amounts are not "
        "included, since they vary by individual and are not captured in "
        "aggregate program-level data."
    )
