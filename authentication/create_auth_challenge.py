"""
Create Auth Challenge

1. Generates an encrypted verification code based on the user's email address and the timestamp now
2. Email it to the user
"""

from .auth_config import AuthConfig
from .auth_types import CognitoEvent


def create_auth_challenge_handler(event: CognitoEvent, context) -> CognitoEvent:
    """
    Lambda function that runs when we want to create an auth challenge.
    This generates a verification code (a string) that we append to the magic link,
    which will be something like remailable.com/verify?key=blablabla

    Then verify_auth_handler will check if this verification code is correct.

    TODO find some way to store some (stateful) secret code so that the
    magic link is one-use only.
    """
    import time

    if event.request.challengeName == AuthConfig.VERIFICATION_CHALLENGE_NAME:
        # generate a new secret login code
        current_time = int(time.time())

        verification_code = generate_verification_code(
            event.request.userAttributes.email, current_time
        )
        event.response.privateChallengeParameters = {"answer": verification_code}
        event.response.publicChallengeParameters = {
            "email_address": event.request.userAttributes.email
        }

        return event
    else:
        pass


def generate_verification_code(emailAddress: str, timestamp: int) -> str:
    """
    Generates a verification code from the email address and the timestamp
    encodes and hashes base64

    FIXME: actually perform some encoding here with a secret key.
    What we could do is take in a `hash_seed` parameter
    (which would be a randomly generated big enough value),
    then pass that to event.response.privateChallengeParameters.

    """
    import json
    import hashlib

    verification_code = json.dumps(
        {
            "email_address": emailAddress,
            "timestamp": timestamp,
        }
    )
    return hashlib.md5(verification_code.encode("utf-8")).hexdigest()


def send_email(emailAddress: str, verificationCode: str) -> None:
    """
    Sends an email to email address with verificationCode
    TODO: implement this
    """
    pass