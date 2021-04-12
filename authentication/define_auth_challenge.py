"""
Define Auth Challenge Lambda function.
This Lambda function decides whether or not to issue Tokens/pass a challenge.
"""

from .auth_config import AuthConfig
from .auth_types import CognitoEvent


def define_auth_challenge_handler(
    event: CognitoEvent, context, callback
) -> CognitoEvent:
    """
    Lambda function that determines whether or not to issue tokens.
    """

    if (
        event.request.session
        and event.response.challengeName != AuthConfig.VERIFICATION_CHALLENGE_NAME
    ):
        # We have an existing session, but wrong challenge name.
        # Fail the challenge.
        event.response.issueTokens = False
        event.response.failAuthentication = True
    elif (
        event.request.session
        and event.response.challengeName == AuthConfig.VERIFICATION_CHALLENGE_NAME
        and event.request.session[0].challengeResult is False
    ):
        # We have an existing session,
        # the challenge name is correct,
        # but the challenge result is false.
        # Fail the challenge.
        event.response.issueTokens = False
        event.response.failAuthentication = True
    elif (
        event.request.session
        and event.response.challengeName == AuthConfig.VERIFICATION_CHALLENGE_NAME
        and event.request.session[0].challengeResult is True
    ):
        # We have an existing session,
        # the challenge name is correct,
        # but the challenge result is false.
        # Fail the session.
        event.response.issueTokens = True
        event.response.failAuthentication = False
    else:
        # We don't have an existing session: create a new session.
        event.response.issueTokens = False
        event.response.failAuthentication = False
        event.response.challengeName = AuthConfig.VERIFICATION_CHALLENGE_NAME

    return event