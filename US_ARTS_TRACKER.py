"""
MiPath — Arts Market Data Pipeline
Valentina Sanchez

Builds the arts market dataset from four public sources (College Scorecard,
BLS OEWS, U.S. Census, BEA) and exports the CSV files used by the MiPath
Streamlit app.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

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
STATE_ABBR_REVERSE = {v: k for k, v in STATE_ABBR.items()}

EXCLUDE_FIELDS = [
    'Area Studies.',
    'Ethnic, Cultural Minority, Gender, and Group Studies.'
]

ARTS_OCC_TITLES = [
    'Music Directors and Composers', 'Musicians and Singers',
    'Actors', 'Dancers', 'Choreographers', 'Producers and Directors'
]

CLUSTER_LABELS = {
    2: 'Major Arts Markets',
    0: 'Competitive Mid-Size Markets',
    1: 'Accessible Small Markets'
}


def build_arts_market_data(fos_path, inst_path, bls_files,
                             census_old_path, census_new_path, bea_path):
    """
    Runs the full arts market pipeline end to end.

    Returns
    -------
    state_summary : DataFrame — one row per state
    field_state_summary : DataFrame — one row per state x arts field
    """

    # College Scorecard (Field of Study + Institution)
    fos_cols = ['UNITID', 'INSTNM', 'CIPCODE', 'CIPDESC', 'CREDLEV',
                'IPEDSCOUNT1', 'EARN_MDN_1YR', 'EARN_MDN_4YR', 'EARN_MDN_5YR',
                'DEBT_ALL_STGP_ANY_MDN']
    fos = pd.read_csv(fos_path, usecols=fos_cols)

    inst_cols = ['UNITID', 'STABBR', 'CONTROL', 'NPT4_PUB', 'NPT4_PRIV']
    inst = pd.read_csv(inst_path, usecols=inst_cols)

    arts = fos[fos['CIPCODE'].astype(str).str.startswith('50')].copy()
    arts = arts[arts['CREDLEV'] == 3]
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

    # BLS employment
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

    print(f"Step 2 — BLS avg: {bls_avg.shape}")

    # Census population
    census_old = pd.read_excel(census_old_path, skiprows=3)
    census_old_clean = census_old[['Unnamed: 0', 2018, 2019]].copy()
    census_old_clean.columns = ['state', '2018', '2019']

    census_new = pd.read_excel(census_new_path, skiprows=3)
    census_new_clean = census_new[['Unnamed: 0', 2020, 2021, 2022]].copy()
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

    # BEA compensation
    bea = pd.read_csv(bea_path, encoding='latin-1')
    performing_arts_desc = [
        '  Performing arts companies ',
        '  Promoters of performing arts and similar events ',
        '  Agents/managers for artists ',
        '  Independent artists, writers, and performers '
    ]
    bea_filtered = bea[bea['Description'].isin(performing_arts_desc)].copy()
    bea_filtered = bea_filtered[['GeoName', '2018', '2019', '2020', '2021', '2022']]
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

    # Master dataset
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

    # State-level clustering
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

    cluster_check = state_clusters.groupby('cluster')[features].mean().round(2)
    print("Step 6 — Cluster summary:")
    print(cluster_check)

    state_clusters['cluster_label'] = state_clusters['cluster'].map(CLUSTER_LABELS)
    state_clusters['state_full_name'] = state_clusters['STABBR'].map(STATE_ABBR_REVERSE)

    print(f"Step 6 — State clusters: {state_clusters.shape}")

    # Top institution by headcount, per state
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

    # Final export tables
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


# ══════════════════════ ADJUST FOR NEW DATA LOADS ══════════════════════
# Update the file paths and bls_files years below to refresh with new data.
state_summary, field_state_summary = build_arts_market_data(
    fos_path='Most-Recent-Cohorts-Field-of-Study.csv',
    inst_path='Most-Recent-Cohorts-Institution.csv',
    bls_files={
        2018: 'state_M2018_dl.xlsx',
        2019: 'state_M2019_dl.xlsx',
        2020: 'state_M2020_dl.xlsx',
        2021: 'state_M2021_dl.xlsx',
        2022: 'state_M2022_dl.xlsx'
    },
    census_old_path='nst-est2020.xlsx',
    census_new_path='NST-EST2022-POP.xlsx',
    bea_path='SAACArtsComp__ALL_AREAS_2001_2023.csv'
)
# ═════════════════════════════════════════════════════════════════════

state_summary.to_csv('state_summary.csv', index=False)
field_state_summary.to_csv('field_state_summary.csv', index=False)

from google.colab import files
files.download('state_summary.csv')
files.download('field_state_summary.csv')
