import uuid

from django.core.management.base import BaseCommand

from api.rest_auth.utils import JWTClaimKey, decompose_access_token

class Command (BaseCommand):
    help = "Extract all data from an access token."

    def add_arguments (this, parser):
        parser.add_argument ('token', type=str, help='JWT access token to decompose')
        parser.add_argument ('-k', '--key', type=open, required=False, help='JWT decoding key, if necessary')

    def handle (this, *args, **kwargs):
        access_token = kwargs ['token']
        decode_key = None if kwargs ['key'] is None else kwargs ['key'].read ()

        decoded_token = decompose_access_token (access_token, decode_key=decode_key)
        user_id = uuid.UUID (decoded_token [JWTClaimKey.SUBJECT.value])

        print (f"token = {decoded_token}")
        print (f"api_user.id = {user_id}")
