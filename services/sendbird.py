import requests

from django.conf import settings
from django.utils.functional import classproperty

__all__ = ['Sendbird']

class Sendbird:
    class API:
        base_url = settings.SENDBIRD ['API_URL']
        version = settings.SENDBIRD ['API_VERSION']
        token_header = {'Api-Token': settings.SENDBIRD ['TOKEN']}

    class Action:
        list_users = 'users'
        create_user = 'users'
        get_user = 'users/{user_id}'
        list_channels = 'group_channels'
        create_channel = 'group_channels'
        get_channel = 'group_channels/{channel_url}'
        join_channel = 'group_channels/{channel_url}/join'

    class ResponseKey:
        next_token = 'next'
        users = 'users'
        channels = 'channels'

    @classmethod
    def build_endpoint (this_class, action):
        return f"{this_class.API.base_url}/{this_class.API.version}/{action}"

    @classmethod
    def build_user_id (this_class, user_id):
        return f"{settings.SCHOOLYARD_ENVIRONMENT}_{user_id}"

    @classmethod
    def build_channel_url (this_class, channel_type, channel_id):
        return f"{settings.SCHOOLYARD_ENVIRONMENT}_{channel_type}_{channel_id}"

    @classmethod
    def get (this_class, action, **query_parameters):
        response = requests.get (this_class.build_endpoint (action), headers=this_class.API.token_header, params=query_parameters).json ()

        if 'message' in response and 'not found' in response ['message']:
            return None

        return response

    @classmethod
    def post (this_class, action, **payload):
        response = requests.post (this_class.build_endpoint (action), headers=this_class.API.token_header, json=payload)

        return response.json ()

    @classmethod
    def put (this_class, action, **payload):
        response = requests.put (this_class.build_endpoint (action), headers=this_class.API.token_header, json=payload)

        return response.json ()

    @classmethod
    def concat_gets (this_class, action, response_key, **query_parameters):
        data = []

        has_next = True
        next_token = None
        while has_next:
            response = this_class.get (action, token=next_token, limit=100)
            data.extend (response [response_key])
            next_token = response [this_class.ResponseKey.next_token]
            has_next = (next_token != '')

        return data

    @classmethod
    def list_users (this_class):
        return this_class.concat_gets (this_class.Action.list_users, this_class.ResponseKey.users)

    @classmethod
    def create_user (this_class, user_id, nickname, profile_url):
        payload = {
            'user_id': user_id,
            'nickname': nickname,
            'profile_url': profile_url }

        return this_class.post (this_class.Action.create_user, **payload)

    @classmethod
    def get_user (this_class, user_id):
        return this_class.get (this_class.Action.get_user.format (user_id=user_id))

    @classmethod
    def list_channels (this_class):
        return this_class.concat_gets (this_class.Action.list_channels, this_class.ResponseKey.channels)

    @classmethod
    def create_channel (this_class, channel_id, user_ids):
        payload = {
            'user_ids': user_ids,
            'channel_url': channel_id,
            'is_public': True }

        return this_class.post (this_class.Action.create_channel, **payload)

    @classmethod
    def get_channel (this_class, channel_id):
        return this_class.get (this_class.Action.get_channel.format (channel_url=channel_id))

    @classmethod
    def join_channel (this_class, channel_id, user_id):
        payload = {'user_id': user_id}

        return this_class.put (this_class.Action.join_channel.format (channel_url=channel_id), **payload)
