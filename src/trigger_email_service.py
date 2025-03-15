import auth
import requests
import os
import pandas as pd
from dotenv import load_dotenv

from utils.logger import setlog

log = setlog("trigger_email_service")

load_dotenv()


def send_email(recipient_email, subject, body):
    token = auth.get_access_token()
    if not token:
        log.error(f"Could not generate auth token.")
        return

    email_body = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient_email}}
            ]
        },
        "saveToSentItems": "true"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{os.getenv('SENDER_EMAIL')}/sendMail",
            json=email_body,
            headers=headers
        )

        if response.status_code == 202:
            log.info(f"Email sent successfully to {recipient_email}")
        else:
            log.error(f"Failed to send email to user {recipient_email}: {response.text}")
    except Exception as e:
        log.critical(f"Failed to send email to user - {recipient_email}. Exception caught - {e.__str__()}")


def load_data():
    try:
        dir = "data/input/customer_email.csv"
        cust_details = pd.read_csv(dir, dtype={
            'email': str, 
            'first_name': str,
            'last_name': str
        })
        cust_details = cust_details.dropna(subset=["email"])

        cust_details["greeting_alias"] = cust_details["first_name"].fillna("").str.capitalize() + " " + cust_details["last_name"].fillna("").str.capitalize()
    
        cust_details["greeting_alias"] = cust_details["greeting_alias"].str.strip().fillna("Customer")
    except FileNotFoundError as file_error:
        log.critical(f"File not found at path - data/input/customer_email.csv. Exception caught - {file_error}")
    except Exception as e:
        log.critical(f"Unexpected error occurred while reading the CSV. Exception caught - {e.__str__()}")
    finally:
        if cust_details.empty:
            log.error(f"Customer data file is empty or doesn't contain relevant data. Please ensure the data integrity is maintained.")
            return pd.DataFrame()
        else:
            return cust_details
