import json
import time

from trigger_email_service import load_data, send_email
import auth
from utils.logger import setlog, exctn_id

log = setlog("main")


if __name__ == '__main__':
    cust_data = load_data().drop_duplicates(subset=['email'])
    if cust_data.empty:
        log.critical("No customer data available. Exiting.")
        exit(1)

    try:
        with open("src/config/introduction_email.json", "r") as email_details:
            email = json.load(email_details)
    except FileNotFoundError as file_error:
        log.critical(f"File not found at src/config/introduction_email.json. Exception caught - {file_error}")
        exit(1)

    token = auth.get_access_token()
    if not token:
        log.critical("Failed to get access token. Exiting.")
        exit(1)
    total_customers = len(cust_data)
    log.info(f"Starting email dispatch to {total_customers} customers.")
    sent_to = 0
    for _, customer in cust_data.iterrows():
        success, token = send_email(
            recipient_email=customer['email'],
            subject=email["subject"],
            body=email["body"].format(reciever=customer['greeting_alias']),
            token=token,
            attachment_paths=[r"data/input/Kavamoss Natural Products.pdf"]
        )
        if success:
            sent_to += 1
            log.info(f"Successfully sent email to {customer['email']}. Total sent: {sent_to}/{total_customers}")
        time.sleep(1)

    log.info(f"Email dispatch completed. Total successful emails sent: {sent_to}/{total_customers}")

    with open("src/config/admin_emails.json", "r") as admin_email_file:
        admin_emails = json.load(admin_email_file).get("emails", [])

    for admin_email in admin_emails:
        success, token = send_email(
            recipient_email=admin_email,
            subject="Email Dispatch Summary",
            body=f"Email dispatch process completed. Successfully sent emails to {sent_to} out of {total_customers} customers.",
            token=token,
            attachment_paths=[rf"data/output/failed_emails_{exctn_id}.log"]
        )