import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# ── Setup ──────────────────────────────────────────
load_dotenv()
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except:
    DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    st.error("DATABASE_URL not found. Check your .env or secrets.toml file.")
    st.stop()

DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)

st.set_page_config(
    page_title="Stock Analytics Platform",
    page_icon="📈",
    layout="wide"
)

# ── Load Data ───────────────────────────────────────
@st.cache_data
def load_data():
    query = """
        SELECT 
            sp.ticker,
            sp.date::text AS date,
            sp.open::float AS open,
            sp.close::float AS close,
            sp.high::float AS high,
            sp.low::float AS low,
            sp.volume::bigint AS volume,
            c.company_name,
            s.sector_name
        FROM stock_prices sp
        JOIN companies c ON sp.ticker = c.ticker
        JOIN sectors s ON c.sector_id = s.sector_id
        ORDER BY sp.ticker, sp.date ASC
    """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    df['close'] = pd.to_numeric(df['close'])
    df['open'] = pd.to_numeric(df['open'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    df = df.sort_values(['ticker', 'date']).reset_index(drop=True)
    return df

df = load_data()

# ── Sidebar ─────────────────────────────────────────
st.sidebar.title("📈 Stock Analytics")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["Executive Summary", "Stock Analysis", "Sector Analysis"]
)

# ════════════════════════════════════════════════════
# PAGE 1 — Executive Summary
# ════════════════════════════════════════════════════
if page == "Executive Summary":
    st.title("📊 Executive Summary")
    st.markdown("Overview of all tracked stocks over the past year.")

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Companies", df['ticker'].nunique())
    col2.metric("Trading Days", df['date'].nunique())
    col3.metric("Total Volume Traded", f"{df['volume'].sum()/1e9:.1f}B")
    col4.metric("Sectors Tracked", df['sector_name'].nunique())

    st.markdown("---")

    # Stock price history — plot each ticker separately
    st.subheader("Stock Price History")
    fig = go.Figure()
    for t in sorted(df['ticker'].unique()):
        t_df = df[df['ticker'] == t].sort_values('date')
        fig.add_trace(go.Scatter(
            x=t_df['date'].tolist(),
            y=t_df['close'].tolist(),
            name=t,
            mode='lines',
            line=dict(width=1.5)
        ))
    fig.update_layout(
        title='Closing Price — All Stocks',
        xaxis_title='Date',
        yaxis_title='Close Price (USD)',
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Volume by stock
    st.subheader("Total Volume by Stock")
    vol = df.groupby('ticker')['volume'].sum().reset_index()
    fig2 = px.bar(
        vol, x='ticker', y='volume',
        color='volume',
        color_continuous_scale='Blues',
        labels={'volume': 'Total Volume'}
    )
    st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════════════════════
# PAGE 2 — Stock Analysis
# ════════════════════════════════════════════════════
elif page == "Stock Analysis":
    st.title("🔍 Stock Analysis")

    ticker = st.selectbox("Select a stock", sorted(df['ticker'].unique()))
    stock = df[df['ticker'] == ticker].copy()
    stock = stock.sort_values('date').reset_index(drop=True)

    # MA30
    stock['ma_30'] = stock['close'].rolling(30).mean()

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("52W High", f"${stock['high'].max():.2f}")
    col2.metric("52W Low", f"${stock['low'].min():.2f}")
    col3.metric("Avg Volume", f"{stock['volume'].mean()/1e6:.1f}M")

    first = stock.iloc[0]['close']
    last = stock.iloc[-1]['close']
    yearly_return = ((last - first) / first) * 100
    col4.metric("Yearly Return", f"{yearly_return:.2f}%")

    st.markdown("---")

    # Price vs MA30
    st.subheader(f"{ticker} — Price vs 30-Day Moving Average")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=stock['date'].tolist(),
        y=stock['close'].tolist(),
        name='Close Price',
        mode='lines',
        line=dict(width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=stock['date'].tolist(),
        y=stock['ma_30'].tolist(),
        name='MA30',
        mode='lines',
        line=dict(width=1.5, dash='dash')
    ))
    fig.update_layout(xaxis_title='Date', yaxis_title='Price (USD)')
    st.plotly_chart(fig, use_container_width=True)

    # Volume
    st.subheader(f"{ticker} — Daily Trading Volume")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=stock['date'].tolist(),
        y=stock['volume'].tolist(),
        name='Volume',
        marker_color='steelblue'
    ))
    fig2.update_layout(xaxis_title='Date', yaxis_title='Volume')
    st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════════════════════
# PAGE 3 — Sector Analysis
# ════════════════════════════════════════════════════
elif page == "Sector Analysis":
    st.title("🏭 Sector Analysis")

    # Yearly return per ticker
    records = []
    for t in df['ticker'].unique():
        t_df = df[df['ticker'] == t].sort_values('date')
        first_close = t_df.iloc[0]['close']
        last_close = t_df.iloc[-1]['close']
        sector = t_df.iloc[0]['sector_name']
        yearly_return = ((last_close - first_close) / first_close) * 100
        records.append({'ticker': t, 'sector_name': sector, 'yearly_return': yearly_return})

    returns = pd.DataFrame(records)

    # Avg return per sector
    sector_returns = returns.groupby('sector_name')['yearly_return'].mean().reset_index()
    sector_returns.columns = ['sector_name', 'avg_return']
    sector_returns = sector_returns.sort_values('avg_return', ascending=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average Yearly Return by Sector")
        fig = go.Figure(go.Bar(
            x=sector_returns['avg_return'].tolist(),
            y=sector_returns['sector_name'].tolist(),
            orientation='h',
            marker=dict(
                color=sector_returns['avg_return'].tolist(),
                colorscale='RdYlGn',
                showscale=True
            )
        ))
        fig.update_layout(xaxis_title='Avg Return (%)', yaxis_title='Sector')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Companies per Sector")
        sector_count = df.groupby('sector_name')['ticker'].nunique().reset_index()
        sector_count.columns = ['sector_name', 'company_count']
        fig2 = px.pie(
            sector_count,
            names='sector_name',
            values='company_count',
            hole=0.4
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Average Daily Volume by Sector")
    sector_vol = df.groupby('sector_name')['volume'].mean().reset_index()
    fig3 = go.Figure(go.Bar(
        x=sector_vol['sector_name'].tolist(),
        y=sector_vol['volume'].tolist(),
        marker_color='steelblue'
    ))
    fig3.update_layout(xaxis_title='Sector', yaxis_title='Avg Daily Volume')
    st.plotly_chart(fig3, use_container_width=True)
