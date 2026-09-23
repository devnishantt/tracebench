import math
from decimal import Decimal, localcontext

from .values import number


def quantile(values: list[float], probability: float) -> float | None:
    if not 0 <= probability <= 1:
        raise ValueError("Quantile probability must be between zero and one")
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low, high = math.floor(position), math.ceil(position)
    # Weighted interpolation avoids subtracting opposite very large endpoints.
    return ordered[low] * (1 - (position - low)) + ordered[high] * (position - low)


def numeric_summary(values: list[str]) -> dict[str, float | None] | None:
    if not values:
        return None
    decimals = [number(value.strip()) for value in values]
    with localcontext() as context:
        context.prec = 60
        mean = sum(decimals) / Decimal(len(decimals))
        variance = sum((value - mean) ** 2 for value in decimals) / Decimal(len(decimals))
        stddev = variance.sqrt()
    floats = [float(value) for value in decimals]

    def finite(value: Decimal) -> float | None:
        return float(value) if math.isfinite(float(value)) else None

    return {
        "minimum": min(floats),
        "maximum": max(floats),
        "mean": finite(mean),
        "stddev": finite(stddev),
        "p25": quantile(floats, 0.25),
        "median": quantile(floats, 0.5),
        "p75": quantile(floats, 0.75),
    }
