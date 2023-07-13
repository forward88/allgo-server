from django.db import migrations

class Migration (migrations.Migration):
    dependencies = [('users', '0002_initial'), ('events', '0002_initial'), ('challenges', '0002_initial')]

    operations = [
        migrations.RunSQL (
            'CREATE VIEW "users_user_obstacle_view" AS ' \
            '   SELECT ' \
            '       CONCAT( ' \
            '           "users_userchallenge"."user_id", \'-\', ' \
            '           "challenges_obstacle"."challenge_id", \'-\', ' \
            '           "users_userchallenge"."iteration", \'-\', ' \
            '           "users_obstacleactivitywindow"."sequence_rank") AS "user_obstacle_id", ' \
            '       "users_userchallenge"."user_id", ' \
            '       "users_userchallenge"."challenge_id", ' \
            '       "users_userchallenge"."iteration", ' \
            '       "challenges_obstacle"."id" AS "obstacle_id", ' \
            '       "users_obstacleactivitywindow"."sequence_rank", ' \
            '       SUM(COALESCE("events_obstacleactivityevent"."amount_registered", 0)) AS "amount_completed" ' \
            '   FROM ' \
            '       "users_obstacleactivitywindow" LEFT JOIN ' \
            '       "users_userchallengephase" ON ("users_obstacleactivitywindow"."challenge_phase_id" = "users_userchallengephase"."id") LEFT JOIN ' \
            '       "users_userchallenge" ON ("users_userchallengephase"."user_challenge_id" = "users_userchallenge"."id") LEFT JOIN ' \
            '       "challenges_obstacle" ON ( ' \
            '           "users_userchallenge"."challenge_id" = "challenges_obstacle"."challenge_id" AND ( ' \
            '               "challenges_obstacle"."sequence_rank" IS NULL OR ' \
            '               "challenges_obstacle"."sequence_rank" = "users_obstacleactivitywindow"."sequence_rank")) LEFT JOIN ' \
            '       "events_obstacleactivityevent" ON ("events_obstacleactivityevent"."obstacle_window_id" = "users_obstacleactivitywindow"."id") '
            '   WHERE ' \
            '       "users_obstacleactivitywindow"."span" @> NOW() ' \
            '   GROUP BY ' \
            '       "users_userchallenge"."user_id", ' \
            '       "users_userchallenge"."challenge_id", ' \
            '       "users_userchallenge"."iteration", ' \
            '       "challenges_obstacle"."id", ' \
            '       "users_obstacleactivitywindow"."sequence_rank";',
            reverse_sql='DROP VIEW IF EXISTS "users_user_obstacle_view";') ]
