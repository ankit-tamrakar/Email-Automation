import json
import time

from trigger_email_service import load_data, send_email
import auth
from utils.logger import setlog

log = setlog("main")


if __name__ == '__main__':
    cust_data = load_data()
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

    for _, customer in cust_data.iterrows():
        success, token = send_email(
            recipient_email=customer['email'],
            subject=email["subject"],
            body=email["body"].format(reciever=customer['greeting_alias']),
            token=token,
            attachment_paths=[r"data/input/Kavamoss Natural Products.pdf"]
        )

        if not success:
            # You can choose to continue instead of break, depending on behavior you want
            log.error(f"Stopping further emails due to failure for {customer['email']}")
            break

        time.sleep(1)
