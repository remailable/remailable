from typing import Tuple

import base64
import io
import email
import tempfile

import boto3

from config import Config

from users import get_config_for_user

# remarkable imports:
from rmapy.document import ZipDocument
from rmapy.api import Client


def load_email_from_s3(path: str):
    """
    Load an email from an s3 path like `s3://foo/bar`.

    """
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
        raise ValueError("No PDF in this message.")

    return (filename, filebytes)


def transfer_file_to_remarkable(user_email: str, fname, fbytes):
    cfg = get_config_for_user(user_email)
    rm = Client(config_dict=cfg)
    # Annoychops; gotta save to disk. Bummski!

    tfile = tempfile.NamedTemporaryFile(prefix=fname, suffix=".pdf")
    tfile.write(fbytes)
    tfile.seek(0)

    doc = ZipDocument(doc=tfile.name)
    rm.upload(doc)


def transfer_s3_path_to_remarkable(path: str):
    message = load_email_from_s3(path)
    user_email = message["From"]
    fname, fbytes = extract_pdf(message)
    transfer_file_to_remarkable(user_email, fname, fbytes)
