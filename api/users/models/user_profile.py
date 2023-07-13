from datetime import datetime, timedelta
from decimal import Decimal
from psycopg2.extras import DateTimeTZRange
import phonenumbers

from dateutil.relativedelta import relativedelta

from django.db import models, transaction
from django.db.models import functions
from django.apps import apps
from django.utils import timezone, dateparse

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from . import APIUser, UserChallenge, UserObstacle, ObstacleActivityWindow, SMSNotification, UserChallengeState, UserSupplementalXP
from api.scoring.models import UserXPLevel
from api.teams.models import TeamInvitationStatus
from api.events.models import ObstacleActivityEvent
from services import Sendbird, send_sms

__all__ = ['UserProfile', 'UserObstacleActivityRecordInterval']


class UserObstacleActivityRecordInterval (models.TextChoices):
    DAY = 'D'
    MONTH = 'M'

class UserObstacleActivityRecordSummary:
    def __init__ (this, record_data, total_xp_earned, n_obstacles, max_streak):
        this.partitions = record_data
        this.total_xp_earned = total_xp_earned
        this.n_obstacles = n_obstacles
        this.max_streak = max_streak

        this.average_amount_completed = 0

        if len (this.partitions) > 0:
            total_completed = sum ([ datum.amount_completed for datum in this.partitions ])
            this.average_amount_completed = total_completed / len (this.partitions)

class UserObstacleActivityRecordData:
    def __init__ (this, participant, date_range, amount_completed, amount_possible):
        this.participant = participant
        this.start_date = date_range.lower.date ()
        this.end_date = date_range.upper.date ()
        this.amount_completed = amount_completed
        this.amount_possible = amount_possible

class UserProfileManager (models.Manager):
    def check_nickname_availability (this, nickname=None):
        return not this.filter (nickname__iexact=nickname).exists ()

class UserProfile (models.Model):
    api_user = models.OneToOneField (APIUser, related_name='user_profile', on_delete=models.CASCADE, verbose_name="API User")
    nickname = models.CharField (max_length=15, db_collation='case_insensitive', null=True, default=None)
    team = models.ForeignKey ('teams.Team', blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='members')
    avatar = models.ForeignKey ('users.Avatar', blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='+')
    bg_color = models.ForeignKey ('users.UserColorProfile', blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='+', verbose_name='BG Color')

    objects = UserProfileManager ()

    class Meta:
        verbose_name = "User Profile"
        constraints = [models.UniqueConstraint (name='unique_nickname', fields=['nickname'])]

    def __str__ (this):
        return this.nickname

    @property
    @extend_schema_field (serializers.IntegerField ())
    def xp_level (this):
        return this.xp_level_data [0]

    @property
    @extend_schema_field (serializers.DecimalField (max_digits=16, decimal_places=3, max_value=1, min_value=0))
    def xp_level_progress (this):
        return this.xp_level_data [1]

    @property
    def xp_level_data(self):
        xp_earned = self.xp_earned
        current_level = None
        next_level = None

        xp_levels = list(UserXPLevel.objects.all())
        for i in range(len(xp_levels)):
            if xp_levels[i].xp_threshold > xp_earned:
                next_level = xp_levels[i]
                current_level = xp_levels[i - 1]
                break

        xp_level = current_level.level
        xp_level_progress = (xp_earned - current_level.xp_threshold) \
                            / (next_level.xp_threshold - current_level.xp_threshold)
        return xp_level, xp_level_progress

    @property
    def open_challenges (this):
        return [ user_challenge for user_challenge in this.user_challenges.all () if user_challenge.open ]

    @property
    def closed_challenges (this):
        return [ user_challenge for user_challenge in this.user_challenges.all () if not user_challenge.open ]

    @property
    def current_obstacles (this):
        return this.get_obstacles ()

    @property
    @extend_schema_field (serializers.CharField ())
    def team_uid (this):
        if this.team is not None:
            return this.team.shareable_uid

        return None

    @property
    def pending_invitations (this):
        return this.api_user.received_invitations.filter (status=TeamInvitationStatus.PENDING.value)

    @property
    @extend_schema_field (serializers.DecimalField (max_digits=16, decimal_places=3))
    def xp_earned (self) -> Decimal:
        return self.xp_earned_obstacle + self.xp_earned_supplemental

    @property
    def xp_earned_obstacle (this):
        return UserObstacle.objects \
            .filter (user_challenge__user=this) \
            .aggregate (total_xp_earned=functions.Coalesce (models.Sum ('xp_earned'), Decimal (0))) ['total_xp_earned']

    @property
    def xp_earned_supplemental (self):
        return UserSupplementalXP.objects \
            .filter (user_profile=self) \
            .aggregate (supplemental_xp=functions.Coalesce (models.Sum ("supplemental_xp_reward__xp_value"), 0)) ["supplemental_xp"]

    def get_obstacles (this, as_of=None):
        if as_of is None:
            all_obstacles = UserObstacle.objects.filter (user_challenge__user=this, overall_span__contains=timezone.now ())
        else:
            as_of = timezone.make_aware (datetime.combine (as_of, dateparse.parse_time ('00:00:00')))
            as_of_range = DateTimeTZRange (as_of, as_of + timedelta (days=1))

            all_obstacles = UserObstacle.objects.filter (user_challenge__user=this, overall_span__overlap=as_of_range)

        return [ obstacle for obstacle in all_obstacles if obstacle.user_challenge.state == UserChallengeState.ACTIVE ]

    def do_challenge_action (this, challenge, action):
        return UserChallenge.objects.do_action (this, challenge, action)

    def do_obstacle_activity (this, obstacle, sequence_rank, amount):
        return ObstacleActivityEvent.objects.add_event (this, obstacle, sequence_rank, amount)

    def get_user_challenge (this, challenge):
        return this.user_challenges.filter (challenge=challenge).order_by ('iteration').last ()

    def get_obstacle_activity_record (this, start_date, end_date, interval_type, team=None):
        date_ranges = []

        if interval_type == UserObstacleActivityRecordInterval.DAY:
            interval = timedelta (days=1)
            n_records = (end_date - start_date).days + 1

            start_i = timezone.make_aware (datetime.combine (start_date, dateparse.parse_time ('00:00:00')))
            end_i = timezone.make_aware (datetime.combine (start_date, dateparse.parse_time ('23:59:59')))

            for i in range (n_records):
                date_ranges.append (DateTimeTZRange (lower=start_i, upper=end_i))
                start_i += interval
                end_i += interval
        else:
            interval = relativedelta (months=1)
            intraval = relativedelta (months=1, days=-1, hours=23, minutes=59, seconds=59)
            n_records = end_date.month - start_date.month + 1

            start_i = timezone.make_aware (datetime.combine (start_date, dateparse.parse_time ('00:00:00')))
            end_i = timezone.make_aware (start_date + intraval)

            for i in range (n_records):
                date_ranges.append (DateTimeTZRange (lower=start_i, upper=end_i))
                start_i += interval
                end_i = start_i + intraval

        records = []

        users = team.members.all() if team is not None else [this, ]

        for date_range in date_ranges:
            obstacle_windows = ObstacleActivityWindow.objects \
                .annotate (span_intersection=models.F ('span') * date_range) \
                .filter (span__overlap=date_range, challenge_phase__user_challenge__user__in=users)

            amount_possible = 0
            for window in obstacle_windows:
                intersection_duration = window.span_intersection.upper - window.span_intersection.lower
                obstacle_duration = window.obstacle.duration
                threshold = window.obstacle.threshold
                amount_possible += threshold * Decimal (intersection_duration / obstacle_duration)

            record_data = ObstacleActivityEvent.objects \
                .filter (api_user__user_profile__in=users, ctime__range=(date_range.lower, date_range.upper)) \
                .aggregate (amount_completed=functions.Coalesce (models.Sum ('amount_registered'), Decimal (0)))

            amount_completed = record_data.get ('amount_completed', 0)

            records.append (UserObstacleActivityRecordData (this, date_range, amount_completed, amount_possible))

        start_datetime = timezone.make_aware (datetime.combine (start_date, dateparse.parse_time ('00:00:00')))
        end_datetime = timezone.make_aware (datetime.combine (end_date, dateparse.parse_time ('23:59:59')))

        summary_data = ObstacleActivityEvent.objects \
            .filter (api_user__user_profile__in=users, ctime__range=(start_datetime, end_datetime)) \
            .aggregate (
                n_obstacles=functions.Coalesce (models.Count (
                    functions.Concat (
                        'obstacle_window__challenge_phase__user_challenge__challenge__pk',
                        models.Value ('-'),
                        'obstacle_window__sequence_rank'), distinct=True), 0),
                max_streak=functions.Coalesce (models.Max ('streak'), 0),
                total_xp_earned=functions.Coalesce (models.Sum (models.F ('amount_registered') * models.F ('obstacle_window__challenge_phase__user_challenge__challenge__scoring__xp_base_unit')), Decimal (0)))

        n_obstacles = summary_data.get ('n_obstacles', 0)
        max_streak = summary_data.get ('max_streak', 0)
        total_xp_earned = summary_data.get ('total_xp_earned', 0)

        return UserObstacleActivityRecordSummary (records, total_xp_earned, n_obstacles, max_streak)

    def create_team (this):
        team_model = apps.get_model ('teams', 'Team')

        with transaction.atomic ():
            team = team_model (creator=this, user_created=True)
            team.save ()

            this.team = team
            this.save ()

            Sendbird.create_channel (this.team.chat_channel_id, [this.chat_user_id])

            return team

    def leave_team (this):
        if this.team is not None:
            with transaction.atomic ():
                if this.team.creator == this:
                    this.team.creator = None
                    this.team.save ()

                this.team = None
                this.save ()

    def invite_team_member (this, team_uid, phone_number):
        team_model = apps.get_model ('teams', 'Team')
        invitation_model = apps.get_model ('teams', 'TeamInvitation')

        team = team_model.objects.get (shareable_uid=team_uid)

        with transaction.atomic ():
            (invitee, created) = APIUser.objects.get_or_create (phone_number=phone_number)
            invitation = invitation_model (inviter=this.api_user, invitee=invitee, team=team)
            invitation.save ()

            message_template = SMSNotification.objects.team_invitation_message_body
            message = message_template.replace ('%%TEAM_UID%%', team.shareable_uid)

            invitee_e164_phone_number = phonenumbers.format_number (invitee.phone_number, phonenumbers.PhoneNumberFormat.E164)

            if not invitee_e164_phone_number.startswith ('+1612555'):
                send_sms (invitee_e164_phone_number, message)

    def accept_team_invitation (this, team_uid):
        team_model = apps.get_model ('teams', 'Team')

        with transaction.atomic ():
            this.team = team_model.objects.get (shareable_uid__iexact=team_uid)
            this.save ()

            invitation = this.pending_invitations.filter (team=this.team).first ()
            if invitation is not None:
                invitation.status = TeamInvitationStatus.ACCEPTED
                invitation.save ()

    def decline_team_invitation (this, team_uid):
        team_model = apps.get_model ('teams', 'Team')

        team = team_model.objects.get (shareable_uid=team_uid)

        invitation = this.pending_invitations.get (team=team)
        invitation.status = TeamInvitationStatus.DECLINED
        invitation.save ()

    @property
    def all_invitations (this):
        invitations = list (this.pending_invitations)

        if this.team is not None:
            invitations.extend (this.team.invitations.all ())

        return invitations

    @property
    @extend_schema_field (serializers.IntegerField ())
    def streak (this):
        now = timezone.now ()
        current_event = ObstacleActivityEvent.objects.filter (
            api_user=this.api_user,
            ctime__year=now.year,
            ctime__month=now.month,
            ctime__day=now.day).first ()

        if current_event is None:
            return 0

        return current_event.streak

    @property
    @extend_schema_field (serializers.CharField ())
    def chat_user_id (this):
        return Sendbird.build_user_id (this.api_user.pk)
