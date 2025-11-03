import streamlit as st
import pandas as pd
import sqlite3
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from pathlib import Path
import altair as alt
# --- Page Configuration ---
st.set_page_config(
    page_title="Quant Analytics Dashboard",
    layout="wide"
)

# --- Database ---
DB_NAME = 'trades.db'

@st.cache_data(ttl=10) # Cache data for 10 seconds
def load_data(db_path=DB_NAME):
    """Loads all tick data from SQLite."""
    if not Path(db_path).exists():
        return pd.DataFrame() # Return empty if DB doesn't exist
        
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT ts, symbol, price FROM ticks", conn)
    except pd.errors.DatabaseError:
        return pd.DataFrame() # Return empty if table isn't ready
    finally:
        conn.close()
        
    if df.empty:
        return pd.DataFrame()
        
    df['ts'] = pd.to_datetime(df['ts'], format='ISO8601')
    return df

# REPLACE the old get_pair_data function with this new one:

@st.cache_data(ttl=10)
def get_pair_data(df):
    """Pivots the raw data into a two-symbol dataframe."""
    if df.empty or 'symbol' not in df.columns:
        return pd.DataFrame()
        
    # Filter data first
    btc_df = df[df['symbol'] == 'btcusdt'].set_index('ts')['price']
    eth_df = df[df['symbol'] == 'ethusdt'].set_index('ts')['price']

    # Handle duplicate timestamps by averaging prices at the same timestamp
    # This is crucial as many trades can happen in the same millisecond
    if not btc_df.index.is_unique:
        btc = btc_df.groupby(btc_df.index).mean()
    else:
        btc = btc_df

    if not eth_df.index.is_unique:
        eth = eth_df.groupby(eth_df.index).mean()
    else:
        eth = eth_df
    
    if btc.empty or eth.empty:
        return pd.DataFrame()
        
    # Combine, forward-fill to align timestamps, and drop any remaining NaNs
    pair_df = pd.concat([btc, eth], axis=1, keys=['btc_price', 'eth_price'])
    pair_df = pair_df.ffill().dropna()
    return pair_df
# --- Analytics Functions ---

@st.cache_resource # Cache the model/results
def calculate_analytics(_pair_df_resampled, window):
    """Calculates all required analytics."""
    
    # 1. OLS Hedge Ratio
    y = _pair_df_resampled['eth_price']
    x = sm.add_constant(_pair_df_resampled['btc_price'])
    model = sm.OLS(y, x).fit()
    hedge_ratio = model.params['btc_price']
    
    # 2. Spread
    spread = _pair_df_resampled['eth_price'] - hedge_ratio * _pair_df_resampled['btc_price']
    
    # 3. Z-Score (using rolling mean/std of the spread)
    spread_mean = spread.rolling(window=window).mean()
    spread_std = spread.rolling(window=window).std()
    z_score = (spread - spread_mean) / spread_std
    
    # 4. Rolling Correlation
    rolling_corr = _pair_df_resampled['btc_price'].rolling(window=window).corr(_pair_df_resampled['eth_price'])
    
    # 5. ADF Test on the spread
    # We drop NaNs from the spread for the test
    adf_test_result = adfuller(spread.dropna())
    
    return {
        'hedge_ratio': hedge_ratio,
        'spread': spread,
        'z_score': z_score,
        'rolling_corr': rolling_corr,
        'adf_p_value': adf_test_result[1],
        'model_summary': model.summary()
    }

# --- Main Application ---
st.title("📈 Live Quant Analytics Dashboard")

# --- 1. Sidebar Controls ---
st.sidebar.title("Controls")
timeframe = st.sidebar.selectbox(
    "Select Timeframe", 
    ("1s", "1m", "5m"), 
    index=1,
    help="Resampling frequency for analytics. '1s' can be noisy."
)
rolling_window = st.sidebar.slider(
    "Rolling Window", 
    min_value=10, 
    max_value=200, 
    value=50,
    help="Window size for rolling Z-Score and Correlation."
)
alert_z_score = st.sidebar.number_input(
    "Z-Score Alert Threshold", 
    min_value=0.5, 
    max_value=5.0, 
    value=2.0, 
    step=0.1
)

# --- 2. Load & Process Data ---
raw_df = load_data()

if raw_df.empty:
    st.warning("No data found. Is `ingest.py` running? Waiting for data...")
    st.stop()

pair_df = get_pair_data(raw_df)

if pair_df.empty:
    st.warning("Waiting for data from both symbols (BTC & ETH) to arrive...")
    st.stop()

# Resample based on selection
# We use .last() to get the last price in the window.
resampled_df = pair_df.resample(timeframe).last().dropna()

if resampled_df.empty or len(resampled_df) < rolling_window:
    st.warning(f"Waiting for more data. Need at least {rolling_window} data points for a '{timeframe}' window...")
    st.stop()

# --- 3. Run Analytics ---
analytics = calculate_analytics(resampled_df, rolling_window)

# Add analytics to our dataframe for easy plotting
resampled_df['spread'] = analytics['spread']
resampled_df['z_score'] = analytics['z_score']
resampled_df['rolling_corr'] = analytics['rolling_corr']

# --- 4. Display Dashboard ---

# Live Stats & Alerting
st.header("Live Stats")
current_z = resampled_df['z_score'].iloc[-1]

col1, col2, col3 = st.columns(3)
col1.metric("Latest BTC Price", f"${resampled_df['btc_price'].iloc[-1]:,.2f}")
col2.metric("Latest ETH Price", f"${resampled_df['eth_price'].iloc[-1]:,.2f}")
col3.metric("Current Z-Score", f"{current_z:.2f}")

# Alerting [cite: 19]
if abs(current_z) > alert_z_score:
    st.error(f"🚨 ALERT: Z-Score ({current_z:.2f}) has breached threshold ({alert_z_score})")

# Tabs for charts
st.header("Analytics Charts")
tab1, tab2, tab3, tab4 = st.tabs(["Prices", "Spread & Z-Score", "Correlation", "Regression Stats"])

with tab1:
    st.subheader("BTC & ETH Prices")
    st.line_chart(resampled_df[['btc_price', 'eth_price']])

# REPLACE THE 'with tab2:' BLOCK AGAIN WITH THIS:
with tab2:
    st.subheader("Pair Spread (ETH - HedgeRatio * BTC)")
    st.line_chart(resampled_df['spread'])
    
    st.subheader("Spread Z-Score")
    
    # --- START OF ALTAIR CHART CODE ---
    
    # We need to reset the index for Altair to use 'ts' as a column
    z_score_df = resampled_df.reset_index()
    
    # Create the base Z-Score line chart
    z_chart = alt.Chart(z_score_df).mark_line().encode(
        x=alt.X('ts', title='Timestamp'),
        y=alt.Y('z_score', title='Z-Score'),
        tooltip=['ts', 'z_score']
    ).interactive() # .interactive() gives zoom/pan

    # Create the DataFrame for the threshold lines
    threshold_df = pd.DataFrame({
        'threshold': [alert_z_score, -alert_z_score]
    })
    
    # Create the red dashed lines
    # --- THIS IS THE CORRECTED LINE ---
    rules = alt.Chart(threshold_df).mark_rule(color='red', strokeDash=[3,3]).encode(
        y=alt.Y('threshold', title='Z-Score')
    )

    # Combine the Z-Score chart and the threshold lines
    st.altair_chart(z_chart + rules, use_container_width=True)
    # --- END OF ALTAIR CHART CODE ---

with tab3:
    st.subheader(f"{rolling_window}-Period Rolling Correlation")
    st.line_chart(resampled_df['rolling_corr'])

with tab4:
    st.subheader("OLS Regression & ADF Test")
    st.metric("OLS Hedge Ratio", f"{analytics['hedge_ratio']:.4f}")
    
    st.subheader("ADF Test for Stationarity (on Spread)")
    st.metric("ADF Test P-Value", f"{analytics['adf_p_value']:.4f}")
    if analytics['adf_p_value'] < 0.05:
        st.success("Spread appears to be stationary (p < 0.05)")
    else:
        st.warning("Spread may not be stationary (p >= 0.05)")
    
    with st.expander("View OLS Model Summary"):
        st.text(analytics['model_summary'])

# --- 5. Data Export  ---
st.sidebar.header("Data Export")
@st.cache_data # Cache the CSV conversion
def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

csv_data = convert_df_to_csv(resampled_df)

st.sidebar.download_button(
    label="Download Analytics Data (CSV)",
    data=csv_data,
    file_name=f"analytics_{timeframe}_{pd.Timestamp.now():%Y%m%d_%H%M%S}.csv",
    mime="text/csv",
)