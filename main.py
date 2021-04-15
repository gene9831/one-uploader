# -*- coding: utf-8 -*-
import argparse
import os

import app_config
from helpers.account_helper import AccountHelper
from graph.auth import OAuthSettings, MSALAuth
from helpers.upload_helper import UploadHelper


def create_msal_auth():
    return MSALAuth(
        OAuthSettings(app_id=os.getenv('APP_ID'),
                      app_secret=os.getenv('APP_SECRET'),
                      redirect=os.getenv('REDIRECT_URL')),
        serialized_token_file=app_config.SERIALIZED_TOKEN)


def account_operations(args):
    if args.list:
        AccountHelper(create_msal_auth()).list()
    elif args.add:
        AccountHelper(create_msal_auth()).add()
    elif args.remove:
        AccountHelper(create_msal_auth()).remove()


def upload_operations(args):
    if args.file:
        UploadHelper(create_msal_auth()).upload_file(
            args.file, args.onedrive_dir, args.user)


parser = argparse.ArgumentParser(description='Onedrive uploader')
parser.set_defaults(func=lambda x: print('Attach -h or --help to get help.'))

subparsers = parser.add_subparsers(title='subcommands')

# account args
parser_ac = subparsers.add_parser('account', help='account operations',
                                  aliases=['ac'])
parser_ac.set_defaults(func=account_operations)

group_ac = parser_ac.add_mutually_exclusive_group(required=True)
group_ac.add_argument('-l', '--list', action='store_true', help='list accounts')
group_ac.add_argument('-a', '--add', action='store_true', help='add account')
group_ac.add_argument('-r', '--remove', action='store_true',
                      help='remove account')

# upload args
parser_up = subparsers.add_parser('upload', help='upload operations',
                                  aliases=['up'])
parser_up.set_defaults(func=upload_operations)

group_up = parser_up.add_mutually_exclusive_group(required=True)
group_up.add_argument('-f', '--file', help='upload file')
# group_up.add_argument('-d', '--dir', help='upload directory')

parser_up.add_argument('-o', '--onedrive_dir', required=True,
                       help='upload to this directory')
parser_up.add_argument('-u', '--user',
                       help='specify user, default the first user')

cmd_args = parser.parse_args()
cmd_args.func(cmd_args)
