from django.conf import settings
from twilio.rest import Client as TwilioClient
from twilio.base import exceptions

__all__ = ['dispatch_verification_code', 'validate_verification_code', 'send_sms']

twilio_client = TwilioClient (settings.TWILIO ['ACCOUNT_SID'], settings.TWILIO ['AUTH_TOKEN'])

def dispatch_verification_code (e164_phone_number):
    twilio_client \
        .verify \
        .services (settings.TWILIO ['VERIFY_SERVICE_ID']) \
        .verifications \
        .create (to=e164_phone_number, channel='sms')

def validate_verification_code (e164_phone_number, verification_code):
    try:
        verification = twilio_client \
            .verify \
            .services (settings.TWILIO ['VERIFY_SERVICE_ID']) \
            .verification_checks \
            .create (to=e164_phone_number, code=verification_code)
    except exceptions.TwilioRestException:
        return False

    return verification.status == 'approved'

def send_sms (e164_phone_number, msg_body):
    twilio_client.messages.create (body=msg_body, to=e164_phone_number, from_=settings.TWILIO ['PHONE_NUMBER'])
