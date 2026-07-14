import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Tuple


def prepare_time_series(df: pd.DataFrame, date_col: str, value_col: str, freq: str) -> pd.Series:
    """Clean a dataframe into a unique-date time series suitable for forecasting."""
    work = df[[date_col, value_col]].copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")

    work[value_col] = (
        work[value_col]
        .astype(str)
        .str.replace(r"[,$]", "", regex=True)
        .str.replace(r"[^0-9.\-]", "", regex=True)
    )
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")

    work = work.dropna(subset=[date_col, value_col]).sort_values(date_col)
    work = work.groupby(date_col, as_index=False)[value_col].last()
    work = work.set_index(date_col)
    work.index = pd.DatetimeIndex(work.index)
    work = work[~work.index.duplicated(keep="last")]

    series = work[value_col].sort_index()
    series.name = value_col

    if freq == "D":
        series = series.asfreq("D").ffill()
    elif freq == "W":
        series = series.resample("W").sum()
    else:
        series = series.resample("M").sum()

    return series


class ForecastModel:
    """Simple forecasting helpers: naive, moving average, exponential smoothing."""

    def __init__(self, series: pd.Series):
        self.series = series.sort_index()

    def naive(self, horizon: int) -> pd.DataFrame:
        last = self.series.iloc[-1]
        idx = pd.date_range(start=self.series.index[-1] + (self.series.index[1] - self.series.index[0]), periods=horizon, freq=self.series.index.freq or pd.infer_freq(self.series.index))
        vals = np.repeat(last, horizon)
        return pd.DataFrame({"forecast": vals}, index=idx)

    def moving_average(self, horizon: int, window: int = 7) -> pd.DataFrame:
        ma = self.series.rolling(window=window, min_periods=1).mean()
        last = ma.iloc[-1]
        idx = pd.date_range(start=self.series.index[-1] + (self.series.index[1] - self.series.index[0]), periods=horizon, freq=self.series.index.freq or pd.infer_freq(self.series.index))
        vals = np.repeat(last, horizon)
        return pd.DataFrame({"forecast": vals}, index=idx)

    def exp_smoothing(self, horizon: int, seasonal: bool = False, seasonal_periods: int = None) -> pd.DataFrame:
        # Fit simple exponential smoothing / Holt-Winters
        try:
            if seasonal and seasonal_periods:
                model = ExponentialSmoothing(self.series, seasonal_periods=seasonal_periods, trend=None, seasonal='add', initialization_method='estimated')
            else:
                model = ExponentialSmoothing(self.series, trend=None, seasonal=None, initialization_method='estimated')
            fit = model.fit(optimized=True)
            pred = fit.forecast(horizon)
        except Exception:
            # fallback to naive if model fails
            pred = pd.Series(np.repeat(self.series.iloc[-1], horizon), index=pd.date_range(start=self.series.index[-1] + (self.series.index[1] - self.series.index[0]), periods=horizon, freq=self.series.index.freq or pd.infer_freq(self.series.index)))

        return pd.DataFrame({"forecast": pred})

    def fit_and_forecast(self, method: str, horizon: int, **kwargs) -> pd.DataFrame:
        method = method.lower()
        if method == 'naive':
            return self.naive(horizon)
        if method == 'moving_average' or method == 'ma':
            return self.moving_average(horizon, window=kwargs.get('window', 7))
        return self.exp_smoothing(horizon, seasonal=kwargs.get('seasonal', False), seasonal_periods=kwargs.get('seasonal_periods', None))
