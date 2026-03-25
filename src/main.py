import json
import time
import os
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
        with open("src/config/introduction_email.json", "r", encoding="utf-8-sig") as email_details:
            email = json.load(email_details)
    except Exception as e:
        log.critical(f"Config error: {e}")
        exit(1)

    token = auth.get_access_token()
    if not token:
        log.critical("Failed to get initial access token.")
        exit(1)

    total_customers = len(cust_data)
    sent_to = 0
    
    log.info(f"Starting dispatch to {total_customers} customers.")

    for _, customer in cust_data.iterrows():
        success, token = send_email(
            recipient_email=customer['email'],
            subject=email["subject"],
            body=email["body"].format(reciever=customer['greeting_alias']),
            token=token,
            first_name=customer['first_name'],
            last_name=customer['last_name'],
            company_name=customer['company_name'],
            attachment_paths=[r"data/input/Kavamoss Natural Products.pdf"]
        )
        if success:
            sent_to += 1
        time.sleep(1)

    log.info(f"Dispatch complete. {sent_to}/{total_customers} successful.")

    # --- Admin Summary Dispatch ---
    try:
        with open("src/config/admin_emails.json", "r", encoding="utf-8-sig") as admin_file:
            admin_emails = json.load(admin_file).get("emails", [])

        failed_log_path = f"data/output/failed_emails_{exctn_id}.csv"
        attachment_paths = [failed_log_path] if os.path.exists(failed_log_path) else []

        for admin_email in admin_emails:
            send_email(
                recipient_email=admin_email,
                subject="Email Dispatch Summary",
                body=f"Process complete.\nSuccessfully sent: {sent_to}\nTotal attempted: {total_customers}",
                token=token,
                attachment_paths=attachment_paths
            )
    except Exception as e:
        log.error(f"Failed to notify admins: {e}")