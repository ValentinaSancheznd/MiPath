import streamlit as st
import pandas as pd
import numpy as np
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
CREAM = "#FAF6F2"
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    .stApp {{ background-color: {CREAM}; }}

    section[data-testid="stSidebar"] {{
        background-color: #FEF9F5;
        border-right: 1px solid {TAN};
    }}
    section[data-testid="stSidebar"] > div {{ padding: 24px 20px; }}

    h1 {{ font-size: 40px; font-weight: 700; color: {NEAR_BLACK} !important;
          font-family: 'Inter', sans-serif; margin-bottom: 8px; }}
    h2 {{ font-size: 28px; font-weight: 700; color: {NEAR_BLACK} !important;
          font-family: 'Inter', sans-serif; margin-bottom: 8px; }}
    h3 {{ font-size: 20px; font-weight: 600; color: {NEAR_BLACK} !important;
          font-family: 'Inter', sans-serif; margin-bottom: 8px; }}
    p, div, span, label {{ font-family: 'Inter', sans-serif; }}

    /* Body text uses the darker maroon — terracotta is reserved for brand
       and data-viz accents, per the palette guidance. */
    div[data-testid="stMetricValue"] {{ color: {MAROON}; font-weight: 700; }}
    div[data-testid="stMetricLabel"] {{ color: {MAROON}; font-size: 14px; font-weight: 500; }}

    .stDataFrame, div[data-testid="stDataFrame"] {{
        border: 1px solid {TAN}; border-radius: 16px; overflow: hidden;
    }}
    hr {{ border-color: {TAN}; margin: 40px 0; }}

    div[data-testid="stExpander"] {{ border: 1px solid {TAN}; border-radius: 16px; }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 16px; }}

    button {{ border-radius: 16px !important; }}
    button[kind="primary"] {{
        background-color: {GREEN} !important; color: {WHITE} !important;
        border: none !important; padding: 0.6rem 1rem !important;
        font-weight: 600 !important; min-height: 44px;
    }}
    button[kind="primary"]:hover {{ background-color: #5A8A40 !important; }}
    button[kind="secondary"] {{
        background-color: {WHITE} !important; color: {MAROON} !important;
        border: 1px solid {TAN} !important; border-radius: 16px !important;
        min-height: 44px;
    }}

    div[data-baseweb="select"] > div {{
        border-radius: 14px !important; background-color: {WHITE} !important;
        border-color: {TAN} !important; padding-top: 2px; padding-bottom: 2px;
    }}

    .info-box {{
        background-color: {TAN}; border-radius: 16px; padding: 12px 16px;
        color: {NEAR_BLACK}; font-size: 14px; margin: 16px 0;
    }}
    .cluster-card {{
        background-color: {WHITE}; border: 1px solid {TAN}; border-radius: 16px;
        padding: 16px; margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(28, 17, 10, 0.06);
    }}
    .filter-note {{ font-size: 12px; color: {MAROON}; font-style: italic; }}
    </style>
""", unsafe_allow_html=True)


def fmt_money(x):
    return f"${x:,.0f}" if pd.notna(x) else "—"

def fmt_num(x, decimals=2):
    return f"{x:.{decimals}f}" if pd.notna(x) else "—"

def metric_card(label, value, sub_note=None):
    """Custom metric display. sub_note shows either a comparison to the
    U.S. average (when data exists) or a plain explanation of why it's
    missing (when it doesn't) — set by the caller."""
    note_html = (f"<p style='font-size:11px;color:{MAROON};margin:4px 0 0;'>{sub_note}</p>"
                 if sub_note else "")
    st.markdown(
        f"<div class='cluster-card'><p style='font-size:12px;color:{MAROON};margin:0;'>{label}</p>"
        f"<p style='font-size:24px;font-weight:700;color:{MAROON};margin:2px 0 0;'>{value}</p>{note_html}</div>",
        unsafe_allow_html=True
    )

def compare_note(value_raw, national_val, formatter):
    """Builds the 'Lower/Higher than the U.S. average (X)' line."""
    if pd.isna(value_raw) or pd.isna(national_val):
        return None
    if value_raw < national_val:
        direction = "Lower"
    elif value_raw > national_val:
        direction = "Higher"
    else:
        direction = "Equal"
    return f"{direction} than the U.S. average ({formatter(national_val)})"

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
    st.markdown("<div style='height: 6vh'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.2, 1])

    with left:
        st.markdown(
            f"""
            <h1 style='font-size:46px; line-height:1.1; color:{MAROON}; margin-bottom:12px;'>
            Explore your future<br>through the arts.
            </h1>

            <p style='font-size:18px; color:{MAROON}; max-width:520px;'>
            Compare employment, salaries, tuition and schools before deciding on an arts degree.
            </p>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        if st.button("Start Exploring", type="primary", width="stretch"):
            st.session_state.started = True
            st.rerun()

    with right:
        st.image("Assets/hero.png", width="stretch")

    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# PENDING UPDATES — clicks (map, bars) can't set a widget's session_state
# key directly once that widget has already rendered this run. So clicks
# stash the new value here, then rerun; on the NEXT run, before any widget
# is created, we apply it — which Streamlit allows.
# ═══════════════════════════════════════════════════════════════════════════
if "chart_nonce" not in st.session_state:
    st.session_state["chart_nonce"] = 0

if "pending_state_update" in st.session_state:
    st.session_state["global_state_select"] = st.session_state.pop("pending_state_update")
    st.session_state["chart_nonce"] += 1
if "pending_field_update" in st.session_state:
    st.session_state["global_field_select"] = st.session_state.pop("pending_field_update")
    st.session_state["chart_nonce"] += 1

# ═══════════════════════════════════════════════════════════════════════════
# ACTIVE TAB STATE — custom nav so filters can react to which tab is open
# ═══════════════════════════════════════════════════════════════════════════
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Explore Fields"

nav_cols = st.columns(3)
tab_defs = ["Explore Fields", "Where to Go", "Cost & Payoff"]
tab_switch_requested = False
for i, name in enumerate(tab_defs):
    with nav_cols[i]:
        is_active = st.session_state.active_tab == name
        if st.button(f"{i+1}. {name}", key=f"nav_{name}", width="stretch",
                     type="primary" if is_active else "secondary"):
            st.session_state.active_tab = name
            tab_switch_requested = True

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# FILTERS — Preferred state and Employment year only show on the tabs
# where they apply.
# ═══════════════════════════════════════════════════════════════════════════
fields = sorted(field_state_summary["CIPDESC"].dropna().unique())
year_slider_options = ["2018-2022 average"] + sorted(state_year_trend["year"].unique().tolist())

if "total_grads" in field_national.columns and field_national["total_grads"].notna().any():
    most_popular_field = field_national.sort_values("total_grads", ascending=False).iloc[0]["CIPDESC"]
else:
    most_popular_field = fields[0]

st.sidebar.image("Assets/logo_horizontal.png", width=180)
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("---")

field_options = ["I'm open to any field"] + fields
with st.sidebar.container(border=True, key="field_container"):
    selected_field_raw = st.selectbox("Field of study", field_options, key="global_field_select")

if selected_field_raw == "I'm open to any field":
    selected_field = most_popular_field
    field_is_default = True
else:
    selected_field = selected_field_raw
    field_is_default = False

if st.session_state.active_tab in ("Where to Go", "Cost & Payoff"):
    state_options = ["I'm open to any state"] + sorted(state_names.values())
    with st.sidebar.container(border=True, key="state_container"):
        selected_state_name = st.selectbox("Preferred state", state_options, key="global_state_select")
else:
    selected_state_name = "I'm open to any state"

if st.session_state.active_tab == "Where to Go":
    with st.sidebar.container(border=True, key="year_container"):
        selected_year = st.select_slider("Employment year", options=year_slider_options, key="global_year_select")
else:
    selected_year = "2018-2022 average"

home_state_abbr = None
if selected_state_name != "I'm open to any state":
    home_state_abbr = [k for k, v in state_names.items() if v == selected_state_name][0]

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — EXPLORE FIELDS (sidebar dropdown and bars stay in sync)
# ═══════════════════════════════════════════════════════════════════════════
if st.session_state.active_tab == "Explore Fields":
    st.subheader("Not sure yet? Start here.")
    if field_is_default:
        st.caption(f"Showing the most popular field nationally. Click a bar (or use the sidebar) to choose your own.")
    else:
        st.caption("Click a bar (or use the sidebar) to choose a different field.")

    field_sorted = field_national.sort_values("median_earnings_4yr", ascending=True).reset_index(drop=True)

    n = len(field_sorted)
    def terracotta_opacity(i):
        # Tiered opacity by rank quartile — 100/85/70/55%, darkest for the
        # highest earners, lightest for the lowest, all in the brand terracotta.
        pct = i / max(n - 1, 1)
        if pct >= 0.75:
            return "rgba(155,41,21,1.0)"
        elif pct >= 0.5:
            return "rgba(155,41,21,0.85)"
        elif pct >= 0.25:
            return "rgba(155,41,21,0.70)"
        else:
            return "rgba(155,41,21,0.55)"

    bar_colors = [GREEN if f == selected_field else terracotta_opacity(i)
                   for i, f in enumerate(field_sorted["CIPDESC"])]
    label_texts = [f"${v:,.0f}  ✓" if f == selected_field else f"${v:,.0f}"
                    for f, v in zip(field_sorted["CIPDESC"], field_sorted["median_earnings_4yr"])]

    fig_earnings = go.Figure(go.Bar(
        x=field_sorted["median_earnings_4yr"], y=field_sorted["CIPDESC"],
        orientation="h",
        marker=dict(color=bar_colors),
        text=label_texts,
        textposition="outside",
        hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>"
    ))
    fig_earnings = style_fig(fig_earnings, height=420, showlegend=False)
    fig_earnings.update_layout(yaxis_title="", xaxis_title="Annual earnings, 4 years after graduation")

    field_click = st.plotly_chart(fig_earnings, width="stretch",
                                    on_select="rerun", key=f"explore_field_click_{st.session_state.chart_nonce}")
    st.caption("These are annual salaries measured 4 years after graduation, among graduates who "
                "received federal financial aid and were working (not back in school) when measured.")
    clicked_pts = field_click.get("selection", {}).get("points", []) if field_click else []
    if clicked_pts:
        pt = clicked_pts[0]
        clicked_field = pt.get("y")
        if not clicked_field:
            idx = pt.get("point_index", pt.get("point_number"))
            if idx is not None and idx < len(field_sorted):
                clicked_field = field_sorted.iloc[idx]["CIPDESC"]
        if clicked_field and clicked_field != selected_field_raw:
            st.session_state["pending_field_update"] = clicked_field
            st.rerun()

    info_text = (f"Most popular field nationally: <strong>{selected_field}</strong>."
                  if field_is_default else f"Selected: <strong>{selected_field}</strong>.")
    st.markdown(
        f"<div class='info-box'>{info_text} "
        f"Go to <strong>Where to Go</strong> to see the best states for it.</div>",
        unsafe_allow_html=True
    )

    st.divider()
    st.subheader("U.S. Arts Employment, 2018-2022")
    trend_year_options = ["All years"] + sorted(trend_national["year"].unique().tolist())
    highlight_year = st.select_slider("Highlight a year (zooms in around it)",
                                        options=trend_year_options, value="All years")

    if highlight_year == "All years":
        marker_sizes = [8] * len(trend_national)
        marker_colors = [GREEN] * len(trend_national)
        text_sizes = [11] * len(trend_national)
        text_colors = [MAROON] * len(trend_national)
        zoom_min, zoom_max = 2017.6, 2022.4
    else:
        marker_sizes = [16 if y == highlight_year else 8 for y in trend_national["year"]]
        marker_colors = [TERRACOTTA if y == highlight_year else GREEN for y in trend_national["year"]]
        text_sizes = [16 if y == highlight_year else 11 for y in trend_national["year"]]
        text_colors = [TERRACOTTA if y == highlight_year else MAROON for y in trend_national["year"]]
        zoom_min = max(2018, highlight_year - 1) - 0.4
        zoom_max = min(2022, highlight_year + 1) + 0.4

    fig_trend = go.Figure(go.Scatter(
        x=trend_national["year"], y=trend_national["arts_employment"],
        mode="lines+markers+text",
        line=dict(color=GREEN, width=3),
        marker=dict(size=marker_sizes, color=marker_colors),
        text=[f"{v:,.0f}" for v in trend_national["arts_employment"]],
        textposition="top center",
        textfont=dict(size=text_sizes, color=text_colors),
        hovertemplate="%{x}: %{y:,.0f} jobs<extra></extra>"
    ))
    fig_trend.add_vrect(x0=2019.5, x1=2021.5, fillcolor=TERRACOTTA, opacity=0.12, line_width=0)
    fig_trend = style_fig(fig_trend, height=340, showlegend=False)
    fig_trend.update_layout(
        xaxis=dict(tickmode="array", tickvals=[2018, 2019, 2020, 2021, 2022], range=[zoom_min, zoom_max]),
        yaxis_title="Total arts jobs", xaxis_title=""
    )
    st.plotly_chart(fig_trend, width="stretch")

    if highlight_year == "All years":
        st.caption("The pandemic dip (shaded) had recovered by 2022. Figures elsewhere in this tool "
                    "are averaged across 2018-2022, so this dip is smoothed into those averages.")
    else:
        highlight_val = trend_national[trend_national["year"] == highlight_year]["arts_employment"].iloc[0]
        st.caption(f"{highlight_year}: {highlight_val:,.0f} total arts jobs nationally. "
                    "The pandemic dip (shaded) had recovered by 2022. Figures elsewhere in this tool "
                    "are averaged across 2018-2022, so this dip is smoothed into those averages.")

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
        cluster_name = spotlight_row["cluster_label"]
        badge_color = CLUSTER_COLOR_MAP.get(cluster_name, TAN)

        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;'>"
            f"<h3 style='margin:0;'>{spotlight_label}: "
            f"<span style='color:{TERRACOTTA};'>{spotlight_row['state_full_name']}</span></h3>"
            f"<span style='background:{badge_color};color:{WHITE};font-size:12px;"
            f"padding:4px 12px;border-radius:14px;white-space:nowrap;'>{cluster_name}</span>"
            f"</div>"
            f"<p style='color:{MAROON};font-size:13px;margin:6px 0 16px;'>"
            f"{CLUSTER_DEFINITIONS.get(cluster_name, '')}</p>",
            unsafe_allow_html=True
        )

        if not home_state_abbr:
            st.caption("Ranked by jobs per graduate, among states with reported earnings data.")

        nat_jobs_per_grad = field_data["jobs_per_grad"].mean(skipna=True)
        nat_earnings_row = field_national[field_national["CIPDESC"] == selected_field]
        nat_earnings = nat_earnings_row.iloc[0]["median_earnings_4yr"] if not nat_earnings_row.empty else np.nan
        nat_compensation = state_summary["avg_compensation"].mean(skipna=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            note = (compare_note(spotlight_row["jobs_per_grad"], nat_jobs_per_grad, lambda v: f"{v:.2f}")
                     if pd.notna(spotlight_row["jobs_per_grad"])
                     else "No employment data available for this field/state.")
            metric_card("Jobs per graduate", fmt_num(spotlight_row["jobs_per_grad"]), note)
        with col2:
            note = (compare_note(spotlight_row["median_earnings_4yr"], nat_earnings, lambda v: f"${v:,.0f}")
                     if pd.notna(spotlight_row["median_earnings_4yr"])
                     else "Cohort too small to report (fewer than 30 students).")
            metric_card("Annual earnings (4 yrs after grad)", fmt_money(spotlight_row["median_earnings_4yr"]), note)
        with col3:
            note = (compare_note(spotlight_row.get("avg_compensation"), nat_compensation, lambda v: f"${v:,.0f}")
                     if pd.notna(spotlight_row.get("avg_compensation"))
                     else "Industry compensation not reported for this state.")
            metric_card("Avg. industry pay", fmt_money(spotlight_row.get("avg_compensation")), note)
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
        base_df = field_data.reset_index(drop=True)
        map_title = (f"How {state_names.get(home_state_abbr)} Compares"
                      if home_state_abbr else f"States ranked by opportunity — {selected_field}")
        fig_map = px.choropleth(
            base_df, locations="STABBR", locationmode="USA-states",
            color="cluster_label", scope="usa",
            color_discrete_map=CLUSTER_COLOR_MAP,
            hover_name="state_full_name",
            hover_data={"STABBR": False, "jobs_per_grad": ":.2f"},
            labels={"cluster_label": "Market type", "jobs_per_grad": "Jobs per grad"}
        )
        map_metric_note = "Colored by market type (2018-2022 average) for this field."
        rank_col, rank_label, rank_source = "jobs_per_grad", "Jobs per graduate", field_data
    else:
        year_data = state_year_trend[state_year_trend["year"] == selected_year].merge(
            state_summary[["STABBR", "state_full_name"]], on="STABBR", how="left"
        )
        year_data["emp_tier"] = pd.qcut(
            year_data["arts_employment"], q=3,
            labels=["Low employment", "Medium employment", "High employment"],
            duplicates="drop"
        )
        base_df = year_data.reset_index(drop=True)
        map_title = (f"How {state_names.get(home_state_abbr)} Compares — {selected_year}"
                      if home_state_abbr else f"Arts employment by state — {selected_year}")
        fig_map = px.choropleth(
            base_df, locations="STABBR", locationmode="USA-states",
            color="emp_tier", scope="usa",
            color_discrete_map=EMP_TIER_COLOR_MAP,
            hover_name="state_full_name",
            hover_data={"STABBR": False, "arts_employment": ":,.0f"},
            labels={"emp_tier": "Employment level", "arts_employment": "Arts jobs"}
        )
        map_metric_note = (f"Colored by total arts employment in {selected_year}. Not field-specific — "
                             "BLS employment data is organized by occupation, not field of study.")
        rank_col, rank_label, rank_source = "arts_employment", "Arts jobs", year_data

    # Highlight the preferred state with a dedicated overlay trace instead of
    # a per-point border array — because color_discrete_map (categorical
    # coloring) makes Plotly split the map into multiple traces internally,
    # one per category. A single border array indexed against base_df's row
    # order doesn't line up correctly across those separate traces, which is
    # why the wrong state was getting highlighted. An overlay trace with just
    # the target state sidesteps that entirely, regardless of how many
    # underlying traces the categorical coloring creates.
    if home_state_abbr:
        fig_map.add_trace(go.Choropleth(
            locations=[home_state_abbr], locationmode="USA-states", z=[1],
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False, marker_line_color=NEAR_BLACK, marker_line_width=4,
            hoverinfo="skip", showlegend=False
        ))

    fig_map.update_layout(paper_bgcolor=CREAM, height=440, geo_bgcolor=CREAM, showlegend=False)
    fig_map.update_geos(bgcolor=CREAM)

    with map_col:
        st.subheader(map_title)
        st.caption("Click a state on the map to set it as your preferred state.")
        map_event = st.plotly_chart(fig_map, width="stretch",
                                      on_select="rerun", key=f"wtg_map_click_{st.session_state.chart_nonce}")
        st.caption(map_metric_note)

        clicked_points = map_event.get("selection", {}).get("points", []) if map_event else []
        if clicked_points:
            # Trust Plotly's own 'location' field — it's per-point and tied to
            # the geo id directly, so it's correct no matter which underlying
            # trace (category) the click landed on. No manual index math.
            clicked_loc = clicked_points[0].get("location")
            if clicked_loc and clicked_loc in state_names:
                clicked_full_name = state_names[clicked_loc]
                if st.session_state.get("global_state_select") != clicked_full_name:
                    st.session_state["pending_state_update"] = clicked_full_name
                    st.rerun()

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
        chart_context = (f"for {selected_field}" if selected_year == "2018-2022 average"
                           else f"in {selected_year}")
        st.subheader(f"Top 10 states — {rank_label} {chart_context}")
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
        st.plotly_chart(fig_bar, width="stretch")
        st.caption("This ranking includes all states, even where earnings data is suppressed — "
                    "so the top state here may differ from the recommendation above.")


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
        st.caption(f"Showing data for: **{state_label}**" +
                    (" (your preferred state)" if target_state == home_state_abbr else " (top-ranked for this field)"))

        total_cost = row["median_net_cost"] * 4 if pd.notna(row["median_net_cost"]) else np.nan

        col1, col2, col3 = st.columns(3)
        with col1:
            cost_note = (f"≈ {fmt_money(row['median_net_cost'])}/year on average. Estimate assumes a "
                          f"standard 4-year completion; actual cost varies by student."
                          if pd.notna(row["median_net_cost"]) else "Net price data not available for this field/state.")
            metric_card("Est. total cost (4 yrs)", fmt_money(total_cost), cost_note)
        with col2:
            metric_card("Median federal loan debt", fmt_money(row["median_debt"]),
                         "Cumulative debt among students who borrowed. Excludes private loans and non-borrowers.")
        with col3:
            metric_card("Annual earnings (4 yrs after grad)", fmt_money(row["median_earnings_4yr"]),
                         "Median salary among graduates working and not enrolled in school when measured.")

        st.caption("**What this means:** the card below compares one year's salary, 5 years after "
                    "graduating, to the total federal debt taken on — a rough signal of how much of "
                    "that debt a single year's income could cover.")

        if pd.notna(row.get("median_roi_5yr")):
            roi = row["median_roi_5yr"]
            direction = "outpace" if roi >= 0 else "fall short of"
            payoff_color = GREEN if roi >= 0 else TERRACOTTA
            st.markdown(
                f"<div class='cluster-card'>"
                f"<p style='font-size:14px;color:{NEAR_BLACK};margin:0;'>"
                f"5 years after graduating, one year's salary {direction} total federal debt by "
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

            def bar_val_text(v, is_money=True):
                if pd.isna(v):
                    return 0, "No data"
                return v, (f"${v:,.0f}" if is_money else f"{v:,.0f}")

            metrics = ["Est. Total Cost (4 yrs)", "Median Federal Debt", "Annual Earnings (4 yrs after grad)"]
            state_total_cost = row["median_net_cost"] * 4 if pd.notna(row["median_net_cost"]) else np.nan
            nat_total_cost = nat_row["median_net_cost"] * 4 if pd.notna(nat_row["median_net_cost"]) else np.nan
            state_raw = [state_total_cost, row["median_debt"], row["median_earnings_4yr"]]
            nat_raw = [nat_total_cost, nat_row["median_debt"], nat_row["median_earnings_4yr"]]
            state_vals, state_texts = zip(*[bar_val_text(v) for v in state_raw])
            nat_vals, nat_texts = zip(*[bar_val_text(v) for v in nat_raw])

            fig_compare = go.Figure()
            fig_compare.add_trace(go.Bar(
                x=metrics, y=state_vals, text=state_texts, textposition="outside",
                name=state_label, marker_color=GREEN
            ))
            fig_compare.add_trace(go.Bar(
                x=metrics, y=nat_vals, text=nat_texts, textposition="outside",
                name="National median", marker_color=TAN
            ))
            fig_compare.update_layout(barmode="group", legend=dict(orientation="h", yanchor="bottom", y=1.02))
            fig_compare = style_fig(fig_compare, height=380)
            fig_compare.update_layout(yaxis_title="Amount (USD)")
            st.plotly_chart(fig_compare, width="stretch")
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

# ═══════════════════════════════════════════════════════════════════════════
# DEFERRED RERUN — triggered only after everything else (including the
# Field of study / Preferred state widgets) has already rendered once this
# pass. Keeps nav button colors snappy without cutting the script short
# before those widgets, which is what caused the sync bug.
# ═══════════════════════════════════════════════════════════════════════════
if tab_switch_requested:
    st.rerun()
