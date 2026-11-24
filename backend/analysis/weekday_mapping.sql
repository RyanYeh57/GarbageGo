-- Which weekday is 84004 d1..d7? (plan Task 6; result in docs/research/opendata-api-check.md §10)
--
-- A "hit" for (stop, slot, date): the stop's own car was within 100 m of the stop,
-- from 30 min before the slot start to 30 min after its end, on that Taipei date.
-- Dates = days on which we fetched GPS (collected_at), so stale GPS from 2025
-- does not add empty dates.
--
-- Table 1 (plan method): 1,000 sampled stops, cell = hit rate per day_index x ISO weekday.
--   Most stops are scheduled on d1,d2,d4,d5,d6 together, so every row looks alike.
-- Table 2: only stops with exactly ONE general-garbage day. Each row should light up
--   in a single weekday column; that column is the weekday of that day_index.
-- Table 3: all stops whose day set is not the common "12456". Per ISO weekday,
--   hit rate on days the stop IS scheduled vs IS NOT scheduled, assuming d<k> = ISO weekday k.
--   If the assumption is right, "scheduled" is high and "not scheduled" is near 0.
--
-- Run (repo root):
--   docker compose cp backend/analysis/weekday_mapping.sql db:/tmp/weekday_mapping.sql
--   docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/weekday_mapping.sql'

\timing on

CREATE TEMP TABLE gps_days AS
SELECT DISTINCT (collected_at AT TIME ZONE 'Asia/Taipei')::date AS d FROM vehicle_observations;

CREATE TEMP TABLE stop_days AS
SELECT stop_id, string_agg(day_index::text, '' ORDER BY day_index) AS days
FROM collection_schedules WHERE kind = 'general' GROUP BY stop_id;

CREATE TEMP TABLE picked AS
WITH eligible AS (
    SELECT s.id, s.car_licence, s.geom, sd.days
    FROM collection_stops s JOIN stop_days sd ON sd.stop_id = s.id
    WHERE s.geom IS NOT NULL AND s.geocode_level <> 'suspect' AND s.car_licence IS NOT NULL
),
sample AS (SELECT id FROM eligible ORDER BY md5(id::text) LIMIT 1000)
SELECT e.*, e.id IN (SELECT id FROM sample) AS in_sample
FROM eligible e
WHERE e.id IN (SELECT id FROM sample) OR e.days <> '12456';

CREATE TEMP TABLE hits AS
SELECT p.id AS stop_id, p.days, p.in_sample, c.day_index, dy.d, EXTRACT(ISODOW FROM dy.d)::int AS isodow,
       EXISTS (
           SELECT 1 FROM vehicle_observations o
           WHERE o.car = p.car_licence
             AND o.observed_at BETWEEN ((dy.d + c.start_time) AT TIME ZONE 'Asia/Taipei') - interval '30 minutes'
                                   AND ((dy.d + c.end_time) AT TIME ZONE 'Asia/Taipei') + interval '30 minutes'
             AND ST_DWithin(o.geom::geography, p.geom::geography, 100)
       ) AS hit
FROM picked p
JOIN collection_schedules c ON c.stop_id = p.id AND c.kind = 'general'
CROSS JOIN gps_days dy;

\echo 'Table 1: 1,000 sampled stops (plan method). Cell = % of (slot, date) with the car at the stop.'
SELECT day_index, count(*) AS pairs,
       round(avg(hit::int) FILTER (WHERE isodow = 1) * 100, 1) AS mon,
       round(avg(hit::int) FILTER (WHERE isodow = 2) * 100, 1) AS tue,
       round(avg(hit::int) FILTER (WHERE isodow = 3) * 100, 1) AS wed,
       round(avg(hit::int) FILTER (WHERE isodow = 4) * 100, 1) AS thu,
       round(avg(hit::int) FILTER (WHERE isodow = 5) * 100, 1) AS fri,
       round(avg(hit::int) FILTER (WHERE isodow = 6) * 100, 1) AS sat,
       round(avg(hit::int) FILTER (WHERE isodow = 7) * 100, 1) AS sun
FROM hits WHERE in_sample GROUP BY day_index ORDER BY day_index;

\echo 'Table 2: stops with exactly one general-garbage day.'
SELECT day_index, count(DISTINCT stop_id) AS stops,
       round(avg(hit::int) FILTER (WHERE isodow = 1) * 100, 1) AS mon,
       round(avg(hit::int) FILTER (WHERE isodow = 2) * 100, 1) AS tue,
       round(avg(hit::int) FILTER (WHERE isodow = 3) * 100, 1) AS wed,
       round(avg(hit::int) FILTER (WHERE isodow = 4) * 100, 1) AS thu,
       round(avg(hit::int) FILTER (WHERE isodow = 5) * 100, 1) AS fri,
       round(avg(hit::int) FILTER (WHERE isodow = 6) * 100, 1) AS sat,
       round(avg(hit::int) FILTER (WHERE isodow = 7) * 100, 1) AS sun
FROM hits WHERE length(days) = 1 GROUP BY day_index ORDER BY day_index;

\echo 'Table 3: stops whose day set is not 12456. Per (stop, date): any slot hit. Assumes d<k> = ISO weekday k.'
WITH per_day AS (
    SELECT stop_id, d, isodow, bool_or(hit) AS hit,
           position(isodow::text IN min(days)) > 0 AS scheduled
    FROM hits WHERE days <> '12456'
    GROUP BY stop_id, d, isodow
)
SELECT isodow,
       count(*) FILTER (WHERE scheduled)                                    AS sched_pairs,
       round(avg(hit::int) FILTER (WHERE scheduled) * 100, 1)               AS sched_hit_pct,
       count(*) FILTER (WHERE NOT scheduled)                                AS unsched_pairs,
       round(avg(hit::int) FILTER (WHERE NOT scheduled) * 100, 1)           AS unsched_hit_pct
FROM per_day GROUP BY isodow ORDER BY isodow;

\echo 'Context'
SELECT (SELECT count(*) FROM picked WHERE in_sample) AS sampled_stops,
       (SELECT count(*) FROM picked WHERE days <> '12456') AS non_12456_stops,
       (SELECT min(d) FROM gps_days) AS first_date, (SELECT max(d) FROM gps_days) AS last_date,
       (SELECT count(*) FROM gps_days) AS dates;
