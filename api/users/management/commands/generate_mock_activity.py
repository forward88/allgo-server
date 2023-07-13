import random, itertools
from datetime import timedelta

import freezegun

from django.db import models, transaction
from django.core.management.base import BaseCommand
from django.utils import timezone

from schoolyard.settings import DAY_S
from api.users.models import UserProfile, UserChallenge, UserChallengeAction, UserChallengePhase, ObstacleActivityWindow, APIUserState
from api.events.models import ObstacleActivityEvent
from api.challenges.models import Challenge

def mean_uniform_random (mean):
    half_range = mean // 3
    return random.randint (mean - half_range, mean + half_range)

def mean_normal_random (mean):
    return abs (int (random.gauss (mean, mean / 3.0)))

def generate_action_string ():
    action_string = [UserChallengeAction.JOIN]

    for j in range (random.randrange (4)):
        action_string.extend ([UserChallengeAction.PAUSE, UserChallengeAction.UNPAUSE])

    action_string.extend (random.choice ([[UserChallengeAction.LEAVE], [UserChallengeAction.PAUSE, UserChallengeAction.LEAVE], [UserChallengeAction.COMPLETE], [None]]))

    return action_string

def generate_activities (participant, challenge, n_iterations):
    activity_schedule = []

    for iteration in range (1, n_iterations + 1):
        final_action = UserChallengePhase.objects \
            .filter (
                user_challenge__user=participant,
                user_challenge__challenge=challenge,
                user_challenge__iteration=iteration) \
            .order_by ('span') \
            .last () \
            .end_action

        guarantee_completion = final_action == UserChallengeAction.COMPLETE

        for (rank, obstacle) in zip (itertools.count (start=1), challenge.obstacles_in_sequence):
            threshold = float (obstacle.threshold)
            discrete = obstacle.discrete

            windows = ObstacleActivityWindow.objects \
                .filter (
                    models.Q (challenge_phase__user_challenge__user=participant) &
                    models.Q (challenge_phase__user_challenge__challenge=challenge) &
                    models.Q (challenge_phase__user_challenge__iteration=iteration) &
                    ~ models.Q (challenge_phase__start_action=UserChallengeAction.PAUSE) &
                    models.Q (sequence_rank=rank)) \
                .order_by ('span')

            samples = []
            for window in windows:
                a_ts = window.span.lower.timestamp ()
                b_ts = window.span.upper.timestamp ()

                n_samples = max (1, int ((b_ts - a_ts) / ((3/4) * DAY_S)))

                for i in range (n_samples):
                    sample_ts = random.uniform (a_ts, b_ts)
                    samples.append (window.span.lower + timedelta (seconds=(sample_ts - a_ts)))
            samples = sorted (samples)

            cummulative_amount = 0
            sub_schedule = []
            for sample in samples:
                random_stop = min (threshold / len (samples), threshold - cummulative_amount + 1)

                if discrete:
                    amount = mean_uniform_random (max (int (random_stop), 1))
                else:
                    amount = round (random.uniform ((2/3) * random_stop, (4/3) * random_stop), 1)

                if amount <= 0:
                    continue

                if cummulative_amount + amount > threshold:
                    break

                cummulative_amount += amount

                sub_schedule.append ({'iteration': iteration, 'sequence_rank': rank, 'time': sample, 'amount': amount})

            if guarantee_completion and cummulative_amount < threshold:
                if len (sub_schedule) == 0:
                    sub_schedule.append ({'iteration': iteration, 'sequence_rank': rank, 'time': samples [0], 'amount': threshold})
                else:
                    sub_schedule [-1] ['amount'] += round (threshold - cummulative_amount, 1)

            activity_schedule.extend (sub_schedule)

    return activity_schedule

class Command (BaseCommand):
    help = "Make some obstacle activity data for testing."

    def add_arguments (this, parser):
        parser.add_argument ('-s', '--seed', type=int, metavar='SEED', help='seed to use with the PRNG, default = 1', default=1)

    def handle (this, *args, **kwargs):
        random.seed (kwargs ['seed'])

        participants = list (UserProfile.objects.filter (api_user__state=APIUserState.ACTIVE.value))
        challenges = list (Challenge.objects.all ())

        mean_interiteration_interval_s = 14 * DAY_S
        mean_intraiteration_interval_s = 2 * DAY_S

        min_interval_s = 10

        with transaction.atomic ():
            UserChallenge.objects.all ().delete ()
            UserChallengePhase.objects.all ().delete ()
            ObstacleActivityWindow.objects.all ().delete ()
            ObstacleActivityEvent.objects.all ().delete ()

            for participant in participants:
                for challenge in random.sample (challenges, random.randint (len (challenges) - 3, len (challenges))):
                    n_iterations = random.randint (2, 4)

                    challenge_duration_s = challenge.duration.total_seconds ()

                    event_offsets = []
                    event_offset_j = 0
                    activity_offsets = []
                    for i in range (n_iterations):
                        iteration_start_offset = event_offset_j
                        iteration_event_offsets = []
                        action_list = generate_action_string ()

                        n_active_phases = action_list.count (UserChallengeAction.UNPAUSE) + 1
                        active_phase_cursor = 1

                        cummulative_active_phase_duration_s = 0
                        for action in action_list [:-1]:
                            iteration_event_offsets.append ((action, event_offset_j, i + 1))

                            if action in [UserChallengeAction.JOIN, UserChallengeAction.UNPAUSE]:
                                if (active_phase_cursor + 1) < n_active_phases:
                                    mean_active_phase_duration_s = ((challenge_duration_s - min_interval_s) - cummulative_active_phase_duration_s) // (n_active_phases - active_phase_cursor)
                                    phase_duration_s = mean_uniform_random (mean_active_phase_duration_s)
                                else:
                                    phase_duration_s = random.randint (min_interval_s, challenge_duration_s - cummulative_active_phase_duration_s)

                                cummulative_active_phase_duration_s += phase_duration_s
                                active_phase_cursor += 1
                            else:
                                phase_duration_s = min_interval_s + mean_normal_random (mean_intraiteration_interval_s)

                            event_offset_j += phase_duration_s

                        if action_list [-1] is None:
                            event_offset_j += challenge_duration_s - cummulative_active_phase_duration_s
                        else:
                            iteration_event_offsets.append ((action_list [-1], event_offset_j, i + 1))
                            event_offset_j += min_interval_s

                        event_offset_j += mean_normal_random (mean_interiteration_interval_s)

                        event_offsets.extend (iteration_event_offsets)

                    schedule_start_offset_s = event_offset_j - mean_uniform_random (challenge_duration_s // 2)
                    offset_to_time = lambda offset : timezone.now () - timedelta (seconds=schedule_start_offset_s - offset)

                    event_schedule = [ (action, offset_to_time (offset_a), iteration) for (action, offset_a, iteration) in event_offsets if schedule_start_offset_s > offset_a ]

                    for (action, action_time, iteration) in event_schedule:
                        mock_date = freezegun.freeze_time (action_time)
                        mock_date.start ()
                        participant.do_challenge_action (challenge, action)
                        mock_date.stop ()

                    final_iteration = event_schedule [-1] [2]

                    activity_schedule = generate_activities (participant, challenge, final_iteration)

                    obstacles = challenge.obstacles_in_sequence

                    for item in activity_schedule:
                        mock_date = freezegun.freeze_time (item ['time'])
                        mock_date.start ()
                        participant.do_obstacle_activity (obstacles [item ['sequence_rank'] - 1], item ['sequence_rank'], item ['amount'])
                        mock_date.stop ()
