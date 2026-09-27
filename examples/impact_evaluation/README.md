# Reminder Impact Evaluation — RCT vs Observational DiD

A small, public-synthetic causal-impact case study for **Bureaucracy Copilot**.

**Question:** does a reminder feature reduce the number of days required to resolve an administrative task?

This example deliberately analyzes the *same intervention* under two data-generating designs:

1. **Randomized controlled trial (RCT):** reminder assignment is randomized.
2. **Observational rollout:** users with larger backlog and more complex tasks are more likely to receive reminders.

The point is not to build a general causal-inference framework. It is to show a reviewable vertical slice from SQL preparation → identification assumptions → estimation → diagnostics → failure-mode demonstration.

## Why this belongs here

Bureaucracy Copilot already contains reminder/calendar workflows. Measuring whether reminders improve resolution speed is therefore a real product-impact question rather than a disconnected econometrics demo. The data are synthetic and contain no Gmail, Calendar, medical, financial, or other private user records.

## What is implemented

| Surface | Method | Purpose |
|---|---|---|
| Experimental | RCT difference in means with HC1 robust SE | Benchmark causal estimate under randomized assignment |
| Observational | Naive post-period OLS | Deliberately biased associational comparator |
| Observational | Difference-in-differences (DiD) with period fixed effects and user-clustered SE | Causal estimate under parallel trends |
| Observational | Logistic propensity model + ATT inverse-probability weights + DiD | Improve observed baseline balance before DiD |
| Diagnostic | Standardized mean differences | Check measured covariate balance before/after weighting |
| Diagnostic | Empirical common support | Check propensity-score overlap/positivity |
| Diagnostic | Pre-trend placebo | Look for evidence against parallel trends |
| Failure mode | Injected differential untreated trend | Show DiD bias when parallel trends is false |
| Data preparation | SQLite CTE / aggregation | Demonstrate explicit SQL dataset construction |

Not implemented on purpose: synthetic controls and instrumental variables. They answer different identification problems and would make this artifact larger without improving this example's identification story. See **Method choice** below.

## Causal estimands and identification

Let \(Y_{it}(1)\) and \(Y_{it}(0)\) be potential days-to-resolution for user \(i\), period \(t\), with and without reminders. Lower is better.

The synthetic truth is a constant post-treatment effect

\[
\tau = Y_{it}(1)-Y_{it}(0) = -1.5 \text{ days}.
\]

### 1. RCT

For randomized treatment \(D_i\), the post-period average treatment effect is identified by

\[
\widehat{\tau}_{RCT}
= \bar Y_{D=1,post} - \bar Y_{D=0,post}.
\]

**Identification assumptions**

- random assignment is implemented as specified;
- SUTVA / no interference between users;
- no hidden versions of the reminder treatment;
- no treatment-dependent attrition or missing outcome process;
- analysis respects the randomization unit (the example randomizes users).

Randomization makes treatment independent of potential outcomes *in expectation*. It does not fix interference, missingness, noncompliance, or bad measurement.

### 2. Difference-in-differences

The observational rollout estimates

\[
Y_{it}
= \alpha + \gamma D_i + \lambda_t + \tau(D_i\times Post_t) + \varepsilon_{it},
\]

with period fixed effects \(\lambda_t\) and standard errors clustered by user.

The identifying restriction is the untreated-potential-outcome parallel-trends condition:

\[
E[Y_{it}(0)-Y_{i,t-1}(0)\mid D_i=1]
=
E[Y_{it}(0)-Y_{i,t-1}(0)\mid D_i=0].
\]

**Additional assumptions**

- no anticipation before rollout;
- stable group composition and outcome measurement;
- no treatment spillovers;
- no other group-specific intervention starts at the same cutoff;
- the single common adoption date used here is correctly recorded.

The example intentionally uses a single adoption date. With staggered adoption and heterogeneous effects, a generic two-way-fixed-effects coefficient can be misleading; use a staggered-adoption estimator designed for that setting instead.

### 3. Propensity-score weighting + DiD

For baseline covariates \(X_i=(\text{backlog}_i,\text{complexity}_i)\), estimate

\[
e(X_i)=P(D_i=1\mid X_i)
\]

with `statsmodels` logistic regression. ATT-style weights are

\[
w_i=
\begin{cases}
1,&D_i=1,\\
\dfrac{e(X_i)}{1-e(X_i)},&D_i=0.
\end{cases}
\]

This targets an observational comparison whose measured baseline covariates more closely resemble the treated group.

**What weighting does not do:** it cannot repair unobserved confounding, interference, differential untreated trends, post-treatment conditioning, or lack of common support. Balance after weighting is a diagnostic, not proof of causal validity.

## Diagnostics

### Covariate balance

For covariate \(X\), the standardized mean difference is

\[
SMD(X)=\frac{\bar X_T-\bar X_C}{\sqrt{(s_T^2+s_C^2)/2}}.
\]

The tests require absolute weighted SMDs below `0.10` on the two synthetic assignment covariates. That threshold is a practical diagnostic convention, not a theorem.

### Overlap / positivity

The code reports treated/control propensity ranges and the fraction of observations outside empirical common support. Extreme scores imply unstable weights and weak support for counterfactual comparisons.

### Pre-trend placebo

On pre-treatment data only, the example estimates a treated × time slope. A detectable differential pre-trend is evidence **against** the standard DiD story.

Failure to reject the placebo is not proof of parallel trends: pre-periods may be noisy or too short to reveal violations.

## Failure-mode experiment

`simulate_rollout(..., parallel_trends=False)` adds a treated-group untreated trend *before and after* treatment. The same DiD estimator that works under the valid design becomes materially biased, while the pre-trend placebo flags the violation.

This is included because a causal artifact should show when its estimator fails, not only when it succeeds.

## Observational vs experimental comparison

| Dimension | RCT | Observational DiD + propensity weighting |
|---|---|---|
| Treatment assignment | randomized | selected using observed baseline characteristics |
| Main identifying argument | randomization | parallel trends; weighting additionally uses conditional treatment model |
| Handles observed level imbalance | by design, in expectation | weighting can improve measured balance |
| Handles unobserved time-invariant level differences | randomization | DiD differences them out |
| Handles unobserved differential trends | randomization, if intact | **no** |
| Primary diagnostics | randomization balance, attrition, compliance, interference | balance, overlap, pre-trends, timing, concurrent shocks |
| Typical failure | noncompliance, attrition, spillovers, broken randomization | nonparallel trends, hidden time-varying confounding, poor overlap, anticipation |
| Causal credibility when feasible | generally stronger | depends heavily on design plausibility and diagnostics |

The observational design is not a weaker RCT substitute by definition; it is a different identification strategy. When randomization is ethically and operationally feasible, the RCT usually requires fewer assumptions about treatment selection.

## Method choice: why not IV or synthetic control here?

| Method | Use when | Key additional identification burden |
|---|---|---|
| RCT | treatment can be randomized | valid randomization, interference/compliance/attrition handling |
| DiD | treatment starts at a known time for treated vs comparison groups | parallel untreated trends, no anticipation/confounding concurrent shocks |
| Propensity methods | treatment selection is explainable by measured baseline covariates | conditional exchangeability + overlap; does not solve hidden confounding |
| Instrumental variables | treatment is endogenous but a credible instrument shifts treatment | relevance, exclusion restriction, independence; monotonicity for LATE |
| Synthetic control | one/few aggregate treated units with a donor pool and long pre-period | donor pool can reproduce untreated counterfactual; no contamination/spillovers |

For this user-level reminder rollout, RCT and DiD are natural. IV would require inventing a credible instrument; synthetic control would require changing the unit of analysis to an aggregate treated unit/donor-pool setting.

## SQL preparation

`reminder_panel.sql` constructs one user × period row from an event table:

```sql
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
SELECT * FROM user_period;
```

The Python example executes the query against an in-memory SQLite database so SQL preparation is part of the tested path rather than README-only pseudocode.

## Run

This example is intentionally an optional research profile so the core Gmail/Calendar runtime does not gain scientific-computing dependencies.

```bash
python -m pip install -e '.[impact]'
python examples/impact_evaluation/reminder_impact.py
python -m pytest -q tests/integration/test_impact_evaluation.py
```

Expected deterministic result with the default seed is approximately:

| Method | Estimate (days) | Interpretation |
|---|---:|---|
| RCT difference in means | -1.53 | close to truth (-1.50) |
| Naive observational | -0.21 | badly confounded by treatment selection |
| DiD | -1.45 | recovers effect under parallel trends |
| IPW DiD | -1.52 | balances observed assignment covariates and recovers effect |
| Pre-trend placebo | 0.00 slope | no detectable differential pre-trend in valid design |

Exact estimates may move slightly across numerical-library versions.

## Tests

The test suite checks that:

- SQL preparation preserves one row per user × period;
- randomized assignment recovers the known effect;
- the naive observational contrast is materially more biased than DiD;
- propensity weighting improves measured covariate balance;
- empirical overlap is adequate in the valid synthetic design;
- IPW DiD recovers the known effect under parallel trends;
- a deliberately violated parallel-trends design is detected by the placebo and biases DiD;
- propensity weights are finite and positive.

The implementation was executed locally with **7 passing tests** on Python 3.13.5, NumPy 2.3.5, pandas 2.2.3, and statsmodels 0.14.6. Current releases checked on 2026-09-27 are newer (NumPy 2.5.3, pandas 3.0.6, statsmodels 0.15.0); the available execution environment could not reach PyPI to create a clean environment for those exact versions, so compatibility with the newest trio is declared as intended by the optional dependency bounds, not falsely claimed as executed evidence.

## Dependency and data boundary

- `numpy`, `pandas`, and `statsmodels` are optional under the `impact` extra only.
- No core runtime module imports them.
- The example uses public-synthetic data only.
- `statsmodels` is a BSD-3-Clause project; NumPy and pandas are established scientific-Python dependencies with permissive open-source licensing.
- The statistical estimators are composed from maintained library primitives rather than reimplementing OLS/logit/covariance estimators from scratch.

## Scope limits

This is an interview-sized research artifact, not a production experimentation platform. It does **not** implement:

- power/sample-size planning;
- sequential testing or alpha spending;
- CUPED/CUPAC variance reduction;
- multiple-testing control;
- heterogeneous treatment-effect estimation;
- cluster randomization;
- noncompliance / ITT / LATE workflows;
- staggered-adoption DiD estimators;
- synthetic controls;
- instrumental variables;
- sensitivity bounds for unobserved confounding;
- production data contracts, lineage, or experiment registry services.

Those are extension points, not hidden claims.
