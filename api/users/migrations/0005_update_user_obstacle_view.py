from django.db import migrations

class Migration (migrations.Migration):
    dependencies = [('users', '0004_smsnotification')]

    operations = [
        migrations.RunSQL (
            'DROP VIEW IF EXISTS "users_user_obstacle_view"; ' \
            'CREATE VIEW "users_user_obstacle_view" AS ' \
            '   SELECT ' \
            '       CONCAT( ' \
            '           "users_userchallenge"."id", \'-\', ' \
            '           "users_userchallenge"."challenge_id", \'-\', ' \
            '           "users_userchallenge"."iteration", \'-\', ' \
            '           "users_obstacleactivitywindow"."sequence_rank") AS "user_obstacle_id", ' \
            '       "users_userchallenge"."id" AS "user_challenge_id", ' \
            '       "users_userchallenge"."challenge_id", ' \
            '       "users_userchallenge"."iteration", ' \
            '       "challenges_obstacle"."id" AS "obstacle_id", ' \
            '       "users_obstacleactivitywindow"."sequence_rank", ' \
            '       TSTZRANGE(MIN(LOWER("users_obstacleactivitywindow"."span")), MAX(UPPER("users_obstacleactivitywindow"."span")), \'[)\') AS "overall_span", ' \
            '       SUM(COALESCE("events_obstacleactivityevent"."amount_registered", 0)) AS "amount_completed", ' \
            '       COUNT("users_obstacleactivitywindow"."span") AS "n_spans" ' \
            '   FROM ' \
            '       "users_userchallenge" LEFT JOIN ' \
            '       "users_userchallengephase" ON ("users_userchallenge"."id" = "users_userchallengephase"."user_challenge_id") INNER JOIN ' \
            '       "users_obstacleactivitywindow" ON ("users_userchallengephase"."id" = "users_obstacleactivitywindow"."challenge_phase_id") LEFT JOIN ' \
            '       "challenges_obstacle" ON ( ' \
            '           "users_userchallenge"."challenge_id" = "challenges_obstacle"."challenge_id" AND ( ' \
            '               "challenges_obstacle"."sequence_rank" IS NULL OR ' \
            '               "challenges_obstacle"."sequence_rank" = "users_obstacleactivitywindow"."sequence_rank")) LEFT JOIN ' \
            '       "events_obstacleactivityevent" ON ("events_obstacleactivityevent"."obstacle_window_id" = "users_obstacleactivitywindow"."id") ' \
            '   GROUP BY ' \
            '       "users_userchallenge"."id", ' \
            '       "users_userchallenge"."challenge_id", ' \
            '       "users_userchallenge"."iteration", ' \
            '       "challenges_obstacle"."id", ' \
            '       "users_obstacleactivitywindow"."sequence_rank" ' \
            '   ORDER BY ' \
            '       "users_userchallenge"."id", ' \
            '       "users_userchallenge"."challenge_id", ' \
            '       "users_userchallenge"."iteration", ' \
            '       "users_obstacleactivitywindow"."sequence_rank";',
            reverse_sql='DROP VIEW IF EXISTS "users_user_obstacle_view";') ]
