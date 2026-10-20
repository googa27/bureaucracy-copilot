"""Independent deterministic oracles, distinct from seed-specific coverage checks."""

from __future__ import annotations

import importlib
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("statsmodels")
impact = importlib.import_module("examples.impact_evaluation.reminder_impact")


def two_period_panel():
    rows = []
    for user, treated, pre, post in [
        (0, 1, 3.0, 4.0),
        (1, 1, 5.0, 7.0),
        (2, 0, 2.0, 5.0),
        (3, 0, 4.0, 8.0),
    ]:
        for period, value in [(-1, pre), (0, post)]:
            rows.append(
                {
                    "user_id": user,
                    "treated": treated,
                    "period": period,
                    "post": int(period == 0),
                    "days_to_resolution": value,
                    "backlog_z": 0.0,
                    "complexity_z": 0.0,
                }
            )
    return pd.DataFrame(rows)


@pytest.mark.parametrize("scores", [[0.96, 0.97, 0.98, 0.99], [0.01, 0.02, 0.03, 0.04]])
def test_raw_disjoint_tails_cannot_become_overlap_after_clipping(monkeypatch, scores):
    # Control only the selection-model output; execute the actual weighting/diagnostic path.
    class Selection:
        def fit(self, **kwargs):
            return self

        def predict(self, baseline):
            return pd.Series(scores, index=baseline.index)

    monkeypatch.setattr(impact.smf, "logit", lambda *args, **kwargs: Selection())
    prop = impact.propensity_scores(two_period_panel())
    diagnostic = impact.overlap_diagnostic(prop)
    assert diagnostic.fraction_outside_common_support == 1.0
    assert diagnostic.treated_min == scores[0] and diagnostic.control_max == scores[-1]
    assert diagnostic.clipped_count == 4 and diagnostic.clipped_fraction == 1.0
    assert diagnostic.score_basis == "unclipped_fitted"
    np.testing.assert_array_equal(prop["raw_propensity"], scores)
    assert prop["propensity_was_clipped"].all()
    # ATT weights use the bounded scores, preserving the deliberate regularization.
    assert prop["propensity"].between(0.05, 0.95).all()
    assert (prop.loc[prop.treated.eq(1), "weight"] == 1).all()


def test_clipped_only_frame_cannot_claim_raw_overlap():
    frame = pd.DataFrame({"treated": [0, 1], "propensity": [0.95, 0.95]})
    with pytest.raises(ValueError, match="raw_propensity"):
        impact.overlap_diagnostic(frame)


@pytest.mark.parametrize("weighted", [False, True])
def test_did_matches_two_period_contrast_and_cluster_sandwich_oracle(weighted):
    panel = two_period_panel()
    weights = np.array([1, 1, 1, 1, 0.5, 0.5, 2, 2]) if weighted else np.ones(8)
    estimate = impact.estimate_did(panel, weights=pd.Series(weights) if weighted else None)
    # Closed-form group changes give -2 unweighted, -2.3 with the supplied weights.
    expected = -2.3 if weighted else -2.0
    assert estimate.estimate == pytest.approx(expected, abs=1e-12)
    x = np.column_stack([np.ones(8), panel.treated, panel.post, panel.treated * panel.post])
    y = panel.days_to_resolution.to_numpy()
    beta = np.linalg.lstsq(np.sqrt(weights)[:, None] * x, np.sqrt(weights) * y, rcond=None)[0]
    bread = np.linalg.inv(x.T @ (weights[:, None] * x))
    residual = y - x @ beta
    scores = np.array(
        [
            (x[panel.user_id.eq(g)] * (weights * residual)[panel.user_id.eq(g), None]).sum(axis=0)
            for g in range(4)
        ]
    )
    # Standard finite-sample group and regression-df corrections, independently assembled.
    covariance = bread @ (scores.T @ scores) @ bread * (4 / 3) * (7 / 4)
    assert estimate.std_error == pytest.approx(float(np.sqrt(covariance[3, 3])), rel=1e-10)
    if weighted:
        assert (
            estimate.uncertainty_scope
            == "conditional_on_supplied_weights_no_first_stage_adjustment"
        )
        assert "requires justified weights" in estimate.estimand
    assert estimate.coverage_validated is False


def test_rct_matches_difference_and_independent_hc1_oracle():
    estimate = impact.estimate_rct(two_period_panel())
    assert estimate.estimate == pytest.approx(-1.0)
    # Two independent groups of two post-user means, each sample variance4.5.
    assert estimate.std_error == pytest.approx(np.sqrt(4.5 / 2 + 4.5 / 2))


def test_sql_file_matches_executed_embedded_preparation():
    frame = two_period_panel()
    sql = (Path(impact.__file__).parent / "reminder_panel.sql").read_text()
    with closing(sqlite3.connect(":memory:")) as connection:
        frame.to_sql("reminder_events", connection, index=False)
        expected = pd.read_sql_query(sql, connection)
    pd.testing.assert_frame_equal(expected, impact.build_panel_from_sqlite(frame))


def test_sql_preparation_closes_owned_native_connection(monkeypatch):
    connection = sqlite3.connect(":memory:")
    monkeypatch.setattr(impact.sqlite3, "connect", lambda *args, **kwargs: connection)
    try:
        impact.build_panel_from_sqlite(two_period_panel())
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")
    finally:
        connection.close()
