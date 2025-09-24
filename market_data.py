"""Utility helpers for fetching market data, correlations and on-chain metrics."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Dict, Iterable, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

BINANCE_BASE_URL = "https://api.binance.com/api/v3/klines"
BLOCKCHAIN_BASE_URL = "https://api.blockchain.info/charts"

BINANCE_INTERVAL_TO_MINUTES = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "2h": 120,
    "4h": 240,
    "6h": 360,
    "8h": 480,
    "12h": 720,
    "1d": 1440,
    "3d": 3 * 1440,
    "1w": 7 * 1440,
    "1M": 30 * 1440,
}

DEFAULT_ONCHAIN_METRICS = {
    "hash_rate": "hash-rate",
    "difficulty": "difficulty",
    "n_transactions": "n-transactions",
    "estimated_transaction_volume": "estimated-transaction-volume",
    "utxo_count": "utxo-count",
}


@dataclass
class DatasetStatus:
    """Simple container describing the state of a retrieved dataset."""

    status: str
    detail: str
    points: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {"status": self.status, "detail": self.detail, "points": self.points}


def _safe_json_request(url: str) -> Tuple[object, DatasetStatus]:
    """Fetch JSON data from ``url`` while handling networking problems gracefully."""

    try:
        with urlopen(url, timeout=30) as response:  # nosec B310 - url controlled internally
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:  # pragma: no cover - network errors depend on environment
        return None, DatasetStatus(status="error", detail=f"HTTP {exc.code}: {exc.reason}")
    except URLError as exc:  # pragma: no cover - network errors depend on environment
        return None, DatasetStatus(status="error", detail=str(exc.reason))

    if isinstance(payload, dict) and payload.get("code"):
        detail = payload.get("msg", "erro inesperado na API")
        return None, DatasetStatus(status="error", detail=detail)

    return payload, DatasetStatus(status="ok", detail="dados carregados")


def fetch_binance_klines(symbol: str, interval: str, limit: int = 500) -> Tuple[pd.DataFrame, DatasetStatus]:
    """Fetch OHLCV candles from Binance for ``symbol`` and ``interval``."""

    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    url = f"{BINANCE_BASE_URL}?{urlencode(params)}"
    payload, status = _safe_json_request(url)
    if payload is None:
        return pd.DataFrame(), status

    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ]
    df = pd.DataFrame(payload, columns=columns)
    if df.empty:
        return df, DatasetStatus(status="empty", detail="sem candles retornados")

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    numeric_cols = ["open", "high", "low", "close", "volume", "quote_asset_volume"]
    df[numeric_cols] = df[numeric_cols].astype(float)
    df["number_of_trades"] = df["number_of_trades"].astype(int)
    df.set_index("close_time", inplace=True)
    df = df[["open", "high", "low", "close", "volume", "number_of_trades"]]
    return df, DatasetStatus(status="ok", detail="candles carregados", points=len(df))


def fetch_multi_interval_market_data(
    symbols: Iterable[str], intervals: Iterable[str], limit: int = 500
) -> Tuple[Dict[str, Dict[str, pd.DataFrame]], Dict[str, Dict[str, DatasetStatus]]]:
    """Fetch candles for several symbols and intervals returning a nested mapping."""

    market_data: Dict[str, Dict[str, pd.DataFrame]] = {}
    metadata: Dict[str, Dict[str, DatasetStatus]] = {}

    for symbol in symbols:
        symbol = symbol.upper()
        market_data[symbol] = {}
        metadata[symbol] = {}
        for interval in intervals:
            df, status = fetch_binance_klines(symbol, interval, limit=limit)
            market_data[symbol][interval] = df
            metadata[symbol][interval] = status
    return market_data, metadata


def _closest_daily_frame(data_by_interval: Dict[str, pd.DataFrame]) -> pd.Series:
    """Return a daily close series using the most appropriate interval available."""

    if "1d" in data_by_interval and not data_by_interval["1d"].empty:
        return data_by_interval["1d"]["close"].copy()

    # fall back to the highest granularity available
    available = [
        (interval, df)
        for interval, df in data_by_interval.items()
        if not df.empty and interval in BINANCE_INTERVAL_TO_MINUTES
    ]
    if not available:
        return pd.Series(dtype=float)

    interval, df = sorted(available, key=lambda item: BINANCE_INTERVAL_TO_MINUTES[item[0]])[0]
    rule = "1D"
    resampled = df["close"].resample(rule).last().dropna()
    resampled.name = df["close"].name
    return resampled


def calculate_gold_btc_correlation(
    btc_data: Dict[str, pd.DataFrame],
    gold_data: Dict[str, pd.DataFrame],
    window: int = 30,
) -> pd.DataFrame:
    """Compute the rolling correlation between BTC and Gold returns."""

    btc_series = _closest_daily_frame(btc_data)
    gold_series = _closest_daily_frame(gold_data)

    if btc_series.empty or gold_series.empty:
        return pd.DataFrame()

    merged = (
        pd.concat([btc_series.rename("btc_close"), gold_series.rename("gold_close")], axis=1)
        .dropna()
        .sort_index()
    )
    merged["btc_return"] = merged["btc_close"].pct_change()
    merged["gold_return"] = merged["gold_close"].pct_change()
    merged["rolling_corr"] = merged["btc_return"].rolling(window).corr(merged["gold_return"])
    return merged.dropna(subset=["rolling_corr"])[["rolling_corr"]]


def _fetch_blockchain_chart(chart_name: str, timespan_days: int) -> Tuple[pd.DataFrame, DatasetStatus]:
    params = {"timespan": f"{timespan_days}days", "format": "json", "sampled": "false"}
    url = f"{BLOCKCHAIN_BASE_URL}/{chart_name}?{urlencode(params)}"
    payload, status = _safe_json_request(url)
    if payload is None:
        return pd.DataFrame(), status

    values = payload.get("values", []) if isinstance(payload, dict) else []
    if not values:
        return pd.DataFrame(), DatasetStatus(status="empty", detail="sem valores retornados")

    df = pd.DataFrame(values)
    df["date"] = pd.to_datetime(df["x"], unit="s")
    df.set_index("date", inplace=True)
    df = df[["y"]].rename(columns={"y": chart_name})
    return df, DatasetStatus(status="ok", detail="dados on-chain carregados", points=len(df))


def fetch_onchain_metrics(
    metrics: Iterable[str] | None = None, timespan_days: int = 180
) -> Tuple[pd.DataFrame, Dict[str, DatasetStatus]]:
    """Retrieve several Blockchain.com chart metrics as a consolidated dataframe."""

    metrics = list(metrics) if metrics is not None else list(DEFAULT_ONCHAIN_METRICS.keys())
    frames: List[pd.DataFrame] = []
    metadata: Dict[str, DatasetStatus] = {}

    for metric in metrics:
        chart_name = DEFAULT_ONCHAIN_METRICS.get(metric, metric)
        df, status = _fetch_blockchain_chart(chart_name, timespan_days)
        metadata[metric] = status
        if df.empty:
            continue
        frames.append(df.rename(columns={chart_name: metric}))

    if not frames:
        return pd.DataFrame(), metadata

    combined = pd.concat(frames, axis=1).sort_index()
    return combined, metadata


def dataframe_to_records(df: pd.DataFrame, value_label: str | None = None) -> List[Dict[str, object]]:
    """Convert a dataframe with a DateTimeIndex into records ready for JSON responses."""

    if df.empty:
        return []

    df_copy = df.copy()
    df_copy.index = df_copy.index.to_series().dt.tz_localize(None)
    df_copy.reset_index(inplace=True)
    df_copy.rename(columns={"index": "timestamp"}, inplace=True)
    if value_label and df_copy.shape[1] == 2:
        df_copy.rename(columns={df_copy.columns[1]: value_label}, inplace=True)
    df_copy["timestamp"] = df_copy["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return df_copy.to_dict(orient="records")


def build_market_overview(
    intervals: Iterable[str] | None = None,
    lookback_limit: int = 500,
    onchain_metrics: Iterable[str] | None = None,
    correlation_window: int = 30,
) -> Dict[str, object]:
    """Aggregate market data, correlation insights and on-chain metrics."""

    intervals = list(intervals) if intervals is not None else ["4h", "1d"]

    market_data, market_status = fetch_multi_interval_market_data(
        symbols=["BTCUSDT", "XAUUSDT"], intervals=intervals, limit=lookback_limit
    )
    correlation_df = calculate_gold_btc_correlation(
        btc_data=market_data.get("BTCUSDT", {}),
        gold_data=market_data.get("XAUUSDT", {}),
        window=correlation_window,
    )
    correlation_records = dataframe_to_records(correlation_df, value_label="rolling_corr")
    correlation_summary = None
    if correlation_records:
        latest_value = correlation_df["rolling_corr"].iloc[-1]
        correlation_summary = {
            "latest": float(latest_value),
            "is_negative": bool(latest_value < 0),
            "window": correlation_window,
        }

    onchain_df, onchain_status = fetch_onchain_metrics(
        metrics=onchain_metrics, timespan_days=max(180, correlation_window * 4)
    )

    return {
        "market_data": {
            symbol: {
                interval: dataframe_to_records(df, value_label="close")
                for interval, df in intervals_map.items()
            }
            for symbol, intervals_map in market_data.items()
        },
        "correlation": {
            "records": correlation_records,
            "summary": correlation_summary,
        },
        "onchain": {
            "records": dataframe_to_records(onchain_df),
            "metrics": list(onchain_df.columns) if not onchain_df.empty else [],
        },
        "metadata": {
            "market_data": {
                symbol: {interval: status.to_dict() for interval, status in status_map.items()}
                for symbol, status_map in market_status.items()
            },
            "onchain": {metric: status.to_dict() for metric, status in onchain_status.items()},
        },
    }
