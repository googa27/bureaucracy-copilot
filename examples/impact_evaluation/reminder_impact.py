"""Causal impact example for a reminder feature rollout.

The module is deliberately synthetic: it demonstrates identification, estimation,
and diagnostics without using any private Bureaucracy Copilot data.
"""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Literal

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


@dataclass(frozen=True)
class Estimate:
    """Compact effect estimate with uncertainty and identification label."""

    method: str
    estimand: str
    estimate: float
    std_error: float
    ci_low: float
    ci_high: float
    p_value: float


@dataclass(frozen=True)
class BalanceDiagnostic:
    """Standardized mean-difference balance before and after weighting."""

    covariate: str
    unweighted_smd: float
    weighted_smd: float


@dataclass(frozen=True)
class OverlapDiagnostic:
    """Propensity-score overlap summary."""

    treated_min: float
    treated_max: float
    control_min: float
    control_max: float
    fraction_outside_common_support: float


PANEL_SQL = """
WITH user_period AS (
    SELECT
        user_id,
        period,
        MAX(treated) AS treated,
        MAX(post) AS post,
        AVG(days_to_resolution) AS days_to_resolution,
        MAX(backlog_z) AS backlog_z,
        MAX(complexity_z) AS complexity_z
    FROM reminder_events
    GROUP BY user_id, period
)
SELECT
    user_id,
    period,
    treated,
    post,
    days_to_resolution,
    backlog_z,
    complexity_z
FROM user_period
ORDER BY user_id, period;
""".strip()


def _to_estimate(method: str, estimand: str, result, term: str) -> Estimate:
    ci = result.conf_int().loc[term]
    return Estimate(
        method=method,
        estimand=estimand,
        estimate=float(result.params[term]),
        std_error=float(result.bse[term]),
        ci_low=float(ci.iloc[0]),
        ci_high=float(ci.iloc[1]),
        p_value=float(result.pvalues[term]),
    )


def simulate_rollout(
    *,
    design: Literal["rct", "observational"],
    n_users: int = 800,
    n_pre: int = 4,
    n_post: int = 4,
    true_effect: float = -1.5,
    seed: int = 7,
    parallel_trends: bool = True,
) -> pd.DataFrame:
    """Generate a user-period panel with known causal truth.

    Outcome is days-to-resolution, so negative treatment effects are improvements.

    RCT identification comes from randomized assignment. Observational assignment
    depends on observed baseline backlog/complexity; DiD additionally requires
    untreated potential outcomes to have parallel trends. Setting
    ``parallel_trends=False`` injects a differential untreated trend for treated
    users, deliberately violating that assumption.
    """

    if design not in {"rct", "observational"}:
        raise ValueError("design must be 'rct' or 'observational'")
    if min(n_users, n_pre, n_post) <= 0:
        raise ValueError("n_users, n_pre, and n_post must be positive")

    rng = np.random.default_rng(seed)
    user_id = np.arange(n_users)
    backlog_z = rng.normal(size=n_users)
    complexity_z = rng.normal(size=n_users)
    unit_effect = rng.normal(scale=0.7, size=n_users)

    if design == "rct":
        treated = rng.binomial(1, 0.5, size=n_users)
    else:
        # Strong observed selection on levels creates naive post-period bias while
        # retaining usable overlap for inverse-probability weighting.
        logits = 0.9 * backlog_z + 0.6 * complexity_z
        propensity = 1.0 / (1.0 + np.exp(-logits))
        treated = rng.binomial(1, propensity)

    periods = np.arange(-n_pre, n_post)
    rows: list[dict[str, float | int]] = []
    for i in user_id:
        for period in periods:
            post = int(period >= 0)
            common_trend = 0.12 * period
            # The violation exists before and after treatment, so it is detectable
            # by a pre-trend diagnostic and biases ordinary DiD.
            differential_trend = 0.0
            if not parallel_trends:
                differential_trend = 0.32 * treated[i] * period

            untreated = (
                6.0
                + 1.2 * backlog_z[i]
                + 0.8 * complexity_z[i]
                + unit_effect[i]
                + common_trend
                + differential_trend
            )
            noise = rng.normal(scale=0.8)
            observed = untreated + true_effect * treated[i] * post + noise
            rows.append(
                {
                    "user_id": int(i),
                    "period": int(period),
                    "treated": int(treated[i]),
                    "post": post,
                    "days_to_resolution": float(observed),
                    "backlog_z": float(backlog_z[i]),
                    "complexity_z": float(complexity_z[i]),
                }
            )

    return pd.DataFrame(rows)


def build_panel_from_sqlite(events: pd.DataFrame) -> pd.DataFrame:
    """Round-trip event-level rows through SQLite using explicit SQL preparation."""

    required = {
        "user_id",
        "period",
        "treated",
        "post",
        "days_to_resolution",
        "backlog_z",
        "complexity_z",
    }
    missing = required.difference(events.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    with sqlite3.connect(":memory:") as conn:
        events.to_sql("reminder_events", conn, index=False, if_exists="replace")
        return pd.read_sql_query(PANEL_SQL, conn)


def estimate_rct(panel: pd.DataFrame) -> Estimate:
    """Estimate the post-period ATE under randomized assignment."""

    post_user = (
        panel.loc[panel["post"].eq(1)]
        .groupby(["user_id", "treated"], as_index=False)["days_to_resolution"]
        .mean()
    )
    result = smf.ols("days_to_resolution ~ treated", data=post_user).fit(cov_type="HC1")
    return _to_estimate("RCT difference in means", "ATE", result, "treated")


def estimate_naive_observational(panel: pd.DataFrame) -> Estimate:
    """Estimate a deliberately naive treated-vs-control post-period contrast."""

    post_user = (
        panel.loc[panel["post"].eq(1)]
        .groupby(["user_id", "treated"], as_index=False)["days_to_resolution"]
        .mean()
    )
    result = smf.ols("days_to_resolution ~ treated", data=post_user).fit(cov_type="HC1")
    return _to_estimate("Naive observational", "associational contrast", result, "treated")


def estimate_did(panel: pd.DataFrame, *, weights: pd.Series | None = None) -> Estimate:
    """Two-group DiD with period fixed effects and user-clustered standard errors."""

    formula = "days_to_resolution ~ treated + treated:post + C(period)"
    if weights is None:
        model = smf.ols(formula, data=panel)
        label = "Difference in differences"
    else:
        model = smf.wls(formula, data=panel, weights=weights)
        label = "IPW difference in differences"

    result = model.fit(cov_type="cluster", cov_kwds={"groups": panel["user_id"]})
    return _to_estimate(label, "ATT under stated assumptions", result, "treated:post")


def propensity_scores(panel: pd.DataFrame, *, clip: float = 0.05) -> pd.DataFrame:
    """Fit baseline treatment propensity and return stabilized ATT-style weights.

    One baseline row per user is used to avoid repeated-observation pseudo-sample
    inflation in the propensity model. Scores are clipped only for numerical
    stability and diagnostic transparency; clipping does not repair bad overlap.
    """

    if not 0.0 < clip < 0.5:
        raise ValueError("clip must lie strictly between 0 and 0.5")

    baseline = (
        panel.sort_values("period")
        .groupby("user_id", as_index=False)
        .first()[["user_id", "treated", "backlog_z", "complexity_z"]]
    )
    fit = smf.logit("treated ~ backlog_z + complexity_z", data=baseline).fit(disp=False)
    baseline["propensity"] = fit.predict(baseline).clip(clip, 1.0 - clip)

    # ATT weights: treated units weight 1, controls e/(1-e).
    baseline["weight"] = np.where(
        baseline["treated"].eq(1),
        1.0,
        baseline["propensity"] / (1.0 - baseline["propensity"]),
    )
    return baseline


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.average(values, weights=weights))


def _weighted_var(values: np.ndarray, weights: np.ndarray) -> float:
    mean = _weighted_mean(values, weights)
    return float(np.average((values - mean) ** 2, weights=weights))


def balance_diagnostics(propensity_frame: pd.DataFrame) -> list[BalanceDiagnostic]:
    """Compute standardized mean differences before and after ATT weighting."""

    diagnostics: list[BalanceDiagnostic] = []
    treated = propensity_frame["treated"].eq(1).to_numpy()
    weights = propensity_frame["weight"].to_numpy()

    for covariate in ("backlog_z", "complexity_z"):
        x = propensity_frame[covariate].to_numpy()
        x_t = x[treated]
        x_c = x[~treated]
        pooled_sd = np.sqrt((np.var(x_t, ddof=1) + np.var(x_c, ddof=1)) / 2.0)
        unweighted = (float(np.mean(x_t)) - float(np.mean(x_c))) / pooled_sd

        wt = weights[treated]
        wc = weights[~treated]
        weighted_pooled_sd = np.sqrt(
            (_weighted_var(x_t, wt) + _weighted_var(x_c, wc)) / 2.0
        )
        weighted = (_weighted_mean(x_t, wt) - _weighted_mean(x_c, wc)) / weighted_pooled_sd
        diagnostics.append(
            BalanceDiagnostic(
                covariate=covariate,
                unweighted_smd=float(unweighted),
                weighted_smd=float(weighted),
            )
        )
    return diagnostics


def overlap_diagnostic(propensity_frame: pd.DataFrame) -> OverlapDiagnostic:
    """Summarize empirical common support of estimated propensity scores."""

    treated_scores = propensity_frame.loc[propensity_frame["treated"].eq(1), "propensity"]
    control_scores = propensity_frame.loc[propensity_frame["treated"].eq(0), "propensity"]
    common_low = max(float(treated_scores.min()), float(control_scores.min()))
    common_high = min(float(treated_scores.max()), float(control_scores.max()))
    outside = ~propensity_frame["propensity"].between(common_low, common_high)
    return OverlapDiagnostic(
        treated_min=float(treated_scores.min()),
        treated_max=float(treated_scores.max()),
        control_min=float(control_scores.min()),
        control_max=float(control_scores.max()),
        fraction_outside_common_support=float(outside.mean()),
    )


def attach_ipw(panel: pd.DataFrame, propensity_frame: pd.DataFrame) -> pd.DataFrame:
    """Attach one user-level propensity/weight to every user-period row."""

    return panel.merge(
        propensity_frame[["user_id", "propensity", "weight"]],
        on="user_id",
        how="left",
        validate="many_to_one",
    )


def pretrend_placebo(panel: pd.DataFrame) -> Estimate:
    """Test for differential linear pre-trends before the intervention.

    A statistically detectable treated×time slope is evidence against the standard
    DiD parallel-trends story; failure to reject is not proof of parallel trends.
    """

    pre = panel.loc[panel["post"].eq(0)].copy()
    result = smf.ols(
        "days_to_resolution ~ treated + period + treated:period + backlog_z + complexity_z",
        data=pre,
    ).fit(cov_type="cluster", cov_kwds={"groups": pre["user_id"]})
    return _to_estimate("Pre-trend placebo", "differential pre-period slope", result, "treated:period")


def compare_designs(*, seed: int = 7) -> pd.DataFrame:
    """Run the complete synthetic RCT-versus-observational comparison."""

    rct = build_panel_from_sqlite(simulate_rollout(design="rct", seed=seed))
    obs = build_panel_from_sqlite(simulate_rollout(design="observational", seed=seed))
    prop = propensity_scores(obs)
    obs_weighted = attach_ipw(obs, prop)

    estimates = [
        estimate_rct(rct),
        estimate_naive_observational(obs),
        estimate_did(obs),
        estimate_did(obs_weighted, weights=obs_weighted["weight"]),
        pretrend_placebo(obs),
    ]
    return pd.DataFrame([estimate.__dict__ for estimate in estimates])


if __name__ == "__main__":
    pd.set_option("display.width", 140)
    pd.set_option("display.max_columns", None)
    print(compare_designs().round(3).to_string(index=False))
