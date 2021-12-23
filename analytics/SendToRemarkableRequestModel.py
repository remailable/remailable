from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, BooleanAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE
from config import Config

class SendToRemarkableRequestModel(Model):
    """
    Log every document event as it arrives at the lambda.
    """

    class Meta:
        table_name = "remailable-send-requests"
        region = Config.AWS_REGION
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    email = UnicodeAttribute(hash_key=True)
    date = UnicodeAttribute(range_key=True)
    upload_size = NumberAttribute(default=0)  # in bytes
    success = BooleanAttribute()
    traceback = UnicodeAttribute()
