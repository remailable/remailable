import sys
import boto3

from config import Config

HELP_MESSAGE = """

Usage: python3 provision.py [COMMAND]

Commands:
    - help:             Show this message
    - verify-sender:    Verify the email sender in Config.EMAIL_SENDER
    - create-table:     Create the UserModel table for use via PynamoDB

"""


def help_and_exit():
    print(HELP_MESSAGE)
    exit(0)


def verify_sender_and_exit():
    if not Config.EMAIL_SENDER:
        print("You must specify a sender as Config.EMAIL_SENDER in config.py.")
    ses = boto3.client("ses", region_name=Config.AWS_REGION)
    response = ses.verify_email_identity(
        EmailAddress=Config.EMAIL_SENDER,
    )
    print(response)
    exit(0)
    

def create_table_and_exit():
    from users import UserModel
    if not UserModel.exists():
        UserModel.create_table(wait=True)
    exit(0)


if sys.argv[-1] in ["--help", "-h", "help"]:
    help_and_exit()

elif sys.argv[-1] in ["verify-sender"]:
    verify_sender_and_exit()
    
elif sys.argv[-1] in ["create-table"]:
    create_table_and_exit()
