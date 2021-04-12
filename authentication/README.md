## What this is about

I'm trying to implement a passwordless user signup flow.

The idea is as follows:

1. User inputs an email address in the input field on our website and hits SUBMIT.
2. We send that email address a verification email that expires in, say, 15 minutes.
   This verification email has a special one-use "magic" link in it (more on this later).
3. When the "magic link" is clicked, the user is authenticated. (This could be a signup or a )


## Implementation

Cognito custom auth flow

## Questions

- How to handle signups if you want to 
use custom user attributes?
- maybe have two different auth flows,
one for sign up, one for sign in.
- What are the consequences if we just
create a user in the user pool?
There should be some way to delete users?
- If we don't use custom user attributes

## Things to consider

- Sign up is (or should be, anyway)
not harmful if the verification code is leaked.

## Bibliography

- [Cognito magic links POC](https://github.com/leanmotherfuckers/serverless-magic-links-poc)
- [GH issue discussing this](https://github.com/aws-amplify/amplify-js/issues/1896)
