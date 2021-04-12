from .auth_config import AuthConfig
from .auth_types import CognitoEvent
from typing import Tuple


def verify_auth_challenge_handler(event, context):
    """
    Verify Auth Challenge Response Lambda Trigger
    https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-verify-auth-challenge-response.html

    TODO make the magic link one-use only:
    generate a secret 6-digit number and revoke it on successful use.
    Or really even an increment-only counter would work.

    actually I think we don't have to worry about making it one-use because
    Amazon might already do it for us: these would be separate auth challenges.
    But I'm not sure how Cognito is able to separate the auth challenges.
    What I mean by this is suppose a user starts an auth challenge.
    Then they click the magic link.
    How does Cognito know which auth challenge this is for?
    have to read more about this.

    So it doesn't know what auth challenge this is for.
    That's why it's important for the client to be on the same browser window
    to ensure "continuity of challenge"

    Ahh, OK, so there are a few solutions:

    - use custom user attributes on user accounts in Cognito.
      See posts [here](https://tschoffelen.medium.com/serverless-magic-links-with-aws-cognito-92eff1351123)
      and GH issue discussion.
      I think this is actually a good idea, overwriting the custom user attribute
      ensures that emails are one-use only.
      [here]https://github.com/aws-amplify/amplify-js/issues/1896)
    - Dehydrate and rehydrate the user session (see GH issue)

    """
    import time

    verification_code = event.request.privateChallengeParameters.answer
    email_address, timestamp = decode_verification_code(verification_code)
    current_time = int(time.time())
    # Check if the challengeAnswer is equal to the verification code,
    # the email in the verificationCode is equal to publicChallengeParameters.email_address,
    # and that the challengeAnswer has not expired (15 minutes).
    if (
        event.request.challengeAnswer == verification_code
        and email_address == event.request.userAttributes.email
        and timestamp + AuthConfig.VERIFICATION_CODE_VALIDITY_DURATION >= current_time
    ):
        event.response.answerCorrect = True
    else:
        event.response.answerCorrect = False

    return event


def decode_verification_code(verification_code: str) -> Tuple[str, int]:
    """
    Decode the verification code
    FIXME: For now, the verification code is not encoded
    """
    import json

    verification_object = json.loads(verification_code)
    assert hasattr(verification_object, "email_address") and hasattr(
        verification_object, "timestamp"
    )

    return (verification_object.email_address, verification_object.timestamp)
