import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ═══════════════════════════════════════════════════════════════════════════
# UPDATE GUIDE — read this before re-running with new data
# ═══════════════════════════════════════════════════════════════════════════
# 1. Download new files from the same 4 sources (Scorecard, BLS, Census, BEA)
# 2. Update the file paths / bls_files dict at the bottom of this script
# 3. If BLS/Census/BEA cover a NEW year range, update the year lists in
#    Steps 2, 3, and 4 (marked TO UPDATE below)
# 4. Re-run the whole script top to bottom
# 5. DO NOT touch STATE_ABBR, EXCLUDE_FIELDS, ARTS_OCC_TITLES, or
#    CLUSTER_LABELS unless your scope itself changes — these encode
#    project decisions, not data structure
# ═══════════════════════════════════════════════════════════════════════════

# ── Static lookups — DO NOT CHANGE on data refresh ─────────────────────────
STATE_ABBR = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY'
}
# Note: BLS files also include District of Columbia and Puerto Rico.
# These are intentionally excluded — scope is defined as the 50 U.S. states.
STATE_ABBR_REVERSE = {v: k for k, v in STATE_ABBR.items()}

# CIP 50 subfields that are NOT actually arts programs, confirmed during EDA
EXCLUDE_FIELDS = [
    'Area Studies.',
    'Ethnic, Cultural Minority, Gender, and Group Studies.'
]

# SOC 27-2 occupation titles used to represent "arts jobs" — a scope decision,
# not a data artifact. Changing this changes what counts as an arts job.
ARTS_OCC_TITLES = [
    'Music Directors and Composers', 'Musicians and Singers',
    'Actors', 'Dancers', 'Choreographers', 'Producers and Directors'
]

# Cluster number -> label mapping. NOTE: KMeans cluster numbers (0, 1, 2) are
# NOT guaranteed to stay in this order on re-run with new data — always check
# the printed cluster_summary after re-running and update these numbers if
# the cluster characteristics have shifted which number is which.
CLUSTER_LABELS = {
    2: 'Major Arts Markets',
    0: 'Competitive Mid-Size Markets',
    1: 'Accessible Small Markets'
}


def build_arts_market_data(fos_path, inst_path, bls_files,
                             census_old_path, census_new_path, bea_path):
    """
    Runs the full arts market pipeline end to end.

    Parameters
    ----------
    fos_path : str — path to College Scorecard Field of Study CSV
    inst_path : str — path to College Scorecard Institution CSV
    bls_files : dict — {year: filepath} for BLS state Excel files
    census_old_path : str — path to older Census file
    census_new_path : str — path to newer Census file
    bea_path : str — path to BEA arts compensation CSV

    Returns
    -------
    state_summary : DataFrame — one row per state, cluster + top institution
    field_state_summary : DataFrame — one row per state x arts field
    """

    # ── Step 1: College Scorecard (Field of Study + Institution) ──────────
    # TO UPDATE: none of the column names below should change year to year,
    # Scorecard's schema is stable. Just point fos_path/inst_path at new files.
    fos_cols = ['UNITID', 'INSTNM', 'CIPCODE', 'CIPDESC', 'CREDLEV',
                'IPEDSCOUNT1', 'EARN_MDN_1YR', 'EARN_MDN_4YR', 'EARN_MDN_5YR',
                'DEBT_ALL_STGP_ANY_MDN']
    fos = pd.read_csv(fos_path, usecols=fos_cols)

    inst_cols = ['UNITID', 'STABBR', 'CONTROL', 'NPT4_PUB', 'NPT4_PRIV']
    inst = pd.read_csv(inst_path, usecols=inst_cols)

    arts = fos[fos['CIPCODE'].astype(str).str.startswith('50')].copy()
    arts = arts[arts['CREDLEV'] == 3]  # bachelor's only — scope decision, don't change
    arts = arts.merge(inst, on='UNITID', how='left')

    arts['net_cost'] = arts['NPT4_PUB'].combine_first(arts['NPT4_PRIV'])
    arts = arts.drop(columns=['NPT4_PUB', 'NPT4_PRIV'])

    numeric_cols = ['EARN_MDN_1YR', 'EARN_MDN_4YR', 'EARN_MDN_5YR',
                     'DEBT_ALL_STGP_ANY_MDN', 'net_cost']
    for col in numeric_cols:
        arts[col] = pd.to_numeric(arts[col], errors='coerce')

    arts['roi_5yr'] = arts['EARN_MDN_5YR'] - arts['DEBT_ALL_STGP_ANY_MDN']
    arts = arts[~arts['CIPDESC'].isin(EXCLUDE_FIELDS)]

    print(f"Step 1 — Scorecard arts base: {arts.shape}")

    # ── Step 2: BLS employment ─────────────────────────────────────────────
    # TO UPDATE: the keys of bls_files (the years) — passed in as a parameter,
    # no code change needed here unless BLS changes its column naming again.
    bls_all = []
    for year, file in bls_files.items():
        df = pd.read_excel(file)
        df.columns = df.columns.str.upper()
        if 'STATE' not in df.columns and 'AREA_TITLE' in df.columns:
            df = df.rename(columns={'AREA_TITLE': 'STATE'})
        df = df[df['OCC_CODE'].str.startswith('27-2')]
        df = df[df['OCC_TITLE'].isin(ARTS_OCC_TITLES)]
        df = df[['STATE', 'OCC_CODE', 'TOT_EMP']].copy()
        df['year'] = year
        bls_all.append(df)

    bls = pd.concat(bls_all, ignore_index=True)
    bls['TOT_EMP'] = pd.to_numeric(bls['TOT_EMP'], errors='coerce')

    bls_avg = bls.groupby('STATE')['TOT_EMP'].mean().reset_index()
    bls_avg.columns = ['STABBR', 'avg_arts_jobs']
    bls_avg['STABBR'] = bls_avg['STABBR'].map(STATE_ABBR)

    print(f"Step 2 — BLS avg: {bls_avg.shape}, "
          f"{bls_avg['STABBR'].isna().sum()} states not matched "
          f"(expected: DC + Puerto Rico)")

    # ── Step 3: Census population ──────────────────────────────────────────
    # TO UPDATE: the column year lists ['2018', '2019'] and [2020, 2021, 2022]
    # below need to match whatever years your two new Census files actually
    # cover — Census sometimes splits files differently across year ranges.
    census_old = pd.read_excel(census_old_path, skiprows=3)
    census_old_clean = census_old[['Unnamed: 0', 2018, 2019]].copy()  # TO UPDATE if years shift
    census_old_clean.columns = ['state', '2018', '2019']

    census_new = pd.read_excel(census_new_path, skiprows=3)
    census_new_clean = census_new[['Unnamed: 0', 2020, 2021, 2022]].copy()  # TO UPDATE if years shift
    census_new_clean.columns = ['state', '2020', '2021', '2022']

    remove = ['United States', 'Northeast', 'Midwest', 'South', 'West']
    for df in [census_old_clean, census_new_clean]:
        df.drop(df[df['state'].isin(remove)].index, inplace=True)
        df.dropna(subset=['state'], inplace=True)
        df['state'] = df['state'].str.replace('.', '', regex=False).str.strip()

    census = census_old_clean.merge(census_new_clean, on='state', how='inner')
    census = census.melt(id_vars='state', var_name='year', value_name='population')
    census['year'] = census['year'].astype(int)

    census_avg = census.groupby('state')['population'].mean().reset_index()
    census_avg.columns = ['state_name', 'avg_population']
    census_avg['STABBR'] = census_avg['state_name'].map(STATE_ABBR)

    print(f"Step 3 — Census: {census_avg.shape}")

    # ── Step 4: BEA compensation ───────────────────────────────────────────
    # TO UPDATE: the year columns ['2018', '2019', '2020', '2021', '2022']
    # below — BEA's file usually has all years in one CSV, so you'd add new
    # year columns to this list rather than swap the file path entirely.
    bea = pd.read_csv(bea_path, encoding='latin-1')
    performing_arts_desc = [
        '  Performing arts companies ',
        '  Promoters of performing arts and similar events ',
        '  Agents/managers for artists ',
        '  Independent artists, writers, and performers '
    ]
    bea_filtered = bea[bea['Description'].isin(performing_arts_desc)].copy()
    bea_filtered = bea_filtered[['GeoName', '2018', '2019', '2020', '2021', '2022']]  # TO UPDATE
    bea_long = bea_filtered.melt(id_vars='GeoName', var_name='year',
                                   value_name='arts_compensation')
    bea_long['arts_compensation'] = pd.to_numeric(bea_long['arts_compensation'],
                                                     errors='coerce')

    remove_bea = ['United States', 'New England', 'Mideast', 'Great Lakes',
                  'Plains', 'Southeast', 'Southwest', 'Rocky Mountain', 'Far West']
    bea_long = bea_long[~bea_long['GeoName'].isin(remove_bea)]

    bea_avg = bea_long.groupby('GeoName')['arts_compensation'].mean().reset_index()
    bea_avg.columns = ['state_name', 'avg_arts_compensation']
    bea_avg['STABBR'] = bea_avg['state_name'].map(STATE_ABBR)

    print(f"Step 4 — BEA: {bea_avg.shape}")

    # ── Step 5: Build master dataset — DO NOT CHANGE on data refresh ───────
    master = arts.merge(bls_avg, on='STABBR', how='left')
    master = master.merge(bea_avg[['STABBR', 'avg_arts_compensation']],
                            on='STABBR', how='left')
    master = master.merge(census_avg[['STABBR', 'avg_population']],
                            on='STABBR', how='left')
    master = master[master['STABBR'].isin(STATE_ABBR.values())]

    master['jobs_per_100k'] = (master['avg_arts_jobs'] / master['avg_population']) * 100000

    grads_by_state = master.groupby('STABBR')['IPEDSCOUNT1'].sum().reset_index()
    grads_by_state.columns = ['STABBR', 'total_grads_by_state']
    master = master.merge(grads_by_state, on='STABBR', how='left')
    master['jobs_per_grad'] = master['avg_arts_jobs'] / master['total_grads_by_state']

    round_cols = master.select_dtypes(include='number').columns
    master[round_cols] = master[round_cols].round(2)

    print(f"Step 5 — Master dataset: {master.shape}")

    # ── Step 6: State-level clustering — DO NOT CHANGE feature list ────────
    # If you add/remove features here, the elbow method should be re-run
    # manually to confirm K=3 is still the right number of clusters.
    state_clusters = master.groupby('STABBR').agg(
        avg_arts_jobs=('avg_arts_jobs', 'mean'),
        avg_earnings=('EARN_MDN_4YR', 'median'),
        avg_debt=('DEBT_ALL_STGP_ANY_MDN', 'median'),
        avg_cost=('net_cost', 'median'),
        avg_compensation=('avg_arts_compensation', 'mean'),
        jobs_per_grad=('jobs_per_grad', 'mean')
    ).dropna().reset_index()

    features = ['avg_arts_jobs', 'avg_earnings', 'avg_debt',
                'avg_cost', 'avg_compensation', 'jobs_per_grad']
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(state_clusters[features])

    km = KMeans(n_clusters=3, random_state=42, n_init=10)
    state_clusters['cluster'] = km.fit_predict(X_scaled)

    # ⚠️ CHECK THIS on every re-run: cluster numbers can shuffle with new data.
    # Print the summary below and confirm CLUSTER_LABELS still maps correctly
    # before trusting the labels.
    cluster_check = state_clusters.groupby('cluster')[features].mean().round(2)
    print("Step 6 — Cluster summary (verify CLUSTER_LABELS still matches):")
    print(cluster_check)

    state_clusters['cluster_label'] = state_clusters['cluster'].map(CLUSTER_LABELS)
    state_clusters['state_full_name'] = state_clusters['STABBR'].map(STATE_ABBR_REVERSE)

    print(f"Step 6 — State clusters: {state_clusters.shape}")

    # ── Step 7: Top institution by headcount, per state ─────────────────────
    # DO NOT CHANGE the selection rule (headcount, public + private included)
    # unless you deliberately revisit that methodology decision.
    inst_headcount = master.groupby(['STABBR', 'UNITID', 'INSTNM', 'CONTROL']).agg(
        total_arts_headcount=('IPEDSCOUNT1', 'sum'),
        net_cost=('net_cost', 'median')
    ).reset_index()

    top_inst_by_state = inst_headcount.loc[
        inst_headcount.groupby('STABBR')['total_arts_headcount'].idxmax()
    ].reset_index(drop=True)

    control_labels = {1: 'Public', 2: 'Private nonprofit', 3: 'Private for-profit'}
    top_inst_by_state['control_type'] = top_inst_by_state['CONTROL'].map(control_labels)

    print(f"Step 7 — Top institution per state: {top_inst_by_state.shape}")

    # ── Step 8: Final export tables — DO NOT CHANGE structure ──────────────
    # These are the two files the Streamlit app reads. If you change column
    # names here, you must also update the app code that references them.
    state_summary = state_clusters.merge(
        top_inst_by_state[['STABBR', 'INSTNM', 'control_type',
                            'total_arts_headcount', 'net_cost']],
        on='STABBR', how='left'
    ).rename(columns={'net_cost': 'top_inst_net_cost', 'INSTNM': 'top_inst_name'})

    field_state_summary = master.groupby(['STABBR', 'CIPDESC']).agg(
        median_earnings_4yr=('EARN_MDN_4YR', 'median'),
        median_debt=('DEBT_ALL_STGP_ANY_MDN', 'median'),
        median_net_cost=('net_cost', 'median'),
        median_roi_5yr=('roi_5yr', 'median')
    ).reset_index()
    field_state_summary = field_state_summary.merge(
        state_clusters[['STABBR', 'cluster_label', 'jobs_per_grad', 'avg_arts_jobs']],
        on='STABBR', how='left'
    )
    field_state_summary['CIPDESC'] = field_state_summary['CIPDESC'].str.replace(
        '.', '', regex=False)

    print(f"Step 8 — Final exports: state_summary {state_summary.shape}, "
          f"field_state_summary {field_state_summary.shape}")

    return state_summary, field_state_summary


# ═══════════════════════════════════════════════════════════════════════════
# RUN THE PIPELINE — this is the only block you touch to refresh data
# ═══════════════════════════════════════════════════════════════════════════
state_summary, field_state_summary = build_arts_market_data(
    fos_path='Most-Recent-Cohorts-Field-of-Study.csv',      # TO UPDATE
    inst_path='Most-Recent-Cohorts-Institution.csv',         # TO UPDATE
    bls_files={                                               # TO UPDATE
        2018: 'state_M2018_dl.xlsx',
        2019: 'state_M2019_dl.xlsx',
        2020: 'state_M2020_dl.xlsx',
        2021: 'state_M2021_dl.xlsx',
        2022: 'state_M2022_dl.xlsx'
    },
    census_old_path='nst-est2020.xlsx',                       # TO UPDATE
    census_new_path='NST-EST2022-POP.xlsx',                   # TO UPDATE
    bea_path='SAACArtsComp__ALL_AREAS_2001_2023.csv'          # TO UPDATE
)

state_summary.to_csv('state_summary.csv', index=False)
field_state_summary.to_csv('field_state_summary.csv', index=False)

from google.colab import files
files.download('state_summary.csv')
files.download('field_state_summary.csv')
