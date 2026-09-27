-- Public-synthetic example only. No private Gmail/Calendar data is queried.
-- Grain after the CTE: one user × period observation.
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
