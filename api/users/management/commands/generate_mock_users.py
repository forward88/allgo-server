import random
from datetime import date, timedelta

import phonenumbers
import freezegun

from django.core.management.base import BaseCommand
from django.utils import timezone

from schoolyard.settings import DAY_S
from api.users.models import APIUser, UserProfile

class Command (BaseCommand):
    help = "Make some users for testing."

    nicknames = [
        "SashaFierce",
        "JenniferJuniper",
        "TelegramSam",
        "LadyElla",
        "ScoobyDoo",
        "ZiggyStardust",
        "WinstonOBoogie" ]

    def handle (this, *args, **kwargs):
        random.shuffle (this.nicknames)
        phone_numbers = [ phonenumbers.parse (f"+1612555{line:04d}") for line in range (len (this.nicknames)) ]

        base_offset_d = -90

        for (nickname, phone_number) in zip (this.nicknames, phone_numbers):
            ctime_offset_d = base_offset_d + random.randint (-5, 5)
            first_sign_in_offset_s = -random.randrange (3 * DAY_S)
            last_sign_in_offset_s = -random.randrange (5 * DAY_S)
            last_access_offset_s = -random.randrange (-last_sign_in_offset_s)

            api_user = APIUser (
                phone_number=phone_number,
                first_sign_in=timezone.now () + (timedelta (days=ctime_offset_d) - timedelta (seconds=first_sign_in_offset_s)),
                last_sign_in=timezone.now () + timedelta (seconds=last_sign_in_offset_s),
                last_access=timezone.now () + timedelta (seconds=last_sign_in_offset_s),
                refresh_token_revocation_cursor=random.randint (4, 32))

            mock_date = freezegun.freeze_time (date.today () + timedelta (days=ctime_offset_d))
            mock_date.start ()
            api_user.save ()
            UserProfile (api_user=api_user, nickname=nickname).save ()
            mock_date.stop ()
