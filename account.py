# -*- coding: utf-8 -*-
import argparse
import os

import app_config
from graph.auth import MSALAuth, OAuthSettings
from helpers.account_helper import AccountHelper


def create_msal_auth():
    return MSALAuth(
        OAuthSettings(app_id=os.getenv('APP_ID'),
                      app_secret=os.getenv('APP_SECRET'),
                      redirect=os.getenv('REDIRECT_URL')),
        serialized_token_file=app_config.SERIALIZED_TOKEN)


def operations(args):
    if args.list:
        AccountHelper(create_msal_auth()).list()
    elif args.add:
        AccountHelper(create_msal_auth()).add()
    elif args.remove:
        AccountHelper(create_msal_auth()).remove()


parser = argparse.ArgumentParser(description='Onedrive account management tool')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-l', '--list', action='store_true', help='list accounts')
group.add_argument('-a', '--add', action='store_true', help='add account')
group.add_argument('-r', '--remove', action='store_true', help='remove account')

parser.set_defaults(func=operations)

cmd_args = parser.parse_args()
cmd_args.func(cmd_args)
