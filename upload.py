# -*- coding: utf-8 -*-
import argparse
import os

import app_config
from graph.auth import MSALAuth, OAuthSettings
from helpers.upload_helper import UploadHelper


def create_msal_auth():
    return MSALAuth(
        OAuthSettings(app_id=os.getenv('APP_ID'),
                      app_secret=os.getenv('APP_SECRET'),
                      redirect=os.getenv('REDIRECT_URL')),
        serialized_token_file=app_config.SERIALIZED_TOKEN)


def operations(args):
    if args.file:
        UploadHelper(create_msal_auth()).upload_file(
            args.file, args.one_dir, args.user)


parser = argparse.ArgumentParser(description='Onedrive file upload tool')

group = parser.add_mutually_exclusive_group(required=True)

group.add_argument('-f', '--file', help='file to be uploaded')
# group.add_argument('-d', '--dir', help='directory to be uploaded')

parser.add_argument('-o', '--one_dir', required=True,
                    help='upload to this directory')
parser.add_argument('-u', '--user',
                    help='specify Onedrive user, default the first one')
parser.set_defaults(func=operations)

cmd_args = parser.parse_args()
cmd_args.func(cmd_args)
