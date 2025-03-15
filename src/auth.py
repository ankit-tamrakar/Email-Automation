import msal
import os

from dotenv import load_dotenv
from utils.logger import setlog

log = setlog("auth")

load_dotenv()


def get_access_token():
    
    TENANT_ID = os.getenv('TENANT_ID')
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=authority, client_credential=CLIENT_SECRET)
    token_result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    
    if "access_token" in token_result:
        log.info("Authentication successful.")
        return token_result["access_token"]
    else:
        log.critical(f"Authentication failed: {token_result.get('error_description')}. \n Response: {token_result}")
        return None
