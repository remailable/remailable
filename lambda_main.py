from typing import Tuple, TypedDict

import base64
import io
import email
import json

import tempfile

import boto3
from botocore.exceptions import ClientError
from flask import Flask, jsonify, render_template

from config import Config

from users import (
    get_config_for_user,
    set_config_for_user,
    renew_user_token,
    delete_user,
)

# remarkable imports:
from rmapy.document import ZipDocument
from rmapy.api import Client


def plog(*args):
    """
    This is a helper function to log to CloudWatch.

    Unfortunately, there's something broken in the stdlib logging calls
    somewhere deep inside our dependencies, and it breaks Lambda when
    we try to run logging.info() et al. So we're stuck with stdout
    for now.
    """
    print(*args)


def send_email_if_enabled(to: str, subject: str, message: str):
    """
    Send an email from `Config.EMAIL_SENDER` to the recipient.

    This is predominantly used to log successful/errorful outputs
    back to the user.
    """
    if not Config.SEND_EMAILS:
        plog("Config.SEND_EMAILS is False; skipping receipt message.")
        return

    ses = boto3.client("ses", region_name=Config.AWS_REGION)

    _suffix = """
\n
To delete your account and unsubscribe from all future emails, reply to this message with the subject line "UNSUBSCRIBE" (case-insensitive).
    """
    try:
        response = ses.send_email(
            Destination={
                "ToAddresses": [to],
            },
            Message={
                "Body": {
                    "Text": {
                        "Charset": "UTF-8",
                        "Data": message + _suffix,
                    },
                },
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": subject,
                },
            },
            Source=Config.EMAIL_SENDER,
        )
    except ClientError as e:
        plog("Encountered error:", e)
    else:
        plog(f"Sent email to {to}.")


def load_email_from_s3(path: str):
    """
    Load an email object from an s3 path like `s3://foo/bar`.

    """
    plog(f"Loading {path} from s3...")
    s3 = boto3.resource("s3")
    virtual_file = io.BytesIO()
    s3.Object(
        bucket_name=Config.BUCKET_NAME, key=f"{Config.BUCKET_PREFIX}/{path}"
    ).download_fileobj(virtual_file)

    virtual_file.seek(0)

    try:
        return email.message_from_bytes(virtual_file.read())
    except:
        plog(f"Path {path} was not a valid email .eml binary.")


def register_user(user_email: str, code: str):
    rm = Client()
    rm.register_device(code, save_to_file=False)
    new_cfg = rm.renew_token(save_to_file=False)
    set_config_for_user(user_email, new_cfg)
    return True

from typing import List, TypedDict
from enum import Enum
FileTuple = Tuple[str, bytes]

class MessageStatus(Enum):
    SUCCESS = 0
    FAILURE = 1
    UNSUBSCRIBE = 2
    REGISTER = 3
    FILE_TOO_BIG = 4 # unused

class ParseMessageResult(TypedDict):
    sent_from: str
    subject: str
    status: MessageStatus
    extracted_files: List[FileTuple]

def extract_files_from_email(message: email.message.Message) -> ParseMessageResult:
    """
    Parses an email Message and returns a ParseMessageResult:
    1. Is there a subject and from in the email? If no, return.
    2. Does the subject contain the word "unsubscribe"? If yes, return.
    3. Is the subject 8 letters long? If yes, return.
    4. Otherwise:
        - Walk through the message and grab all parts that match
          "application/pdf;" or "application/epub".
        - Return a ParseMessageResult with those files.
    """
    subject: str = message.get("Subject")
    sent_from: str = message.get("From")
    assert subject and sent_from
    if "unsubscribe" in subject.lower():
        return ParseMessageResult(
            sent_from=sent_from,
            subject=subject,
            status=MessageStatus.UNSUBSCRIBE, 
            extracted_files=[])
    # FIXME: need a more robust check here
    if subject and len(subject) == 8:
        return ParseMessageResult(
            sent_from=sent_from,
            subject=subject,
            status=MessageStatus.REGISTER, 
            extracted_files=[])
    # Now we're done parsing the subject, we should check if there are any attachments
    files: List[FileTuple] = []
    for part in message.walk():
        if "application/pdf;" in part["Content-Type"]:
            filename = part.get_filename() or "Remailable_Attachment.pdf"
            filebytes = base64.b64decode(part.get_payload())
            assert type(filename) == str
            files.append((filename, filebytes))
        elif "application/epub" in part["Content-Type"]:
            filename = part.get_filename() or "Remailable_Attachment.epub"
            filebytes = base64.b64decode(part.get_payload())
            assert type(filename) == str
            files.append((filename, filebytes))
    if files:
        return ParseMessageResult(
            sent_from=sent_from,
            subject = subject,
            status=MessageStatus.SUCCESS, 
            extracted_files=files)
    else:
        # Couldn't parse any files, empty
        return ParseMessageResult(
            sent_from=sent_from,
            subject = subject,
            status=MessageStatus.FAILURE, 
            extracted_files=files)

def extract_pdf(message: email.message.Message) -> Tuple[str, bytes]:
    """
    Get a PDF from the email.

    TODO: This is the thing to change to accommodate more than one PDF per msg.
    """

    # Handle unsubscribes:
    subject = message.get("Subject")
    if "unsubscribe" in subject.lower():
        plog(f"Permanently removing user {message.get('From')}.")
        delete_user(message.get("From"))
        return (False, False)

    filename = None
    filebytes = None
    for part in message.walk():
        if "application/pdf;" in part["Content-Type"]:
            filename = part.get_filename() or "Remailable_Attachment.pdf"
            filebytes = base64.b64decode(part.get_payload())
            break
    else:
        # Let's try getting the subjectline and body and see if there's a code
        # for us to gobble up in there :)
        code = message.get("Subject")
        if code and len(code) == 8:
            register_user(message.get("From"), code)
            plog(f"Registered a new user {message.get('From')}.")
            send_email_if_enabled(
                message.get("From"),
                subject="Your email address is now verified!",
                message="Your verification succeeded, and you can now email documents to your reMarkable tablet. Try responding to this email with a PDF attachment!",
            )
            return (False, False)
        else:
            send_email_if_enabled(
                message.get("From"),
                subject="A problem with your document :(",
                message="Unfortunately, a problem occurred while processing your email. Remailable only supports PDF attachments for now. If you're still encountering issues, please get in touch with Jordan at remailable@matelsky.com or on Twitter at @j6m8.",
            )
            plog(f"ERROR: Encountered no PDF in message from {message.get('From')}")
            return (False, False)

    return (filename, filebytes)


def transfer_file_to_remarkable(user_email: str, fname, fbytes):
    plog(f"* Asking for {user_email} credentials...")
    cfg = renew_user_token(user_email)
    rm = Client(config_dict=cfg)
    # Annoychops; gotta save to disk. Bummski!
    tfile = tempfile.NamedTemporaryFile(prefix=fname, suffix=".pdf")
    tfile.write(fbytes)
    tfile.seek(0)

    plog(f"* Generating zip...")
    doc = ZipDocument(doc=tfile.name)
    plog(f"* Uploading to device.")
    rm.upload(doc)
    plog("Success.")
    send_email_if_enabled(
        user_email,
        subject="Your document is on the way!",
        message=f"Your document, '{fname}', has been successfully sent to your reMarkable.",
    )


def handle_message_result(result: ParseMessageResult) -> None:
    """
    Takes in a ParseMessageResult and sends the appropriate emails/
    transfers the approriate files depending on the message status
    """
    if result["status"] == MessageStatus.UNSUBSCRIBE:
        plog(f"Permanently removing user {result['sent_from']}.")
        delete_user(result["sent_from"])
    elif result["status"] == MessageStatus.REGISTER:
        register_user(result["sent_from"], result["subject"])
        plog(f"Registered a new user {result['sent_from']}.")
        send_email_if_enabled(
            to=result["sent_from"],
            subject="Your email address is now verified!",
            message="Your verification succeeded, and you can now email documents to your reMarkable tablet. Try responding to this email with a PDF attachment!",
        )
    elif result["status"] == MessageStatus.FAILURE:
        send_email_if_enabled(
            to=result["sent_from"],
            subject="A problem with your document :(",
            message="Unfortunately, a problem occurred while processing your email. Remailable only supports PDF attachments for now. If you're still encountering issues, please get in touch with Jordan at remailable@matelsky.com or on Twitter at @j6m8.",
        )
        plog(f"ERROR: Encountered no files I could pass in message from {result['sent_from']}")
    else:
        for fname, fbytes in result["extracted_files"]:
            transfer_file_to_remarkable(result["sent_from"], fname, fbytes)
    

def transfer_s3_path_to_remarkable(path: str):
    message = load_email_from_s3(path)
    handle_message_result(extract_files_from_email(message))


def upload_handler(event, context):
    """
    This is the function that is called when an event takes place in s3.

    """
    # bucket = event['Records'][0]['s3']['bucket']['name']
    key = event["Records"][0]["s3"]["object"]["key"]
    path = key.split("/")[-1]
    transfer_s3_path_to_remarkable(path)
    return {"statusCode": 200, "body": "Success"}


APP = Flask(__name__)


@APP.route("/")
def main():
    return render_template("index.html")
