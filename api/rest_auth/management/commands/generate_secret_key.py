from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key

class Command (BaseCommand):
    help = "Generate a secret key for project settings."

    def handle (this, *args, **kwargs):
        print (get_random_secret_key ())
