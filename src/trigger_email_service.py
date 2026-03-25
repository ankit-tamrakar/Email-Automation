import auth
import base64
import requests
import os
import pandas as pd
import time
import csv
from dotenv import load_dotenv
from utils.logger import setlog, exctn_id

log = setlog("trigger_email_service")
load_dotenv()

def send_email(recipient_email, subject, body, token, first_name="", last_name="", company_name="", attachment_paths=None):
    if not token:
        log.error("No auth token provided to send_email.")
        return False, None

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
        "saveToSentItems": True
    }

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
    failure_reason = "Unknown Error"

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
                log.warning("Authentication token expired. Refreshing...")
                new_token = auth.get_access_token()
                if not new_token:
                    failure_reason = "Critical: Token refresh failed"
                    log.critical(failure_reason)
                    break # Stop retrying if we can't get a token

                current_token = new_token
                headers["Authorization"] = f"Bearer {current_token}"
                continue

            else:
                failure_reason = f"Status {response.status_code}: {response.text[:100]}"
                log.error(f"Failed to send to {recipient_email}: {failure_reason}")
                retries += 1
                if retries < max_retries:
                    time.sleep(5)

        # --- Log failed email with Reason ---
        failed_csv_path = f"data/output/failed_emails_{exctn_id}.csv"
        file_exists = os.path.isfile(failed_csv_path)
        
        with open(failed_csv_path, "a", encoding="utf-8", newline='') as fail_log:
            writer = csv.writer(fail_log)
            if not file_exists:
                writer.writerow(["email", "first_name", "last_name", "company_name", "failure_reason"])
            
            writer.writerow([
                recipient_email, 
                "" if pd.isna(first_name) else first_name, 
                "" if pd.isna(last_name) else last_name, 
                "" if pd.isna(company_name) else company_name,
                failure_reason
            ])
            
        return False, current_token

    except Exception as e:
        log.critical(f"Critical exception for {recipient_email}: {e}")
        return False, current_token

def load_data():
    path = "data/output/failed_emails_20260325174356.csv"
    try:
        cust_details = pd.read_csv(path, dtype=str).fillna("")
        cust_details = cust_details.dropna(subset=["email"])
        cust_details = cust_details[cust_details["email"] != ""]

        cust_details["greeting_alias"] = (
            cust_details["first_name"].str.capitalize() + " " +
            cust_details["last_name"].str.capitalize()
        ).str.strip()

        cust_details["greeting_alias"] = cust_details.apply(
            lambda x: x["company_name"] if not x["greeting_alias"] else x["greeting_alias"],
            axis=1
        )
        log.info(f"Loaded {len(cust_details)} records.")
        return cust_details
    except Exception as e:
        log.critical(f"Data loading failed: {e}")
        return pd.DataFrame()