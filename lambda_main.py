from typing import Tuple

import base64
import io
import email
import json

# import logging
import tempfile

import boto3
from flask import Flask, jsonify, render_template

from config import Config

from users import get_config_for_user, set_config_for_user, renew_user_token

# remarkable imports:
from rmapy.document import ZipDocument
from rmapy.api import Client


def load_email_from_s3(path: str):
    """
    Load an email object from an s3 path like `s3://foo/bar`.

    """
    # logging.info(f"Loading {path} from s3...")
    s3 = boto3.resource("s3")
    virtual_file = io.BytesIO()
    s3.Object(
        bucket_name=Config.BUCKET_NAME, key=f"{Config.BUCKET_PREFIX}/{path}"
    ).download_fileobj(virtual_file)

    virtual_file.seek(0)

    try:
        return email.message_from_bytes(virtual_file.read())
    except:
        raise TypeError(f"Path {path} was not a valid email .eml binary.")


def register_user(user_email: str, code: str):
    rm = Client()
    rm.register_device(code, save_to_file=False)
    new_cfg = rm.renew_token(save_to_file=False)
    set_config_for_user(user_email, new_cfg)
    return True


def extract_pdf(message: email.message.Message) -> Tuple[str, bytes]:
    """
    Get a PDF from the email.

    TODO: This is the thing to change to accommodate more than one PDF per msg.
    """
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
            return True
        else:
            raise ValueError("No PDF in this message.")

    return (filename, filebytes)


def transfer_file_to_remarkable(user_email: str, fname, fbytes):
    # logging.info(f"Asking for {user_email} credentials...")
    cfg = renew_user_token(user_email)
    rm = Client(config_dict=cfg)
    # Annoychops; gotta save to disk. Bummski!
    tfile = tempfile.NamedTemporaryFile(prefix=fname, suffix=".pdf")
    tfile.write(fbytes)
    tfile.seek(0)

    doc = ZipDocument(doc=tfile.name)
    rm.upload(doc)


def transfer_s3_path_to_remarkable(path: str):
    message = load_email_from_s3(path)
    user_email = str(message["From"])
    # logging.info(user_email)
    fname, fbytes = extract_pdf(message)
    # logging.info(str(fname))
    transfer_file_to_remarkable(user_email, str(fname), fbytes)


def upload_handler(event, context):
    # bucket = event['Records'][0]['s3']['bucket']['name']
    key = event["Records"][0]["s3"]["object"]["key"]
    path = key.split("/")[-1]
    transfer_s3_path_to_remarkable(path)
    return {"statusCode": 200, "body": "Success"}


APP = Flask(__name__)


@APP.route("/")
def main():
    return render_template("index.html")
