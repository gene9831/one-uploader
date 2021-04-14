# -*- coding: utf-8 -*-
import json
import os
from dataclasses import dataclass, field

import msal

from utils import color_print


@dataclass
class OAuthSettings:
    app_id: str
    app_secret: str
    redirect: str
    scopes: list[str] = field(  # scopes大小写敏感
        default_factory=lambda: ['User.Read', 'Files.ReadWrite.All'])
    authority: str = 'https://login.microsoftonline.com/common'


class MSALAuth(msal.ConfidentialClientApplication):
    def __init__(self, oauth_settings: OAuthSettings,
                 serialized_token_file=None):
        self.oauth_settings = oauth_settings
        self.serialized_token_file = serialized_token_file
        self.token_cache = msal.SerializableTokenCache()

        serialized_token = self.load_token()
        if serialized_token:
            self.token_cache.deserialize(serialized_token)

        super().__init__(client_id=oauth_settings.app_id,
                         client_credential=oauth_settings.app_secret,
                         authority=oauth_settings.authority,
                         token_cache=self.token_cache)

    def initiate_auth_code_flow(
            self,
            scopes=None,
            redirect_uri=None,
            state=None,
            prompt=None,
            login_hint=None,
            domain_hint=None,
            claims_challenge=None,
    ):
        if scopes is None:
            scopes = self.oauth_settings.scopes
        if redirect_uri is None:
            redirect_uri = self.oauth_settings.redirect
        return super().initiate_auth_code_flow(scopes, redirect_uri, state,
                                               prompt, login_hint, domain_hint,
                                               claims_challenge)

    def load_token(self):
        if not self.serialized_token_file:
            return None
        # 文件是否存在
        if not os.path.isfile(self.serialized_token_file):
            return None
        with open(self.serialized_token_file, 'r', encoding='utf8') as f:
            serialized_token = f.read()

        # 判断是否为json格式
        try:
            json.loads(serialized_token)
        except ValueError as e:
            color_print.r(str(e))
            return None
        return serialized_token

    def save_token(self):
        if self.serialized_token_file and self.token_cache.has_state_changed:
            try:
                with open(self.serialized_token_file, 'w',
                          encoding='utf8') as f:
                    f.write(self.token_cache.serialize())
            except PermissionError as e:
                color_print.r(str(e))
