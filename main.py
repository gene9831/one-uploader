# -*- coding: utf-8 -*-
import argparse
import os

import app_config
from account_helper import AccountHelper
from graph.auth import OAuthSettings, MSALAuth


def create_msal_auth():
    return MSALAuth(
        OAuthSettings(app_id=os.getenv('APP_ID'),
                      app_secret=os.getenv('APP_SECRET'),
                      redirect=os.getenv('REDIRECT_URL')),
        serialized_token_file=os.path.join(
            app_config.WORKDIR, app_config.SERIALIZED_TOKEN))


def account_operations(params):
    ah = AccountHelper(create_msal_auth())
    if params.list:
        ah.list()
    elif params.add:
        ah.add()
    elif params.remove:
        ah.remove()


def upload_operations(params):
    print(params)


parser = argparse.ArgumentParser(description='Onedrive uploader')
parser.set_defaults(func=lambda x: print('use -h or --help to get help'))

subparsers = parser.add_subparsers(title='subcommands')

# account args
parser_ac = subparsers.add_parser('account', help='account operations',
                                  aliases=['ac'])
group_ac = parser_ac.add_mutually_exclusive_group()
group_ac.add_argument('-l', '--list', action='store_true', help='list accounts')
group_ac.add_argument('-a', '--add', action='store_true', help='add account')
group_ac.add_argument('-r', '--remove', action='store_true',
                      help='remove account')
group_ac.set_defaults(func=account_operations)

# upload args
parser_up = subparsers.add_parser('upload', help='upload operations',
                                  aliases=['up'])
group_up = parser_up.add_mutually_exclusive_group()
group_up.add_argument('--new', help='new upload task')
group_up.set_defaults(func=upload_operations)

args = parser.parse_args()
args.func(args)
