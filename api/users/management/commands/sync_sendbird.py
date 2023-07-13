from django.core.management.base import BaseCommand
from django.core.management.base import CommandParser

from api.challenges.models import Challenge
from api.users.models import UserProfile, UserChallenge
from api.teams.models import Team
from services import Sendbird

class Command (BaseCommand):
    def add_arguments (self, parser: CommandParser) -> None:
        parser.add_argument ("-d", "--dry-run", default=False, action="store_true", help="Only show what would be done.")

    def handle (self, *args, **options) -> None:
        dry_run = options ["dry_run"]

        self.sync_users (dry_run)
        self.sync_teams (dry_run)
        self.sync_challenges (dry_run)

    def sync_challenges (self, dry_run: bool) -> None:
        n_checked = 0
        n_changed = 0
        for challenge in Challenge.objects.all ():
            self.stdout.write (f"Checking {challenge.name} ({challenge.chat_channel_id})")
            n_checked += 1

            sendbird_channel_id = challenge.chat_channel_id
            sendbird_channel = Sendbird.get_channel (sendbird_channel_id)

            if sendbird_channel is None:
                self.stdout.write (self.style.WARNING (f"Create challenge channel: {challenge.chat_channel_id}"))

                if not dry_run:
                    user_challenges = UserChallenge.objects.filter (challenge=challenge).distinct ('user')
                    user_ids = [ user_challenge.user.chat_user_id for user_challenge in user_challenges ]
                    Sendbird.create_channel (sendbird_channel_id, user_ids)
                    n_changed += 1

        self.stdout.write (self.style.SUCCESS (f"Checked {n_checked} challenges; updated {n_changed} challenges."))

    def sync_users (self, dry_run: bool) -> None:
        n_checked = 0
        n_changed = 0
        for user in UserProfile.objects.all ():
            self.stdout.write (f"Checking {user.nickname} ({user.chat_user_id})")
            n_checked += 1

            sendbird_user_id = user.chat_user_id
            sendbird_user = Sendbird.get_user (sendbird_user_id)

            if sendbird_user is None:
                self.stdout.write (self.style.WARNING (f"Create user: {user.api_user.pk} ({user.nickname})"))

                if not dry_run:
                    Sendbird.create_user (sendbird_user_id, user.nickname, '')
                    n_changed += 1

        self.stdout.write (self.style.SUCCESS (f"Checked {n_checked} users; updated {n_changed} users."))

    def sync_teams (self, dry_run: bool) -> None:
        n_checked = 0
        n_changed = 0
        for team in Team.objects.all ():
            self.stdout.write (f"Checking {team.chat_channel_id}")
            n_checked += 1

            sendbird_channel_id = team.chat_channel_id
            sendbird_channel = Sendbird.get_channel (sendbird_channel_id)

            if sendbird_channel is None:
                self.stdout.write (self.style.WARNING (f"Create team channel: {team.chat_channel_id}"))

                if not dry_run:
                    member_ids = [ user.chat_user_id for user in team.roster ]
                    Sendbird.create_channel (sendbird_channel_id, member_ids)
                    n_changed += 1

        self.stdout.write (self.style.SUCCESS (f"Checked {n_checked} teams; updated {n_changed} teams."))
