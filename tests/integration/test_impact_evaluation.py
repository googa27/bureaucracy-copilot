from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("pandas")
pytest.importorskip("statsmodels")

from examples.impact_evaluation.reminder_impact import (
    attach_ipw,
    balance_diagnostics,
    build_panel_from_sqlite,
    estimate_did,
    estimate_naive_observational,
    estimate_rct,
    overlap_diagnostic,
    pretrend_placebo,
    propensity_scores,
    simulate_rollout,
)


def test_sql_roundtrip_preserves_user_period_panel() -> None:
    raw = simulate_rollout(design="rct", n_users=20, n_pre=2, n_post=2, seed=1)
    panel = build_panel_from_sqlite(raw)

    assert len(panel) == 20 * 4
    assert panel[["user_id", "period"]].duplicated().sum() == 0
    assert set(panel["post"].unique()) == {0, 1}


def test_rct_recovers_known_effect() -> None:
    truth = -1.5
    panel = simulate_rollout(design="rct", n_users=1200, seed=3, true_effect=truth)
    estimate = estimate_rct(panel)

    assert abs(estimate.estimate - truth) < 0.20
    assert estimate.ci_low < truth < estimate.ci_high


def test_naive_observational_is_more_biased_than_did() -> None:
    truth = -1.5
    panel = simulate_rollout(design="observational", n_users=1200, seed=5, true_effect=truth)
    naive = estimate_naive_observational(panel)
    did = estimate_did(panel)

    assert abs(did.estimate - truth) < 0.20
    assert abs(naive.estimate - truth) > abs(did.estimate - truth) + 0.50


def test_propensity_weighting_improves_measured_balance() -> None:
    panel = simulate_rollout(design="observational", n_users=1500, seed=8)
    prop = propensity_scores(panel)
    diagnostics = balance_diagnostics(prop)
    overlap = overlap_diagnostic(prop)

    assert max(abs(d.weighted_smd) for d in diagnostics) < 0.10
    assert max(abs(d.weighted_smd) for d in diagnostics) < max(
        abs(d.unweighted_smd) for d in diagnostics
    )
    assert overlap.fraction_outside_common_support < 0.05


def test_ipw_did_recovers_effect_under_parallel_trends() -> None:
    truth = -1.5
    panel = simulate_rollout(design="observational", n_users=1200, seed=11, true_effect=truth)
    weighted = attach_ipw(panel, propensity_scores(panel))
    estimate = estimate_did(weighted, weights=weighted["weight"])

    assert abs(estimate.estimate - truth) < 0.25
    assert estimate.ci_low < truth < estimate.ci_high


def test_pretrend_placebo_flags_parallel_trends_violation() -> None:
    panel_ok = simulate_rollout(
        design="observational", n_users=1200, seed=13, parallel_trends=True
    )
    panel_bad = simulate_rollout(
        design="observational", n_users=1200, seed=13, parallel_trends=False
    )

    placebo_ok = pretrend_placebo(panel_ok)
    placebo_bad = pretrend_placebo(panel_bad)
    did_bad = estimate_did(panel_bad)

    assert placebo_ok.p_value > 0.05
    assert placebo_bad.p_value < 0.001
    assert abs(placebo_bad.estimate) > 0.20
    assert abs(did_bad.estimate - (-1.5)) > 0.50


def test_propensity_weights_are_finite_and_positive() -> None:
    panel = simulate_rollout(design="observational", n_users=500, seed=21)
    prop = propensity_scores(panel)

    assert np.isfinite(prop["weight"]).all()
    assert (prop["weight"] > 0).all()
    assert prop["propensity"].between(0.05, 0.95).all()
