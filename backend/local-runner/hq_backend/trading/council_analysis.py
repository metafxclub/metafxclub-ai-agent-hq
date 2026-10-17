"""Deterministic closed-bar technical and price-action feature calculations.

This module owns the Core20 formula version and feature families. Its inputs are
already-selected bar windows; it never selects a terminal, caches results, reads
runtime state, or dispatches a trade. Bridge cache and execution gates remain in
bridge_server.
"""

from __future__ import annotations

import math


AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION = (
    "metafx-deterministic-core20-price-action-v3"
)

AI_TRADE_COUNCIL_TECHNICAL_MODULES = (
    "sma_family",
    "ema_family",
    "rsi14",
    "macd_12_26_9",
    "stochastic_14_3_3",
    "atr14",
    "bollinger_20_2",
    "adx_dmi14",
    "cci20",
    "williams_r14",
    "roc12",
    "momentum10",
    "obv",
    "mfi14",
)

AI_TRADE_COUNCIL_PRICE_ACTION_MODULES = (
    "confirmed_swing_pivots",
    "support_resistance",
    "trendlines",
    "fibonacci_latest_confirmed_swing",
    "rsi_divergence",
    "macd_divergence",
)


def _technical_output_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return round(number, 8) if math.isfinite(number) else None


def _technical_ema_series(values: list[float], period: int) -> list[float | None]:
    """Return an SMA-seeded EMA series with explicit null warm-up values."""
    result: list[float | None] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return result
    seed = sum(values[:period]) / period
    if not math.isfinite(seed):
        return result
    result[period - 1] = seed
    multiplier = 2.0 / (period + 1.0)
    previous = seed
    for index in range(period, len(values)):
        previous = ((values[index] - previous) * multiplier) + previous
        if not math.isfinite(previous):
            return [None] * len(values)
        result[index] = previous
    return result


def _technical_ema(values: list[float], period: int) -> float | None:
    series = _technical_ema_series(values, period)
    return _technical_output_number(series[-1]) if series else None


def _technical_rsi_wilder_series(
    closes: list[float],
    period: int = 14,
) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    if period <= 0 or len(closes) < period + 1:
        return result
    changes = [closes[index] - closes[index - 1] for index in range(1, len(closes))]
    average_gain = sum(max(value, 0.0) for value in changes[:period]) / period
    average_loss = sum(max(-value, 0.0) for value in changes[:period]) / period

    def rsi_value(gain: float, loss: float) -> float:
        if loss == 0.0:
            return 100.0 if gain > 0.0 else 50.0
        relative_strength = gain / loss
        return 100.0 - (100.0 / (1.0 + relative_strength))

    result[period] = rsi_value(average_gain, average_loss)
    for index in range(period + 1, len(closes)):
        change = changes[index - 1]
        average_gain = (
            (average_gain * (period - 1)) + max(change, 0.0)
        ) / period
        average_loss = (
            (average_loss * (period - 1)) + max(-change, 0.0)
        ) / period
        current = rsi_value(average_gain, average_loss)
        if not math.isfinite(current):
            return [None] * len(closes)
        result[index] = current
    return result


def _technical_atr_wilder_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    if period <= 0 or len(closes) < period:
        return result
    true_ranges: list[float] = []
    for index in range(len(closes)):
        if index == 0:
            value = highs[index] - lows[index]
        else:
            previous_close = closes[index - 1]
            value = max(
                highs[index] - lows[index],
                abs(highs[index] - previous_close),
                abs(lows[index] - previous_close),
            )
        if not math.isfinite(value) or value < 0:
            return result
        true_ranges.append(value)
    previous = sum(true_ranges[:period]) / period
    result[period - 1] = previous
    for index in range(period, len(closes)):
        previous = ((previous * (period - 1)) + true_ranges[index]) / period
        if not math.isfinite(previous):
            return [None] * len(closes)
        result[index] = previous
    return result


def _technical_macd_signal_series(
    macd_line: list[float | None],
    period: int = 9,
) -> list[float | None]:
    result: list[float | None] = [None] * len(macd_line)
    observed = [
        (index, float(value))
        for index, value in enumerate(macd_line)
        if value is not None and math.isfinite(float(value))
    ]
    if period <= 0 or len(observed) < period:
        return result
    seed = sum(value for _, value in observed[:period]) / period
    seed_index = observed[period - 1][0]
    result[seed_index] = seed
    multiplier = 2.0 / (period + 1.0)
    previous = seed
    for index, value in observed[period:]:
        previous = ((value - previous) * multiplier) + previous
        if not math.isfinite(previous):
            return [None] * len(macd_line)
        result[index] = previous
    return result


def _technical_sma_series(
    values: list[float],
    period: int,
) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return result
    rolling = sum(values[:period])
    result[period - 1] = rolling / period
    for index in range(period, len(values)):
        rolling += values[index] - values[index - period]
        result[index] = rolling / period
    return result


def _technical_stochastic_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    lookback: int = 14,
    slowing: int = 3,
    signal: int = 3,
) -> tuple[list[float | None], list[float | None]]:
    raw: list[float | None] = [None] * len(closes)
    for index in range(lookback - 1, len(closes)):
        high = max(highs[index - lookback + 1:index + 1])
        low = min(lows[index - lookback + 1:index + 1])
        raw[index] = 50.0 if high == low else ((closes[index] - low) / (high - low)) * 100.0

    def smoothed(source: list[float | None], period: int) -> list[float | None]:
        output: list[float | None] = [None] * len(source)
        for index in range(period - 1, len(source)):
            window = source[index - period + 1:index + 1]
            if all(value is not None for value in window):
                output[index] = sum(float(value) for value in window) / period
        return output

    percent_k = smoothed(raw, slowing)
    return percent_k, smoothed(percent_k, signal)


def _technical_bollinger_series(
    closes: list[float],
    period: int = 20,
    deviations: float = 2.0,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    middle = _technical_sma_series(closes, period)
    upper: list[float | None] = [None] * len(closes)
    lower: list[float | None] = [None] * len(closes)
    for index in range(period - 1, len(closes)):
        window = closes[index - period + 1:index + 1]
        mean = float(middle[index])
        variance = sum((value - mean) ** 2 for value in window) / period
        standard_deviation = math.sqrt(max(variance, 0.0))
        upper[index] = mean + (deviations * standard_deviation)
        lower[index] = mean - (deviations * standard_deviation)
    return middle, upper, lower


def _technical_adx_dmi_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    size = len(closes)
    adx: list[float | None] = [None] * size
    plus_di: list[float | None] = [None] * size
    minus_di: list[float | None] = [None] * size
    if period <= 0 or size <= period:
        return adx, plus_di, minus_di
    true_ranges = [0.0] * size
    plus_dm = [0.0] * size
    minus_dm = [0.0] * size
    for index in range(1, size):
        true_ranges[index] = max(
            highs[index] - lows[index],
            abs(highs[index] - closes[index - 1]),
            abs(lows[index] - closes[index - 1]),
        )
        upward = highs[index] - highs[index - 1]
        downward = lows[index - 1] - lows[index]
        plus_dm[index] = upward if upward > downward and upward > 0.0 else 0.0
        minus_dm[index] = downward if downward > upward and downward > 0.0 else 0.0
    smoothed_tr = sum(true_ranges[1:period + 1])
    smoothed_plus = sum(plus_dm[1:period + 1])
    smoothed_minus = sum(minus_dm[1:period + 1])
    dx: list[float | None] = [None] * size
    for index in range(period, size):
        if index > period:
            smoothed_tr = smoothed_tr - (smoothed_tr / period) + true_ranges[index]
            smoothed_plus = smoothed_plus - (smoothed_plus / period) + plus_dm[index]
            smoothed_minus = smoothed_minus - (smoothed_minus / period) + minus_dm[index]
        if smoothed_tr <= 0.0:
            plus = minus = 0.0
        else:
            plus = 100.0 * smoothed_plus / smoothed_tr
            minus = 100.0 * smoothed_minus / smoothed_tr
        plus_di[index] = plus
        minus_di[index] = minus
        denominator = plus + minus
        dx[index] = 0.0 if denominator == 0.0 else 100.0 * abs(plus - minus) / denominator
    first_adx_index = (period * 2) - 1
    if size > first_adx_index:
        seed_values = [float(value) for value in dx[period:first_adx_index + 1] if value is not None]
        if len(seed_values) == period:
            previous = sum(seed_values) / period
            adx[first_adx_index] = previous
            for index in range(first_adx_index + 1, size):
                current_dx = dx[index]
                if current_dx is None:
                    continue
                previous = ((previous * (period - 1)) + current_dx) / period
                adx[index] = previous
    return adx, plus_di, minus_di


def _technical_cci_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 20,
) -> list[float | None]:
    typical = [(highs[index] + lows[index] + closes[index]) / 3.0 for index in range(len(closes))]
    result: list[float | None] = [None] * len(closes)
    for index in range(period - 1, len(closes)):
        window = typical[index - period + 1:index + 1]
        mean = sum(window) / period
        mean_deviation = sum(abs(value - mean) for value in window) / period
        result[index] = 0.0 if mean_deviation == 0.0 else (typical[index] - mean) / (0.015 * mean_deviation)
    return result


def _technical_williams_r_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    for index in range(period - 1, len(closes)):
        high = max(highs[index - period + 1:index + 1])
        low = min(lows[index - period + 1:index + 1])
        result[index] = -50.0 if high == low else -100.0 * (high - closes[index]) / (high - low)
    return result


def _technical_rate_series(
    closes: list[float],
    period: int,
    *,
    base: float,
) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    for index in range(period, len(closes)):
        previous = closes[index - period]
        if previous > 0.0:
            result[index] = (closes[index] / previous) * base
            if base == 100.0:
                result[index] -= 100.0
    return result


def _technical_momentum_series(
    closes: list[float],
    period: int = 10,
) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    for index in range(period, len(closes)):
        previous = closes[index - period]
        if previous > 0.0:
            result[index] = (closes[index] / previous) * 100.0
    return result


def _technical_obv_series(
    closes: list[float],
    volumes: list[float],
) -> list[float | None]:
    if not closes:
        return []
    result: list[float | None] = [0.0] * len(closes)
    for index in range(1, len(closes)):
        previous = float(result[index - 1])
        if closes[index] > closes[index - 1]:
            result[index] = previous + volumes[index]
        elif closes[index] < closes[index - 1]:
            result[index] = previous - volumes[index]
        else:
            result[index] = previous
    return result


def _technical_mfi_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    volumes: list[float],
    period: int = 14,
) -> list[float | None]:
    size = len(closes)
    result: list[float | None] = [None] * size
    typical = [(highs[index] + lows[index] + closes[index]) / 3.0 for index in range(size)]
    positive = [0.0] * size
    negative = [0.0] * size
    for index in range(1, size):
        flow = typical[index] * volumes[index]
        if typical[index] > typical[index - 1]:
            positive[index] = flow
        elif typical[index] < typical[index - 1]:
            negative[index] = flow
    for index in range(period, size):
        positive_sum = sum(positive[index - period + 1:index + 1])
        negative_sum = sum(negative[index - period + 1:index + 1])
        if negative_sum == 0.0:
            result[index] = 100.0 if positive_sum > 0.0 else 50.0
        else:
            result[index] = 100.0 - (100.0 / (1.0 + (positive_sum / negative_sum)))
    return result


def _technical_indicator_snapshot_uncached(bars: list[dict]) -> dict:
    """Calculate reproducible indicators from one exact closed-bar window."""
    times: list[int | None] = []
    closes: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    volumes: list[float] = []
    payload_valid = bool(bars)
    for item in bars:
        if not isinstance(item, dict):
            payload_valid = False
            break
        open_price = _technical_output_number(item.get("open"))
        close = _technical_output_number(item.get("close"))
        high = _technical_output_number(item.get("high"))
        low = _technical_output_number(item.get("low"))
        volume = _technical_output_number(item.get("volume"))
        timestamp = item.get("time")
        if (
            open_price is None
            or not isinstance(timestamp, int)
            or isinstance(timestamp, bool)
            or timestamp <= 0
            or close is None
            or high is None
            or low is None
            or volume is None
            or min(open_price, close, high, low) <= 0
            or volume < 0
            or high < max(open_price, close)
            or low > min(open_price, close)
            or high < low
        ):
            payload_valid = False
            break
        times.append(timestamp)
        closes.append(close)
        highs.append(high)
        lows.append(low)
        volumes.append(volume)

    empty_series: list[dict] = []
    if not payload_valid:
        return {
            "available": False,
            "reasonCode": "invalid_closed_bar_payload",
            "basis": "backend_calculated_closed_bars_only",
            "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
            "moduleCount": len(AI_TRADE_COUNCIL_TECHNICAL_MODULES),
            "modules": list(AI_TRADE_COUNCIL_TECHNICAL_MODULES),
            "barCount": len(bars),
            "latestClosedBarTime": None,
            "latestClose": None,
            "sma20": None,
            "sma50": None,
            "sma200": None,
            "ema9": None,
            "ema12": None,
            "ema20": None,
            "ema26": None,
            "ema50": None,
            "ema200": None,
            "rsi14": None,
            "atr14": None,
            "atrPercent": None,
            "macdLine": None,
            "macdSignal": None,
            "macdHistogram": None,
            "stochasticK": None,
            "stochasticD": None,
            "bollingerMiddle": None,
            "bollingerUpper": None,
            "bollingerLower": None,
            "adx14": None,
            "plusDI14": None,
            "minusDI14": None,
            "cci20": None,
            "williamsR14": None,
            "roc12": None,
            "momentum10": None,
            "obv": None,
            "mfi14": None,
            "volumeMA20": None,
            "averageVolume20": None,
            "closeVsEma20": None,
            "trendState": "UNAVAILABLE",
            "series": empty_series,
        }

    def latest(series: list[float | None]) -> float | None:
        return _technical_output_number(series[-1]) if series else None

    sma20_series = _technical_sma_series(closes, 20)
    sma50_series = _technical_sma_series(closes, 50)
    sma200_series = _technical_sma_series(closes, 200)
    ema9_series = _technical_ema_series(closes, 9)
    ema12_series = _technical_ema_series(closes, 12)
    ema20_series = _technical_ema_series(closes, 20)
    ema26_series = _technical_ema_series(closes, 26)
    ema50_series = _technical_ema_series(closes, 50)
    ema200_series = _technical_ema_series(closes, 200)
    rsi14_series = _technical_rsi_wilder_series(closes, 14)
    atr14_series = _technical_atr_wilder_series(highs, lows, closes, 14)
    stochastic_k_series, stochastic_d_series = _technical_stochastic_series(
        highs,
        lows,
        closes,
    )
    (
        bollinger_middle_series,
        bollinger_upper_series,
        bollinger_lower_series,
    ) = _technical_bollinger_series(closes)
    adx14_series, plus_di14_series, minus_di14_series = _technical_adx_dmi_series(
        highs,
        lows,
        closes,
    )
    cci20_series = _technical_cci_series(highs, lows, closes)
    williams_r14_series = _technical_williams_r_series(highs, lows, closes)
    roc12_series = _technical_rate_series(closes, 12, base=100.0)
    momentum10_series = _technical_momentum_series(closes, 10)
    obv_series = _technical_obv_series(closes, volumes)
    mfi14_series = _technical_mfi_series(highs, lows, closes, volumes)
    volume_ma20_series = _technical_sma_series(volumes, 20)
    macd_line_series: list[float | None] = [
        (ema12_series[index] - ema26_series[index])
        if ema12_series[index] is not None and ema26_series[index] is not None
        else None
        for index in range(len(closes))
    ]
    macd_signal_series = _technical_macd_signal_series(macd_line_series, 9)
    macd_histogram_series: list[float | None] = [
        (macd_line_series[index] - macd_signal_series[index])
        if macd_line_series[index] is not None
        and macd_signal_series[index] is not None
        else None
        for index in range(len(closes))
    ]
    latest_close = closes[-1]
    sma20 = latest(sma20_series)
    sma50 = latest(sma50_series)
    sma200 = latest(sma200_series)
    ema9 = latest(ema9_series)
    ema12 = latest(ema12_series)
    ema20 = latest(ema20_series)
    ema26 = latest(ema26_series)
    ema50 = latest(ema50_series)
    ema200 = latest(ema200_series)
    rsi14 = latest(rsi14_series)
    atr14 = latest(atr14_series)
    macd_line = latest(macd_line_series)
    macd_signal = latest(macd_signal_series)
    macd_histogram = latest(macd_histogram_series)
    stochastic_k = latest(stochastic_k_series)
    stochastic_d = latest(stochastic_d_series)
    bollinger_middle = latest(bollinger_middle_series)
    bollinger_upper = latest(bollinger_upper_series)
    bollinger_lower = latest(bollinger_lower_series)
    adx14 = latest(adx14_series)
    plus_di14 = latest(plus_di14_series)
    minus_di14 = latest(minus_di14_series)
    cci20 = latest(cci20_series)
    williams_r14 = latest(williams_r14_series)
    roc12 = latest(roc12_series)
    momentum10 = latest(momentum10_series)
    obv = latest(obv_series)
    mfi14 = latest(mfi14_series)
    volume_ma20 = latest(volume_ma20_series)
    atr_percent = (
        _technical_output_number((atr14 / latest_close) * 100.0)
        if atr14 is not None and latest_close > 0
        else None
    )
    if ema20 is None or ema50 is None:
        trend_state = "UNAVAILABLE"
    elif (
        latest_close > ema20 > ema50
        and (ema200 is None or ema50 > ema200)
    ):
        trend_state = "BULLISH"
    elif (
        latest_close < ema20 < ema50
        and (ema200 is None or ema50 < ema200)
    ):
        trend_state = "BEARISH"
    else:
        trend_state = "MIXED"
    available = all(
        value is not None
        for value in (
            ema20,
            ema50,
            rsi14,
            atr14,
            macd_line,
            stochastic_k,
            bollinger_middle,
            adx14,
            cci20,
            williams_r14,
            roc12,
            momentum10,
            obv,
            mfi14,
        )
    )
    return {
        "available": available,
        "reasonCode": "ready" if available else "indicator_warmup_incomplete",
        "basis": "backend_calculated_closed_bars_only",
        "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
        "moduleCount": len(AI_TRADE_COUNCIL_TECHNICAL_MODULES),
        "modules": list(AI_TRADE_COUNCIL_TECHNICAL_MODULES),
        "barCount": len(bars),
        "latestClosedBarTime": bars[-1].get("time") if bars else None,
        "latestClose": _technical_output_number(latest_close),
        "sma20": sma20,
        "sma50": sma50,
        "sma200": sma200,
        "ema9": ema9,
        "ema12": ema12,
        "ema20": ema20,
        "ema26": ema26,
        "ema50": ema50,
        "ema200": ema200,
        "rsi14": rsi14,
        "atr14": atr14,
        "atrPercent": atr_percent,
        "macdLine": macd_line,
        "macdSignal": macd_signal,
        "macdHistogram": macd_histogram,
        "stochasticK": stochastic_k,
        "stochasticD": stochastic_d,
        "bollingerMiddle": bollinger_middle,
        "bollingerUpper": bollinger_upper,
        "bollingerLower": bollinger_lower,
        "adx14": adx14,
        "plusDI14": plus_di14,
        "minusDI14": minus_di14,
        "cci20": cci20,
        "williamsR14": williams_r14,
        "roc12": roc12,
        "momentum10": momentum10,
        "obv": obv,
        "mfi14": mfi14,
        "volumeMA20": volume_ma20,
        "averageVolume20": volume_ma20,
        "closeVsEma20": (
            "above"
            if latest_close > ema20
            else "below"
            if latest_close < ema20
            else "equal"
        ) if ema20 is not None else None,
        "trendState": trend_state,
        "series": [
            {
                "time": times[index],
                "sma20": _technical_output_number(sma20_series[index]),
                "sma50": _technical_output_number(sma50_series[index]),
                "sma200": _technical_output_number(sma200_series[index]),
                "ema9": _technical_output_number(ema9_series[index]),
                "ema20": _technical_output_number(ema20_series[index]),
                "ema50": _technical_output_number(ema50_series[index]),
                "ema200": _technical_output_number(ema200_series[index]),
                "rsi14": _technical_output_number(rsi14_series[index]),
                "atr14": _technical_output_number(atr14_series[index]),
                "macdLine": _technical_output_number(macd_line_series[index]),
                "macdSignal": _technical_output_number(macd_signal_series[index]),
                "macdHistogram": _technical_output_number(
                    macd_histogram_series[index]
                ),
                "stochasticK": _technical_output_number(stochastic_k_series[index]),
                "stochasticD": _technical_output_number(stochastic_d_series[index]),
                "bollingerMiddle": _technical_output_number(
                    bollinger_middle_series[index]
                ),
                "bollingerUpper": _technical_output_number(
                    bollinger_upper_series[index]
                ),
                "bollingerLower": _technical_output_number(
                    bollinger_lower_series[index]
                ),
                "adx14": _technical_output_number(adx14_series[index]),
                "plusDI14": _technical_output_number(plus_di14_series[index]),
                "minusDI14": _technical_output_number(minus_di14_series[index]),
                "cci20": _technical_output_number(cci20_series[index]),
                "williamsR14": _technical_output_number(
                    williams_r14_series[index]
                ),
                "roc12": _technical_output_number(roc12_series[index]),
                "momentum10": _technical_output_number(momentum10_series[index]),
                "obv": _technical_output_number(obv_series[index]),
                "mfi14": _technical_output_number(mfi14_series[index]),
                "volumeMA20": _technical_output_number(volume_ma20_series[index]),
            }
            for index in range(len(closes))
        ],
    }


def _price_action_confirmed_pivots(
    bars: list[dict],
    *,
    left: int = 3,
    right: int = 3,
) -> tuple[list[dict], list[dict]]:
    """Return only pivots confirmed by already-closed bars to their right."""
    highs = [float(item["high"]) for item in bars]
    lows = [float(item["low"]) for item in bars]
    high_pivots: list[dict] = []
    low_pivots: list[dict] = []
    for index in range(left, len(bars) - right):
        high = highs[index]
        low = lows[index]
        if all(high > highs[offset] for offset in range(index - left, index)) and all(
            high > highs[offset] for offset in range(index + 1, index + right + 1)
        ):
            high_pivots.append({
                "index": index,
                "time": bars[index]["time"],
                "confirmedAtTime": bars[index + right]["time"],
                "price": _technical_output_number(high),
                "type": "HIGH",
            })
        if all(low < lows[offset] for offset in range(index - left, index)) and all(
            low < lows[offset] for offset in range(index + 1, index + right + 1)
        ):
            low_pivots.append({
                "index": index,
                "time": bars[index]["time"],
                "confirmedAtTime": bars[index + right]["time"],
                "price": _technical_output_number(low),
                "type": "LOW",
            })
    return high_pivots, low_pivots


def _price_action_cluster_levels(
    pivots: list[dict],
    *,
    current_price: float,
    threshold: float,
    side: str,
) -> list[dict]:
    clusters: list[dict] = []
    for pivot in pivots:
        price = float(pivot["price"])
        matching = next(
            (
                cluster
                for cluster in clusters
                if abs(price - float(cluster["price"])) <= threshold
            ),
            None,
        )
        if matching is None:
            clusters.append({
                "price": price,
                "touches": 1,
                "firstTime": pivot["time"],
                "lastTime": pivot["time"],
                "lastConfirmedAtTime": pivot["confirmedAtTime"],
                "pivotTimes": [pivot["time"]],
            })
            continue
        touches = int(matching["touches"])
        matching["price"] = ((float(matching["price"]) * touches) + price) / (touches + 1)
        matching["touches"] = touches + 1
        matching["lastTime"] = pivot["time"]
        matching["lastConfirmedAtTime"] = pivot["confirmedAtTime"]
        matching["pivotTimes"].append(pivot["time"])
    if side == "support":
        clusters = [cluster for cluster in clusters if float(cluster["price"]) <= current_price]
    else:
        clusters = [cluster for cluster in clusters if float(cluster["price"]) >= current_price]
    clusters.sort(
        key=lambda cluster: (
            abs(float(cluster["price"]) - current_price),
            -int(cluster["touches"]),
        )
    )
    return [
        {
            **cluster,
            "price": _technical_output_number(cluster["price"]),
            "distancePercent": _technical_output_number(
                abs(float(cluster["price"]) - current_price) / current_price * 100.0
            ),
        }
        for cluster in clusters[:6]
    ]


def _price_action_trendline(
    pivots: list[dict],
    *,
    kind: str,
    latest_index: int,
    latest_time: int,
) -> dict | None:
    if len(pivots) < 2:
        return None
    first, second = pivots[-2], pivots[-1]
    distance = int(second["index"]) - int(first["index"])
    if distance <= 0:
        return None
    slope = (float(second["price"]) - float(first["price"])) / distance
    epsilon = max(abs(float(second["price"])) * 1e-10, 1e-10)
    direction = "RISING" if slope > epsilon else "FALLING" if slope < -epsilon else "FLAT"
    projected = float(second["price"]) + slope * (latest_index - int(second["index"]))
    return {
        "kind": kind,
        "direction": direction,
        "first": dict(first),
        "second": dict(second),
        "slopePerBar": _technical_output_number(slope),
        "projectedPrice": _technical_output_number(projected),
        "validThroughTime": latest_time,
    }


def _price_action_latest_fibonacci(
    high_pivots: list[dict],
    low_pivots: list[dict],
) -> dict:
    pivots = sorted([*high_pivots, *low_pivots], key=lambda item: int(item["index"]))
    if len(pivots) < 2:
        return {
            "available": False,
            "direction": None,
            "from": None,
            "to": None,
            "range": None,
            "levels": [],
        }
    end = pivots[-1]
    start = next(
        (pivot for pivot in reversed(pivots[:-1]) if pivot["type"] != end["type"]),
        None,
    )
    if start is None:
        return {
            "available": False,
            "direction": None,
            "from": None,
            "to": None,
            "range": None,
            "levels": [],
        }
    direction = "UP" if start["type"] == "LOW" and end["type"] == "HIGH" else "DOWN"
    price_range = abs(float(end["price"]) - float(start["price"]))
    ratios = (
        (0.0, "0%"),
        (0.236, "23.6%"),
        (0.382, "38.2%"),
        (0.5, "50%"),
        (0.618, "61.8%"),
        (0.786, "78.6%"),
        (1.0, "100%"),
    )
    return {
        "available": price_range > 0.0,
        "direction": direction,
        "from": dict(start),
        "to": dict(end),
        "range": _technical_output_number(price_range),
        "levels": [
            {
                "ratio": ratio,
                "label": label,
                "price": _technical_output_number(
                    float(end["price"])
                    + ((float(start["price"]) - float(end["price"])) * ratio)
                ),
            }
            for ratio, label in ratios
        ],
    }


def _price_action_regular_divergence(
    pivots: list[dict],
    oscillator_series: list[float | None],
    *,
    oscillator: str,
    bullish: bool,
) -> dict | None:
    observed = [
        pivot
        for pivot in pivots
        if 0 <= int(pivot["index"]) < len(oscillator_series)
        and oscillator_series[int(pivot["index"])] is not None
    ]
    if len(observed) < 2:
        return None
    first, second = observed[-2], observed[-1]
    first_value = float(oscillator_series[int(first["index"])] or 0.0)
    second_value = float(oscillator_series[int(second["index"])] or 0.0)
    confirmed = (
        float(second["price"]) < float(first["price"])
        and second_value > first_value
        if bullish
        else float(second["price"]) > float(first["price"])
        and second_value < first_value
    )
    if not confirmed:
        return None

    def evidence(pivot: dict, value: float) -> dict:
        return {
            "index": pivot["index"],
            "time": pivot["time"],
            "confirmedAtTime": pivot["confirmedAtTime"],
            "price": pivot["price"],
            "oscillatorValue": _technical_output_number(value),
        }

    return {
        "kind": "REGULAR_BULLISH" if bullish else "REGULAR_BEARISH",
        "oscillator": oscillator,
        "first": evidence(first, first_value),
        "second": evidence(second, second_value),
        "detectedAtTime": second["confirmedAtTime"],
    }


def _price_action_features_snapshot_uncached(
    bars: list[dict],
    technical: dict,
) -> dict:
    series = technical.get("series") if isinstance(technical.get("series"), list) else []
    if technical.get("reasonCode") == "invalid_closed_bar_payload" or not bars or len(series) != len(bars):
        return {
            "available": False,
            "reasonCode": "invalid_closed_bar_payload",
            "basis": "backend_calculated_confirmed_closed_bars_only",
            "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
            "moduleCount": len(AI_TRADE_COUNCIL_PRICE_ACTION_MODULES),
            "modules": list(AI_TRADE_COUNCIL_PRICE_ACTION_MODULES),
            "barCount": len(bars),
            "pivotConfig": {"leftBars": 3, "rightBars": 3, "confirmedOnly": True},
            "swings": {"highs": [], "lows": [], "latestHigh": None, "latestLow": None},
            "supportResistance": {"supports": [], "resistances": [], "threshold": None},
            "trendlines": {"support": None, "resistance": None},
            "fibonacci": _price_action_latest_fibonacci([], []),
            "divergences": {
                "rsi": {"bullish": None, "bearish": None},
                "macd": {"bullish": None, "bearish": None},
            },
        }
    high_pivots, low_pivots = _price_action_confirmed_pivots(bars)
    latest_price = float(bars[-1]["close"])
    latest_atr = technical.get("atr14")
    threshold = max(
        (float(latest_atr) * 0.35) if isinstance(latest_atr, (int, float)) else 0.0,
        latest_price * 0.001,
    )
    rsi_series = [item.get("rsi14") if isinstance(item, dict) else None for item in series]
    macd_series = [item.get("macdLine") if isinstance(item, dict) else None for item in series]
    fibonacci = _price_action_latest_fibonacci(high_pivots, low_pivots)
    ready = bool(high_pivots and low_pivots)
    return {
        "available": ready,
        "reasonCode": "ready" if ready else "confirmed_pivot_warmup_incomplete",
        "basis": "backend_calculated_confirmed_closed_bars_only",
        "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
        "moduleCount": len(AI_TRADE_COUNCIL_PRICE_ACTION_MODULES),
        "modules": list(AI_TRADE_COUNCIL_PRICE_ACTION_MODULES),
        "barCount": len(bars),
        "latestClosedBarTime": bars[-1]["time"],
        "pivotConfig": {"leftBars": 3, "rightBars": 3, "confirmedOnly": True},
        "swings": {
            "highs": [dict(item) for item in high_pivots[-24:]],
            "lows": [dict(item) for item in low_pivots[-24:]],
            "latestHigh": dict(high_pivots[-1]) if high_pivots else None,
            "latestLow": dict(low_pivots[-1]) if low_pivots else None,
        },
        "supportResistance": {
            "supports": _price_action_cluster_levels(
                low_pivots,
                current_price=latest_price,
                threshold=threshold,
                side="support",
            ),
            "resistances": _price_action_cluster_levels(
                high_pivots,
                current_price=latest_price,
                threshold=threshold,
                side="resistance",
            ),
            "threshold": _technical_output_number(threshold),
        },
        "trendlines": {
            "support": _price_action_trendline(
                low_pivots,
                kind="support",
                latest_index=len(bars) - 1,
                latest_time=bars[-1]["time"],
            ),
            "resistance": _price_action_trendline(
                high_pivots,
                kind="resistance",
                latest_index=len(bars) - 1,
                latest_time=bars[-1]["time"],
            ),
        },
        "fibonacci": fibonacci,
        "divergences": {
            "rsi": {
                "bullish": _price_action_regular_divergence(
                    low_pivots,
                    rsi_series,
                    oscillator="RSI14",
                    bullish=True,
                ),
                "bearish": _price_action_regular_divergence(
                    high_pivots,
                    rsi_series,
                    oscillator="RSI14",
                    bullish=False,
                ),
            },
            "macd": {
                "bullish": _price_action_regular_divergence(
                    low_pivots,
                    macd_series,
                    oscillator="MACD_LINE",
                    bullish=True,
                ),
                "bearish": _price_action_regular_divergence(
                    high_pivots,
                    macd_series,
                    oscillator="MACD_LINE",
                    bullish=False,
                ),
            },
        },
    }

