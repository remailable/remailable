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
mock_delete_user = MagicMock(return_value=True)


@pytest.fixture(autouse=True)
def mock_lambdamain(monkeypatch):
    monkeypatch.setattr(lambda_main, "register_user", mock_register_user)
    monkeypatch.setattr(lambda_main, "send_email_if_enabled", mock_send_email)
    monkeypatch.setattr(lambda_main, "delete_user", mock_delete_user)

@pytest.fixture
def message_with_one_attachment():
    """
    Pytest fixture 
    """
    with open("./test_data/pdf_one_email.eml", "rb") as f:
        message = email.message_from_binary_file(f)
        return message

@pytest.fixture
def message_with_epub_attachment():
    with open("./test_data/epub_email.eml", "rb") as f:
        message = email.message_from_binary_file(f)
        return message

@pytest.fixture
def message_with_multiple_attachments():
    with open("./test_data/multiple_emails.eml", "rb") as f:
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
def regular_message():
    """
    Pytest fixture for regular email
    (not a code, not an unsubscribe, no attachment)
    """
    with open("./test_data/regular_email.eml", "rb") as f:
        message = email.message_from_binary_file(f)
        return message

@pytest.fixture
def unsubscribe_message():
    """
    Pytest fixture for unsubscribe email
    """
    with open("./test_data/unsubscribe_email.eml", "rb") as f:
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

@pytest.fixture
def test_epub():
    """
    Returns the binary data of test_pdf.epub
    for testing purposes
    """
    # FIXME
    with open("./test_data/test_pdf.epub", "rb") as epub:
        return epub.read()

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
    mock_register_user.assert_called_with("Lieu Zheng Hong <lieu@lieuzhenghong.com>", "ABCD1234")
    mock_send_email.assert_called_with(
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

def test_extract_pdf_no_pdf(regular_message):
    filename, filebytes = lambda_main.extract_pdf(regular_message)
    assert (filename, filebytes) == (False, False)
    mock_send_email.assert_called_with(
        "Lieu Zheng Hong <lieu@lieuzhenghong.com>",
        subject="A problem with your document :(",
        message="Unfortunately, a problem occurred while processing your email. Remailable only supports PDF attachments for now. If you're still encountering issues, please get in touch with Jordan at remailable@matelsky.com or on Twitter at @j6m8.",
    )

def test_extract_pdf_unsubscribe(unsubscribe_message):
    filename, filebytes = lambda_main.extract_pdf(unsubscribe_message)
    assert (filename, filebytes) == (False, False)
    mock_delete_user.assert_called_once_with(
        "Lieu Zheng Hong <lieu@lieuzhenghong.com>",
    )

def test_extract_files_from_email_unsubscribe(unsubscribe_message):
    result = lambda_main.extract_files_from_email(unsubscribe_message)
    assert result ==  lambda_main.ParseMessageResult(
        sent_from="Lieu Zheng Hong <lieu@lieuzhenghong.com>",
        status=lambda_main.MessageStatus.UNSUBSCRIBE,
        subject="Please Unsubscribe Me",
        extracted_files=[]
    )

def test_extract_files_from_email_register(message_with_code):
    result = lambda_main.extract_files_from_email(message_with_code)
    assert result ==  lambda_main.ParseMessageResult(
        sent_from="Lieu Zheng Hong <lieu@lieuzhenghong.com>",
        status=lambda_main.MessageStatus.REGISTER,
        subject="ABCD1234",
        extracted_files=[]
    )

def test_extract_files_from_email_pdf(message_with_one_attachment, test_pdf):
    result = lambda_main.extract_files_from_email(message_with_one_attachment)
    assert result == lambda_main.ParseMessageResult(
        sent_from="Lieu Zheng Hong <lieu@lieuzhenghong.com>",
        status=lambda_main.MessageStatus.SUCCESS,
        subject="Re: Test email with test PDF",
        extracted_files=[("test_pdf.pdf", test_pdf)]
    )

def test_extract_files_from_email_epub(message_with_epub_attachment, test_epub):
    result = lambda_main.extract_files_from_email(message_with_epub_attachment)
    assert result["sent_from"] == "Lieu Zheng Hong <lieu@lieuzhenghong.com>"
    assert result["status"] == lambda_main.MessageStatus.SUCCESS
    assert result["subject"] == "Email with an EPUB attachment"
    assert result["extracted_files"] == [("test_pdf.epub", test_epub)]

def test_extract_files_from_email_multiple(message_with_multiple_attachments, test_epub, test_pdf):
    result = lambda_main.extract_files_from_email(message_with_multiple_attachments)
    assert result["sent_from"] == "Lieu Zheng Hong <lieu@lieuzhenghong.com>"
    assert result["status"] == lambda_main.MessageStatus.SUCCESS
    assert result["subject"] == "An email with multiple files"
    assert sorted(result["extracted_files"]) == sorted([("test_pdf.epub", test_epub), ("test_pdf.pdf", test_pdf)]
    )

def test_extract_files_from_email_error(message_with_one_attachment, test_pdf):
    # TODO
    assert True
