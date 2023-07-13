from django.db import migrations

class Migration (migrations.Migration):
    dependencies = [('scoring', '0001_initial')]

    operations = [
        migrations.RunSQL (
            'DROP VIEW IF EXISTS "scoring_challenge_scoring_view"; ' \
            'CREATE VIEW "scoring_challenge_scoring_view" AS ' \
            '   SELECT ' \
            '       "s_2"."challenge_id", ' \
            '       "s_2"."threshold_sum", ' \
            '       ("s_2"."xp_value" / "s_2"."threshold_sum")::DECIMAL(16, 3) AS "xp_base_unit" ' \
            '   FROM ( ' \
            '       SELECT ' \
            '           "s_1".*, ' \
            '           CASE ' \
            '               WHEN "s_1"."repeated_obstacle" THEN "s_1"."n_obstacles" * "s_1"."base_threshold_sum" ' \
            '               ELSE "s_1"."base_threshold_sum" ' \
            '           END AS "threshold_sum" ' \
            '       FROM ( ' \
            '           SELECT ' \
            '               "s_0".*, ' \
            '               "s_0"."challenge_d" / "s_0"."obstacle_d" AS "n_obstacles" ' \
            '           FROM ( ' \
            '               SELECT ' \
            '                   "challenges_challenge"."id" AS "challenge_id", ' \
            '                   "challenges_challenge"."xp_value", ' \
            '                   ARRAY_AGG("challenges_obstacle"."threshold") AS "thresholds", ' \
            '                   (ARRAY_AGG("challenges_obstacle"."sequence_rank"))[1] IS NULL AS "repeated_obstacle", ' \
            '                   EXTRACT(DAY FROM "challenges_challenge"."duration")::INTEGER AS "challenge_d", ' \
            '                   (ARRAY_AGG( ' \
            '                       CASE ' \
            '                           WHEN "challenges_obstacle"."interval" = \'D\' THEN 1 ' \
            '                           WHEN "challenges_obstacle"."interval" = \'W\' THEN 7 ' \
            '                           ELSE 28 ' \
            '                       END))[1] AS "obstacle_d", ' \
            '                   SUM("challenges_obstacle"."threshold") AS "base_threshold_sum" ' \
            '               FROM ' \
            '                   "challenges_challenge" LEFT JOIN ' \
            '                   "challenges_obstacle" ON ("challenges_obstacle"."challenge_id" = "challenges_challenge"."id") ' \
            '               GROUP BY ' \
            '                   "challenges_challenge"."id" ' \
            '               ) AS "s_0" ' \
            '           ) AS "s_1" ' \
            '       ) AS "s_2";',
            reverse_sql='DROP VIEW IF EXISTS "scoring_challenge_scoring_view";') ]
