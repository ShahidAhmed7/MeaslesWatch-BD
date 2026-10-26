"""Small count baselines with explicit training cutoffs and failure states."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import warnings

import numpy as np
import pandas as pd
from scipy.stats import nbinom, poisson
from statsmodels.discrete.discrete_model import NegativeBinomial, Poisson
from statsmodels.stats.diagnostic import acorr_ljungbox


def design(dates, origin):
    dates = pd.DatetimeIndex(dates)
    origin = pd.Timestamp(origin)
    t = ((dates.year - origin.year) * 12 + dates.month - origin.month) / 12
    phase = 2 * np.pi * (dates.month - 1) / 12
    return np.column_stack([np.ones(len(dates)), t, np.sin(phase), np.cos(phase)])


def checked_history(dates, counts):
    dates = pd.DatetimeIndex(dates)
    counts = np.asarray(counts, dtype=float)
    if len(dates) != len(counts) or len(dates) < 12:
        raise ValueError("A complete dated training window of at least 12 months is required")
    if dates.has_duplicates or not dates.equals(pd.date_range(dates[0], periods=len(dates), freq="MS")):
        raise ValueError("Training months must be unique, ordered and contiguous; no imputation")
    if not np.isfinite(counts).all() or (counts < 0).any() or (counts != np.floor(counts)).any():
        raise ValueError("Training counts must be observed nonnegative integers")
    return dates, counts


@dataclass
class CountFit:
    model: str
    dates: pd.DatetimeIndex
    y: np.ndarray
    params: np.ndarray | None = None
    alpha: float | None = None
    status: str = "ok"
    diagnostics: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)

    def means(self, targets):
        targets = pd.DatetimeIndex(targets)
        if len(targets) and (targets <= self.dates[-1]).any():
            raise ValueError("Every prediction month must follow the training cutoff")
        if self.status != "ok":
            return None
        if self.model == "seasonal_naive":
            index = {d: float(y) for d, y in zip(self.dates, self.y)}
            return np.array([index.get(d - pd.DateOffset(years=1), np.nan) for d in targets])
        if self.model == "seasonal_reference":
            return np.array([self.y[self.dates.month == d.month].mean() for d in targets])
        if self.params is None:
            return np.zeros(len(targets))
        with np.errstate(over="ignore", invalid="ignore"):
            return np.exp(design(targets, self.dates[0]) @ self.params)

    def predict(self, target, observed):
        target = pd.Timestamp(target)
        means = self.means([target])
        result = {
            "model": self.model, "month": target.strftime("%Y-%m"),
            "training_start": self.dates[0].strftime("%Y-%m"),
            "training_end": self.dates[-1].strftime("%Y-%m"),
            "training_months": len(self.dates), "observed": int(observed),
            "status": self.status, "expected": None, "lower_95": None,
            "upper_95": None, "upper_99": None, "anomaly": None,
            "tail_probability": None, "negative_log_probability": None,
            "zero_predictive_probability": False, "mase_scale": None,
            "alpha": self.alpha, "warnings": self.warnings,
        }
        if len(self.y) > 12:
            scale = float(np.mean(np.abs(self.y[12:] - self.y[:-12])))
            result["mase_scale"] = scale if scale > 0 else None
        if means is None:
            return result
        mu = float(means[0])
        if not math.isfinite(mu) or mu < 0:
            result["status"] = "unavailable_nonfinite_mean"
            return result
        result["expected"] = mu
        if self.model == "seasonal_naive":
            result["predictive_scope"] = "point_comparator_no_predictive_distribution"
            return result
        alpha = self.alpha or 0.0
        distribution = (nbinom(1 / alpha, 1 / (1 + alpha * mu))
                        if alpha > 1e-8 and mu > 0 else poisson(mu))
        quantiles = distribution.ppf([0.025, 0.975, 0.99])
        if not np.isfinite(quantiles).all():
            result["status"] = "unavailable_nonfinite_quantiles"
            return result
        logp = float(distribution.logpmf(observed))
        result.update({
            "lower_95": int(quantiles[0]), "upper_95": int(quantiles[1]),
            "upper_99": int(quantiles[2]), "anomaly": bool(observed > quantiles[2]),
            "tail_probability": float(distribution.sf(observed - 1)),
            "negative_log_probability": -logp if math.isfinite(logp) else None,
            "zero_predictive_probability": not math.isfinite(logp),
            "predictive_scope": "plug_in_conditional_count_variation_only",
        })
        return result


def fit_count(model, dates, counts):
    dates, y = checked_history(dates, counts)
    fit = CountFit(model, dates, y)
    if model in ("seasonal_naive", "seasonal_reference"):
        fit.alpha = None if model == "seasonal_naive" else 0.0
        fit.diagnostics = {"assumption": "point_reference" if model == "seasonal_naive"
                           else "Poisson reference; assess actual coverage under overdispersion"}
        return fit
    if model not in ("negative_binomial", "poisson_diagnostic"):
        raise ValueError(f"Unknown model: {model}")
    if not np.any(y):
        fit.alpha = 0.0
        fit.diagnostics = {"special_case": "all_zero_training_degenerate_poisson"}
        return fit
    x = design(dates, dates[0])
    caught = []
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            estimator = (NegativeBinomial(y, x, loglike_method="nb2")
                         if model == "negative_binomial" else Poisson(y, x))
            result = estimator.fit(method="bfgs", maxiter=200, disp=False)
        fit.warnings = sorted({str(w.message) for w in caught})
        converged = bool(result.mle_retvals.get("converged", False))
        alpha = float(result.params[-1]) if model == "negative_binomial" else 0.0
        params = np.asarray(result.params[:4], dtype=float)
        if not converged or not np.isfinite(params).all() or not math.isfinite(alpha) or alpha < 0:
            fit.status = "unavailable_fit_failed"
            fit.diagnostics = {"converged": converged}
            return fit
        fit.params, fit.alpha = params, alpha
        mu = np.exp(x @ params)
        variance = mu + alpha * mu**2
        residual = (y - mu) / np.sqrt(np.maximum(variance, 1e-12))
        ljung = acorr_ljungbox(residual, lags=[12], return_df=True)
        fit.diagnostics = {
            "converged": True, "alpha": alpha,
            "poisson_limit": alpha <= 1e-8,
            "pearson_dispersion": float(np.sum(residual**2) / max(1, len(y) - 4)),
            "residual_mean": float(residual.mean()),
            "residual_lag12_ljung_box_p": float(ljung.lb_pvalue.iloc[0]),
            "observed_variance_to_mean": float(np.var(y, ddof=1) / np.mean(y)),
            "residuals": [float(v) for v in residual],
            "fitted_means": [float(v) for v in mu],
        }
    except (ValueError, ArithmeticError, np.linalg.LinAlgError) as error:
        fit.status = "unavailable_fit_exception"
        fit.warnings = sorted({str(w.message) for w in caught} | {f"{type(error).__name__}: {error}"})
    return fit
