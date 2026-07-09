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
    "Major Arts Markets": TERRACOTTA,
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
    "High employment": TERRACOTTA
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


def fmt_money(x):
    """Shows a real value, or an honest label when Scorecard suppressed it
    (cohorts under 30 students return no earnings/debt figure)."""
    return f"${x:,.0f}" if pd.notna(x) else "Suppressed (small cohort)"

def fmt_num(x, decimals=2):
    return f"{x:.{decimals}f}" if pd.notna(x) else "N/A"

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
    top_institutions = pd.read_csv("top_institutions.csv")
    return (state_summary, field_state_summary, trend_national, field_national,
            state_year_trend, top_institutions)

(state_summary, field_state_summary, trend_national, field_national,
 state_year_trend, top_institutions) = load_data()
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
# FILTERS — Explore Fields has no sidebar at all; the field selector lives
# inline in that tab's own content. Where to Go / Cost & Payoff keep the
# sidebar, with each filter in its own bordered box for readability.
# ═══════════════════════════════════════════════════════════════════════════
fields = sorted(field_state_summary["CIPDESC"].dropna().unique())
year_slider_options = ["2018-2022 average"] + sorted(state_year_trend["year"].unique().tolist())

if st.session_state.active_tab == "Explore Fields":
    selected_state_name = "I'm open to any state"
    selected_year = "2018-2022 average"
    # selected_field is rendered inline within the tab body below
else:
    st.sidebar.markdown("### MiPath")
    st.sidebar.markdown("---")

    with st.sidebar.container(border=True):
        selected_field = st.selectbox("Field of study", fields, key="global_field_select")

    if st.session_state.active_tab in ("Where to Go", "Cost & Payoff"):
        state_options = ["I'm open to any state"] + sorted(state_names.values())
        with st.sidebar.container(border=True):
            selected_state_name = st.selectbox("Preferred state", state_options, key="global_state_select")
    else:
        selected_state_name = "I'm open to any state"

    if st.session_state.active_tab == "Where to Go":
        with st.sidebar.container(border=True):
            selected_year = st.select_slider("Employment year", options=year_slider_options, key="global_year_select")
    else:
        selected_year = "2018-2022 average"

home_state_abbr = None
if selected_state_name != "I'm open to any state":
    home_state_abbr = [k for k, v in state_names.items() if v == selected_state_name][0]

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — EXPLORE FIELDS (no sidebar — this tab is a standalone exploration page)
# ═══════════════════════════════════════════════════════════════════════════
if st.session_state.active_tab == "Explore Fields":
    st.subheader("Not sure yet? Start here.")
    with st.container(border=True):
        selected_field = st.selectbox("Field of study", fields, key="global_field_select")
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
        f"<div class='info-box'>Selected: <strong>{selected_field}</strong>. "
        f"Go to <strong>Where to Go</strong> to see the best states for it.</div>",
        unsafe_allow_html=True
    )

    st.divider()
    st.subheader("The bigger picture: U.S. arts employment, 2018-2022")
    fig_trend = go.Figure(go.Scatter(
        x=trend_national["year"], y=trend_national["arts_employment"],
        mode="lines+markers", line=dict(color=GREEN, width=3),
        marker=dict(size=8, color=GREEN),
        hovertemplate="%{x}: %{y:,.0f} jobs<extra></extra>"
    ))
    fig_trend.add_vrect(x0=2019.5, x1=2021.5, fillcolor=TERRACOTTA, opacity=0.12, line_width=0)
    fig_trend = style_fig(fig_trend, height=320, showlegend=False)
    fig_trend.update_layout(
        xaxis=dict(tickmode="array", tickvals=[2018, 2019, 2020, 2021, 2022]),
        yaxis_title="Total arts jobs", xaxis_title=""
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    st.caption("Employment dropped sharply during the pandemic (shaded) and had recovered by 2022. "
                "Figures elsewhere in this tool are averaged across the full period, so this dip is "
                "smoothed into those averages.")

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

    # Spotlight — field-aware: uses the selected field to pick the state,
    # so the recommendation actually changes when the field changes.
    # Handles the case where the preferred state has no data for this
    # specific field, instead of crashing.
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
        has_earnings = field_data.dropna(subset=["median_earnings_4yr"])
        ranking_pool = has_earnings if not has_earnings.empty else field_data
        spotlight_state = ranking_pool.sort_values("jobs_per_grad", ascending=False).iloc[0]["STABBR"]
        spotlight_label = f"Top-ranked state for {selected_field}"

    if field_missing_note:
        st.markdown(f"<div class='info-box'>{field_missing_note}</div>", unsafe_allow_html=True)

    # ── Spotlight block, at the top — this is the answer to "where do I go" ──
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

        col1, col2, col3 = st.columns(3)
        col1.metric("Jobs per graduate", fmt_num(spotlight_row["jobs_per_grad"]))
        col2.metric("Median earnings (4yr)", fmt_money(spotlight_row["median_earnings_4yr"]))
        col3.metric("Avg. industry pay", fmt_money(spotlight_row.get("avg_compensation")))
        st.caption("Industry pay reflects the whole arts sector in this state (BEA), not just recent graduates — a broader signal of how the local market pays.")

        schools = top_institutions[top_institutions["STABBR"] == spotlight_state].sort_values("rank")
        if not schools.empty:
            st.write(f"**Schools with the most arts enrollment in {spotlight_row['state_full_name']}:**")
            for _, school in schools.iterrows():
                st.markdown(
                    f"<div class='cluster-card'>"
                    f"<strong>{int(school['rank'])}. {school['inst_name']}</strong> "
                    f"<span style='color:{MAROON};font-size:12px;'>({school['control_type']})</span>"
                    f"<p style='font-size:12px;color:{MAROON};margin:4px 0 0;'>"
                    f"{int(school['total_arts_headcount']):,} arts students &middot; "
                    f"net cost {fmt_money(school['inst_net_cost'])}</p></div>",
                    unsafe_allow_html=True
                )
            st.caption("Ranked by arts program enrollment size, not program quality or reputation.")
    else:
        st.markdown(f"<div class='info-box'>No data available for {selected_field} in any state.</div>",
                     unsafe_allow_html=True)

    st.divider()

    # ── Map, with the cluster legend/definitions placed right beside it ──────
    map_col, legend_col = st.columns([3, 1])

    if selected_year == "2018-2022 average":
        map_title = f"States ranked by opportunity — {selected_field}"
        fig_map = px.choropleth(
            field_data, locations="STABBR", locationmode="USA-states",
            color="cluster_label", scope="usa",
            color_discrete_map=CLUSTER_COLOR_MAP,
            hover_name="state_full_name",
            hover_data={"STABBR": False, "jobs_per_grad": ":.2f"},
            labels={"cluster_label": "Market type", "jobs_per_grad": "Jobs per grad"}
        )
        map_metric_note = "Colored by market type (2018-2022 average) for this field."
        rank_col, rank_label, rank_source = "jobs_per_grad", "Jobs per graduate", field_data
    else:
        map_title = f"Arts employment by state — {selected_year}"
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
        rank_col, rank_label, rank_source = "arts_employment", "Arts jobs", year_data

    if home_state_abbr:
        highlight_df = pd.DataFrame({"STABBR": [home_state_abbr], "val": [1]})
        fig_map.add_trace(go.Choropleth(
            locations=highlight_df["STABBR"], locationmode="USA-states",
            z=highlight_df["val"], colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False, marker_line_color=NEAR_BLACK, marker_line_width=3,
            hoverinfo="skip"
        ))

    fig_map.update_layout(paper_bgcolor=CREAM, height=440, geo_bgcolor=CREAM, legend_title_text="")
    fig_map.update_geos(bgcolor=CREAM)

    with map_col:
        st.subheader(map_title)
        st.plotly_chart(fig_map, use_container_width=True)
        st.caption(map_metric_note)

    with legend_col:
        st.markdown("<div style='height:2.8rem'></div>", unsafe_allow_html=True)
        for cluster, definition in CLUSTER_DEFINITIONS.items():
            color = CLUSTER_COLOR_MAP[cluster]
            st.markdown(
                f"<div class='cluster-card'>"
                f"<span style='display:inline-block;width:10px;height:10px;background:{color};"
                f"border-radius:2px;margin-right:6px;'></span>"
                f"<strong style='font-size:12px;'>{cluster}</strong>"
                f"<p style='font-size:11px;color:{MAROON};margin:4px 0 0;'>{definition}</p>"
                f"</div>", unsafe_allow_html=True
            )

    # ── Bar chart: only when browsing broadly, not when a state is already chosen ──
    if not home_state_abbr:
        st.subheader(f"Top 10 states — {rank_label}")
        top10 = rank_source.dropna(subset=[rank_col]).sort_values(
            rank_col, ascending=False
        ).head(10).sort_values(rank_col)
        fig_bar = go.Figure(go.Bar(
            x=top10[rank_col], y=top10["state_full_name"], orientation="h",
            marker_color=GREEN,
            text=top10[rank_col].apply(lambda x: f"{x:,.2f}" if rank_col == "jobs_per_grad" else f"{x:,.0f}"),
            textposition="outside",
            hovertemplate="%{y}<extra></extra>"
        ))
        fig_bar = style_fig(fig_bar, height=360, showlegend=False)
        fig_bar.update_layout(yaxis_title="", xaxis_title=rank_label)
        st.plotly_chart(fig_bar, use_container_width=True)


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
        has_earnings3 = field_data3.dropna(subset=["median_earnings_4yr"])
        ranking_pool3 = has_earnings3 if not has_earnings3.empty else field_data3
        target_state = ranking_pool3.sort_values("jobs_per_grad", ascending=False).iloc[0]["STABBR"]

    if missing_note:
        st.markdown(f"<div class='info-box'>{missing_note}</div>", unsafe_allow_html=True)

    if target_state:
        row = field_data3[field_data3["STABBR"] == target_state].iloc[0]
        state_label = state_names.get(target_state, target_state)

        st.subheader(f"{selected_field}, in {state_label}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Net cost", fmt_money(row["median_net_cost"]))
        col2.metric("Median debt", fmt_money(row["median_debt"]))
        col3.metric("Earnings (4yr)", fmt_money(row["median_earnings_4yr"]))

        if pd.notna(row.get("median_roi_5yr")):
            roi = row["median_roi_5yr"]
            direction = "outpace" if roi >= 0 else "fall short of"
            payoff_color = GREEN if roi >= 0 else TERRACOTTA
            st.markdown(
                f"<div class='cluster-card'>"
                f"<p style='font-size:14px;color:{NEAR_BLACK};margin:0;'>"
                f"5 years after graduating, earnings {direction} debt by "
                f"<strong style='color:{payoff_color};'>${abs(roi):,.0f}</strong>.</p></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='info-box'>Earnings or debt data is suppressed for this "
                f"field/state combination (College Scorecard withholds figures for "
                f"cohorts under 30 students), so the 5-year payoff can't be shown.</div>",
                unsafe_allow_html=True
            )

        if pd.notna(row.get("total_grads")):
            st.caption(f"About {int(row['total_grads']):,} students graduate from {selected_field} "
                        f"programs in {state_label} each year — that's the competition for local jobs.")

        st.divider()
        st.subheader(f"How {state_label} Compares to the Rest of the Country")
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
