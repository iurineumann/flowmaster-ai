# backend/utils/authlib_client.py

import os
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

# Pull environment variables
config_dict = {
    "MICROSOFT_CLIENT_ID": os.environ.get("AZURE_CLIENT_ID"),
    "MICROSOFT_CLIENT_SECRET": os.environ.get("AZURE_CLIENT_SECRET"),
    "MSGRAPH_TENANT_ID": os.environ.get("MSGRAPH_TENANT_ID", "common")
}
config = Config(environ=config_dict)
oauth = OAuth(config)

# Define the scopes we want on INITIAL LOGIN.
# Note: We removed ADO_SCOPE to avoid the static scope limit error.
DEFAULT_SCOPES = [
    "openid", 
    "profile", 
    "email", 
    "offline_access",
    os.environ.get("MSGRAPH_SCOPE", "https://graph.microsoft.com/.default")
]

# Register the "microsoft" client
oauth.register(
    name='microsoft',
    client_id=config("MICROSOFT_CLIENT_ID"),
    client_secret=config("MICROSOFT_CLIENT_SECRET"),
    server_metadata_url=(
        f"https://login.microsoftonline.com/"
        f"{config('MSGRAPH_TENANT_ID')}/v2.0/.well-known/openid-configuration"
    ),
    client_kwargs={
        'scope': " ".join(DEFAULT_SCOPES),
        'response_type': 'code',
        'prompt': 'select_account',
        # ✅ FIX: Enable PKCE (Mandatory for this flow)
        'code_challenge_method': 'S256',
    }
)