import streamlit as st
import pandas as pd
import plotly.express as px
from src.forecast import ForecastModel, prepare_time_series
import numpy as np


st.set_page_config(page_title="Care Load Forecast", layout="wide")

st.title("Predictive Forecasting — Care Load & Placement Demand")

with st.sidebar:
    st.header("Data & Model")
    upload = st.file_uploader("Upload CSV (or leave blank to use project file)", type=["csv"])
    if upload is None:
        data_path = "HHS_Unaccompanied_Alien_Children_Program.csv"
    else:
        data_path = upload

    date_col = st.text_input("Date column name", value="Date")
    value_col = st.text_input("Target column name", value="Children in HHS Care")
    freq = st.selectbox("Frequency", options=["D", "W", "M"], index=0)
    method = st.selectbox("Forecast method", options=["Exp_Smoothing", "Moving_Average", "Naive"], index=0)
    horizon = st.slider("Forecast horizon (periods)", min_value=7, max_value=365, value=30, step=1)
    ma_window = st.slider("MA window (if using moving average)", min_value=2, max_value=60, value=7)

@st.cache_data
def load_data(path):
    if hasattr(path, 'read'):
        df = pd.read_csv(path)
    else:
        df = pd.read_csv(path)
    return df

df = None
try:
    df = load_data(data_path)
except Exception as e:
    st.error(f"Could not load data: {e}")

if df is not None:
    if date_col not in df.columns:
        st.warning(f"Date column '{date_col}' not found in data. Available columns: {list(df.columns)}")
    elif value_col not in df.columns:
        st.warning(f"Value column '{value_col}' not found in data. Available columns: {list(df.columns)}")
    else:
        series = prepare_time_series(df, date_col, value_col, freq)

        if series.empty:
            st.warning("No usable values were found after cleaning the selected date/value columns.")
        else:
            st.subheader("Historical data")
            plot_df = series.reset_index()
            plot_df.columns = [plot_df.columns[0], value_col]
            fig = px.line(plot_df, x=plot_df.columns[0], y=value_col, labels={value_col: value_col})
        st.plotly_chart(fig, use_container_width=True)

        fm = ForecastModel(series)
        if method == 'Naive' or method.lower() == 'naive':
            forecast = fm.fit_and_forecast('naive', horizon)
        elif method.lower().startswith('moving'):
            forecast = fm.fit_and_forecast('moving_average', horizon, window=ma_window)
        else:
            forecast = fm.fit_and_forecast('exp_smoothing', horizon)

        combined = pd.concat([series.rename('observed'), forecast['forecast'].rename('forecast')])

        st.subheader("Forecast")
        fig2 = px.line(combined.reset_index(), x=combined.index.name or 'index', y=combined.name if hasattr(combined, 'name') else combined.columns.tolist())
        # Plot observed + forecast
        obs = series.reset_index()
        fc = forecast.reset_index()
        obs.columns = ['ds', 'y']
        fc.columns = ['ds', 'y']
        fig3 = px.line()
        fig3.add_scatter(x=obs['ds'], y=obs['y'], mode='lines', name='observed')
        fig3.add_scatter(x=fc['ds'], y=fc['y'], mode='lines', name='forecast')
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")
        st.subheader("Forecast Data")
        st.dataframe(forecast.reset_index().rename(columns={'index': 'ds'}))

        st.info("This app provides quick baseline forecasts (naive, moving average, exponential smoothing). For production use, consider training more advanced models and validating using cross validation.")
