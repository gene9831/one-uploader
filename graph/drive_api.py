# -*- coding: utf-8 -*-
import time

import requests

from utils import color_print

BASE_URL = 'https://graph.microsoft.com/v1.0/me/drive'


def put_content(access_token: str,
                onedrive_item_path: str,
                local_file_data: bytes, ):
    url = '{}/root:{}:/content'.format(BASE_URL, onedrive_item_path)
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }
    return request_retry('PUT', url, headers=headers, data=local_file_data)


def create_upload_session(access_token: str,
                          filename: str,
                          onedrive_item_path: str):
    url = '{}/root:{}:/createUploadSession'.format(BASE_URL, onedrive_item_path)
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }
    data = {
        '@microsoft.graph.conflictBehavior': 'rename',
        'name': filename
    }
    return request_retry('POST', url, headers=headers, json=data)


def request_retry(method, url, **kwargs):
    retry_cnt = 1
    while True:
        try:
            return requests.request(method, url, **kwargs)
        except requests.exceptions.RequestException as e:
            color_print.y(str(e))
            delay = 2 ** retry_cnt
            delay = delay if delay <= 60 else 60
            color_print.y('第%d次重试，%ds后重试' % (retry_cnt, delay))
            time.sleep(delay)
            retry_cnt += 1
