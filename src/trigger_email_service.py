import auth
import base64
import requests
import os
import pandas as pd
import time
from dotenv import load_dotenv
from utils.logger import setlog
from utils.logger import exctn_id

log = setlog("trigger_email_service")

load_dotenv()


def send_email(recipient_email, subject, body, token, attachment_paths=None):
    """
    Sends an email and returns (success, latest_token).

    success: True if email was sent successfully, False otherwise.
    latest_token: The token that was last used (may be refreshed),
                  or None if we could not get a valid token.
    """
    if not token:
        log.error("No auth token provided to send_email.")
        return False, None

    # Build base email body
    email_body = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient_email}}
            ],
            "attachments": []
        },
        "saveToSentItems": True  # Graph prefers boolean
    }

    # Add attachments if provided
    if attachment_paths:
        for file_path in attachment_paths:
            try:
                with open(file_path, "rb") as file:
                    content_bytes = base64.b64encode(file.read()).decode('utf-8')

                attachment = {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": os.path.basename(file_path),
                    "contentType": "application/octet-stream",
                    "contentBytes": content_bytes
                }
                email_body["message"]["attachments"].append(attachment)
            except Exception as e:
                log.error(f"Failed to attach {file_path}: {e}")

    current_token = token
    headers = {
        "Authorization": f"Bearer {current_token}",
        "Content-Type": "application/json"
    }

    max_retries = 3
    retries = 0

    try:
        while retries < max_retries:
            response = requests.post(
                f"https://graph.microsoft.com/v1.0/users/{os.getenv('SENDER_EMAIL')}/sendMail",
                json=email_body,
                headers=headers
            )

            if response.status_code == 202:
                log.info(f"Email sent successfully to {recipient_email}")
                return True, current_token

            elif response.status_code == 401:
                # Token expired or invalid – refresh
                log.warning("Authentication token expired or invalid. Attempting to refresh token.")
                new_token = auth.get_access_token()
                if not new_token:
                    log.critical("Token refresh failed; aborting email send.")
                    return False, None

                current_token = new_token
                headers["Authorization"] = f"Bearer {current_token}"
                continue

            else:
                log.error(f"Failed to send email to user {recipient_email}: {response.text}")
                retries += 1
                if retries < max_retries:
                    time.sleep(5)
                    log.info(f"Retrying email for user {recipient_email} (attempt {retries + 1}/{max_retries})")

        log.error(f"Exhausted retries for {recipient_email}")
        with open(f"data/output/failed_emails_{exctn_id}.log", "+a") as fail_log:
            fail_log.write(f"{recipient_email}\n")
        return False, current_token

    except Exception as e:
        log.critical(f"Failed to send email to user - {recipient_email}. Exception caught - {e}")
        return False, current_token


def load_data():
    path = "data/input/customer_email.csv"
    cust_details = pd.DataFrame()

    try:
        cust_details = pd.read_csv(path, dtype={
            'email': str,
            'first_name': str,
            'last_name': str,
            'company_name': str
        })
        cust_details = cust_details.dropna(subset=["email"])

        cust_details["greeting_alias"] = (
            cust_details["first_name"].fillna("").str.capitalize() + " " +
            cust_details["last_name"].fillna("").str.capitalize()
        ).str.strip()

        cust_details["greeting_alias"] = cust_details.apply(
            lambda x: x["company_name"]
            if x["greeting_alias"] in (None, "")
            else x["greeting_alias"],
            axis=1
        )

        log.info(f"\n{cust_details}")

    except FileNotFoundError as file_error:
        log.critical(f"File not found at path - {path}. Exception caught - {file_error}")
    except Exception as e:
        log.critical(f"Unexpected error occurred while reading the CSV. Exception caught - {e}")

    if cust_details.empty:
        log.error(
            "Customer data file is empty or doesn't contain relevant data. "
            "Please ensure the data integrity is maintained."
        )
        return pd.DataFrame()

    return cust_details
