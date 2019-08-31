import os
import re
import secrets
import boto3
from string import digits


def define_auth_challenge(event, _context):
    if "response" not in event:
        event["response"] = {}
    if (
        event["request"].get("session")
        and len(event["request"]["session"]) >= 3
        and not event["request"]["session"][-1].get("challengeResult")
    ):
        event["response"]["issueTokens"] = False
        event["response"]["failAuthentication"] = True
    elif event["request"].get("session") and event["request"]["session"][-1].get(
        "challengeResult"
    ):
        event["response"]["issueTokens"] = True
        event["response"]["failAuthentication"] = False
    else:
        event["response"]["issueTokens"] = False
        event["response"]["failAuthentication"] = False
        event["response"]["challengeName"] = "CUSTOM_CHALLENGE"

    return event


def create_auth_challenge(event, _context):
    rand = secrets.SystemRandom()
    if "response" not in event:
        event["response"] = {}
    if not event["request"].get("session"):
        secret_login_code = "".join(rand.choice(digits) for _ in range(6))
        send_email(event["request"]["userAttributes"]["email"], secret_login_code)
    else:
        previous_challenge = event["request"]["session"][-1]
        data = re.search(r"CODE-(\d*)", previous_challenge.get("challengeMetadata"))
        secret_login_code = data.group()[0]
    event["response"]["publicChallengeParameters"] = {
        "email": event["request"]["userAttributes"]["email"]
    }
    event["response"]["privateChallengeParameters"] = {
        "secretLoginCode": secret_login_code
    }

    event["response"]["challengeMetadata"] = f"CODE-{secret_login_code}"

    return event


def verify_auth_challenge_response(event, _context):
    expected_answer = event["request"]["privateChallengeParameters"]["secretLoginCode"]
    if "response" not in event:
        event["response"] = {}
    event["response"]["answerCorrect"] = False
    if event["request"]["challengeAnswer"] == expected_answer:
        event["response"]["answerCorrect"] = True

    return event


def pre_sign_up(event, _context):
    if "response" not in event:
        event["response"] = {}
    event["response"]["autoConfirmUser"] = True
    event["response"]["autoVerifyEmail"] = True
    return event


def send_email(email, code):
    ses = boto3.client("ses")
    ses.send_email(
        Source=os.getenv("SES_FROM_ADDRESS"),
        Destination={"ToAddresses": [email]},
        Message={
            "Body": {
                "Html": {
                    "Charset": "UTF-8",
                    "Data": "<html><body><p>This is your secret login code:</p>"
                    f"<h3>{code}</h3></body></html>",
                },
                "Text": {"Charset": "UTF-8", "Data": f"Your secret login code: {code}"},
            },
            "Subject": {"Charset": "UTF-8", "Data": "Your secret login code"},
        },
    )
