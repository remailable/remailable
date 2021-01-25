import pytest
from unittest.mock import MagicMock, patch
import email

from users import UserModel
import lambda_main

class MockUserModel(UserModel):
    def exists(self):
        return True
    def create_table(self, wait=True):
        return True


mock_register_user = MagicMock(return_value=True)
mock_send_email = MagicMock()

@pytest.fixture(autouse=True)
def mock_lambdamain(monkeypatch):
    monkeypatch.setattr(lambda_main, "register_user", mock_register_user)
    monkeypatch.setattr(lambda_main, "send_email_if_enabled", mock_send_email)


@pytest.fixture
def message_with_one_attachment():
    """
    Pytest fixture 
    """
    with open("./test_data/pdf_one_email.eml", "rb") as f:
        message = email.message_from_binary_file(f)
        return message

@pytest.fixture
def message_with_code():
    """
    Pytest fixture
    """
    with open("./test_data/code_email.eml", "rb") as f:
        message = email.message_from_binary_file(f)
        return message

@pytest.fixture
def test_pdf():
    """
    Returns the binary data of test_pdf.pdf
    for testing purposes
    """
    with open("./test_data/test_pdf.pdf", "rb") as pdff:
        return pdff.read()

def test_extract_pdf_code(message_with_code):
    """
    Tests that the extract_pdf function in lambda_main
    succesfully registers a new user,
    emails the user to confirm, and
    successfully returns (False, False)
    when given an email with a 8-digit code as subject.
    """
    filename, filebytes = lambda_main.extract_pdf(message_with_code)
    assert (filename, filebytes) == (False, False)
    mock_register_user.assert_called_once_with("Lieu Zheng Hong <lieu@lieuzhenghong.com>", "ABCD1234")
    mock_send_email.assert_called_once_with(
        "Lieu Zheng Hong <lieu@lieuzhenghong.com>",
        subject="Your email address is now verified!",
        message="Your verification succeeded, and you can now email documents to your reMarkable tablet. Try responding to this email with a PDF attachment!",
    )

def test_extract_pdf_single_pdf(message_with_one_attachment, test_pdf):
    """
    Tests that the extract_pdf function in lambda_main
    successfully returns the file name and binary data of 
    test_pdf.pdf when it is attached in an email.
    """
    filename, filebytes = lambda_main.extract_pdf(message_with_one_attachment)
    assert (filename, filebytes) == ("test_pdf.pdf", test_pdf)

def test_extract_pdf_no_pdf():
    assert False