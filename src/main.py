from trigger_email_service import load_data, send_email

from utils.logger import setlog

log = setlog("main")


if __name__ == '__main__':
    cust_data = load_data()
    try:
        with open("src/config/introduction_email.txt", "r") as email_body:
            body = email_body.read()
    except FileNotFoundError as file_error:
        log.critical(f"File not found at src/config/introduction_email.txt. Exception caught - {file_error}")
        exit(1)

    for _, customer in cust_data.iterrows():
        send_email(
            customer['email'],
            "Introduction to Kavamoss Natural Products",
            body.format(reciever=customer['greeting_alias'])
        )
