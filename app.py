# -*- coding: utf-8 -*-
import os

from flask import Flask
from flask_pymongo import PyMongo

import app_config
from graph.auth import OAuthSettings, MSALAuth

app = Flask(__name__)
app.config.from_object(app_config)
mongo = PyMongo(app)

msal_auth = MSALAuth(
    OAuthSettings(app_id=os.getenv('APP_ID'),
                  app_secret=os.getenv('APP_SECRET'),
                  redirect=os.getenv('REDIRECT_URL')),
    serialized_token_file=os.path.join(
        app_config.WORKDIR, app_config.SERIALIZED_TOKEN)
)

print(msal_auth.acquire_token_silent(msal_auth.oauth_settings.scopes,
                                     msal_auth.get_accounts()[0]))
msal_auth.save_token()
