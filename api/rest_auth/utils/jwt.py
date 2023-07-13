import uuid
from datetime import datetime
import calendar
import enum

from django.conf import settings
import jwt
from cryptography.fernet import Fernet

__all__ = ['JWTClaimKey', 'create_access_token', 'create_access_refresh_token_pair', 'rotate_refresh_token', 'extract_access_token_data', 'extract_refresh_token_data', 'decompose_access_token']

class JWTClaimKey (enum.Enum):
    TYPE = 'typ'
    VERSION = 'ver'
    TOKEN_ID = 'jti'
    ISSUED_AT = 'iat'
    EXPIRY = 'exp'
    SUBJECT = 'sub'

class JWTType (enum.Enum):
    ACCESS = 'acc'
    REFRESH = 'ref'

jwt_id_fernet_instance = Fernet (settings.API_AUTH_FERNET_KEY)

def utc_epoch_now ():
    return calendar.timegm (datetime.utcnow ().utctimetuple ())

def create_access_token (sub_uuid):
    now = utc_epoch_now ()

    access_token_payload = {
        JWTClaimKey.TYPE.value: JWTType.ACCESS.value,
        JWTClaimKey.VERSION.value: settings.API_AUTH_JWT_VERSION,
        JWTClaimKey.TOKEN_ID.value: uuid.uuid4 ().hex,
        JWTClaimKey.ISSUED_AT.value: now,
        JWTClaimKey.EXPIRY.value: now + settings.API_AUTH_ACCESS_TOKEN_LIFETIME_S,
        JWTClaimKey.SUBJECT.value: sub_uuid.hex }

    return jwt.encode (access_token_payload, settings.API_AUTH_JWT_PRIVATE_KEY, algorithm=settings.API_AUTH_JWT_ALGORITHM)

def create_refresh_token (sub_uuid, revocation_cursor, expiration_time):
    now = utc_epoch_now ()

    if expiration_time is None:
        expiration_time = now + settings.API_AUTH_REFRESH_TOKEN_LIFETIME_S

    revocation_cursor_b = bytes (str (revocation_cursor), 'utf-8')

    refresh_token_payload = {
        JWTClaimKey.TYPE.value: JWTType.REFRESH.value,
        JWTClaimKey.VERSION.value: settings.API_AUTH_JWT_VERSION,
        JWTClaimKey.TOKEN_ID.value: jwt_id_fernet_instance.encrypt (sub_uuid.bytes + revocation_cursor_b).decode (),
        JWTClaimKey.ISSUED_AT.value: now,
        JWTClaimKey.EXPIRY.value: expiration_time,
        JWTClaimKey.SUBJECT.value: sub_uuid.hex }

    return jwt.encode (refresh_token_payload, settings.API_AUTH_JWT_PRIVATE_KEY, algorithm=settings.API_AUTH_JWT_ALGORITHM)

def create_access_refresh_token_pair (sub_uuid, revocation_cursor):
    return (create_access_token (sub_uuid), create_refresh_token (sub_uuid, revocation_cursor, None))

def rotate_refresh_token (sub_uuid, revocation_cursor, expiration):
    return (create_access_token (sub_uuid), create_refresh_token (sub_uuid, revocation_cursor, expiration))

def extract_access_token_data (access_token):
    decoded_token = jwt.decode (access_token, key=settings.API_AUTH_JWT_PUBLIC_KEY, algorithms=[settings.API_AUTH_JWT_ALGORITHM])

    if decoded_token [JWTClaimKey.TYPE.value] != JWTType.ACCESS.value:
        raise jwt.exceptions.InvalidTokenError ()

    return uuid.UUID (decoded_token [JWTClaimKey.SUBJECT.value])

def extract_refresh_token_data (refresh_token):
    decoded_token = jwt.decode (refresh_token, key=settings.API_AUTH_JWT_PUBLIC_KEY, algorithms=[settings.API_AUTH_JWT_ALGORITHM])

    if decoded_token [JWTClaimKey.TYPE.value] != JWTType.REFRESH.value:
        raise jwt.exceptions.InvalidTokenError ()

    payload_sub_uuid = uuid.UUID (decoded_token [JWTClaimKey.SUBJECT.value])

    token_id_crypt = decoded_token [JWTClaimKey.TOKEN_ID.value]
    token_id_plain = jwt_id_fernet_instance.decrypt (bytes (token_id_crypt, 'utf-8'))
    token_id_sub_uuid = uuid.UUID (token_id_plain [:16].hex ())

    if payload_sub_uuid != token_id_sub_uuid:
        raise jwt.exceptions.InvalidTokenError ()

    revocation_tag = int (token_id_plain [16:])
    expiration = decoded_token [JWTClaimKey.EXPIRY.value]

    return (payload_sub_uuid, revocation_tag, expiration)

def decompose_access_token (access_token, decode_key=None):
    if decode_key is None:
        decode_key = settings.API_AUTH_JWT_PUBLIC_KEY

    return jwt.decode (access_token, key=decode_key, algorithms=[settings.API_AUTH_JWT_ALGORITHM], options={'verify_exp': False})
