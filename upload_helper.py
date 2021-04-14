# -*- coding: utf-8 -*-
import dataclasses
import datetime
import hashlib
import json
import math
import os
import signal
import time
from typing import Optional

import requests

import app_config
from graph import drive_api
from graph.auth import MSALAuth
from utils import color_print


@dataclasses.dataclass
class UploadInfo:
    filename: str
    size: int
    local_file_path: str
    sha1: str
    onedrive_dir_path: str
    onedrive_account: dict
    create_time: str
    upload_url: str = ''
    finished: int = 0
    speed: int = 0
    spend_time: float = 0
    finish_time: str = '---'
    status: str = 'pending'
    error: str = ''


class UploadHelper:
    def __init__(self, msal_auth: MSALAuth):
        self.msal_auth = msal_auth
        self.stop_flag = False

    def upload_file(self,
                    local_file_path: str,
                    onedrive_dir_path: str,
                    onedrive_user: Optional[str] = None):
        """
        上传文件至OneDrive目录下
        :param local_file_path: 本地文件路径
        :param onedrive_dir_path: 上传到的OneDrive目录的路径
        :param onedrive_user: 上传至此用户的OneDrive，默认为token_cache中的首个用户
        :return:
        """
        # 处理local_file_path
        local_file_path = strip_and_replace(local_file_path)

        if not os.path.isfile(local_file_path):
            raise FileNotFoundError('%s is not a file' % local_file_path)

        file_size = os.path.getsize(local_file_path)
        if file_size <= 0:
            color_print.y('File size is 0, nothing to be uploaded.')
            return

        # 处理onedrive_dir_path
        onedrive_dir_path = strip_and_replace(onedrive_dir_path, True)

        if not onedrive_dir_path.startswith('/'):
            onedrive_dir_path = '/' + onedrive_dir_path

        # 处理onedrive_user
        users = self.msal_auth.get_accounts(onedrive_user)
        account = users[0] if len(users) > 0 else None
        if account is None:
            raise Exception('%s is a invalid user.' % onedrive_user)

        info = UploadInfo(
            filename=os.path.split(local_file_path)[1],
            size=file_size,
            local_file_path=local_file_path,
            sha1=get_sha1(local_file_path),
            onedrive_dir_path=onedrive_dir_path,
            onedrive_account=account,
            create_time=utc_datetime_str()
        )
        self._upload(info)

    def upload_dir(self):
        pass

    def _upload(self, info: UploadInfo):
        token = self.msal_auth.acquire_token_silent(
            self.msal_auth.oauth_settings.scopes, info.onedrive_account)

        if info.size <= 4 * 1024 * 1024:
            # 小于或等于4MB的文件直接上传
            log_info(info)
            start = time.time()
            with open(info.local_file_path, 'rb') as f:
                resp_json = drive_api.put_content(
                    token['access_token'],
                    info.onedrive_dir_path + info.filename,
                    f.read()
                ).json()

            if 'id' in resp_json.keys():
                # 上传成功
                info.spend_time = time.time() - start
                info.speed = int(info.size / info.spend_time)
                info.finish_time = utc_datetime_str()
                info.status = 'finished'
                info.finished = info.size
                log_info(info)
                color_print.g('上传成功. 文件: %s' % info.filename)
            else:
                raise Exception(str(resp_json.get('error')))
            return

        # 处理超过4MB的大文件

        info_cache = 'upload-info-{}.json'.format(info.sha1)
        info_cache_path = os.path.join(app_config.CACHE_DIR, info_cache)

        if os.path.isfile(info_cache_path):
            # 已存在上传缓存信息，说明上次上传未完成
            info = read_upload_info(info_cache_path)
        else:
            # 首次保存上传信息
            write_upload_info(info_cache_path, info)

        log_info(info)

        # CTRL-C信号处理
        original_sigint_handler = signal.getsignal(signal.SIGINT)

        def sigint_handler(signum, frame):
            info.status = 'stopped'
            info.speed = 0
            write_upload_info(info_cache_path, info)

            signal.signal(signal.SIGINT, original_sigint_handler)
            self.stop_flag = True
            color_print.y('接收到CTRL-C信号，正在停止上传。再次输入CTRL-C立即停止')

        signal.signal(signal.SIGINT, sigint_handler)

        size_mb = app_config.UPLOAD_CHUNK_SIZE
        chunk_size = 1024 * 1024 * size_mb

        try:
            if not info.upload_url:
                # 创建上传会话
                resp_json = drive_api.create_upload_session(
                    token['access_token'],
                    info.filename,
                    info.onedrive_dir_path + info.filename
                ).json()
                upload_url = resp_json.get('uploadUrl')
                if upload_url:
                    info.upload_url = upload_url
                    write_upload_info(info_cache_path, info)
                else:
                    # 创建上传会话失败
                    raise Exception(str(resp_json.get('error')))
            else:
                resp_json = requests.get(info.upload_url).json()

            if 'nextExpectedRanges' not in resp_json.keys():
                # upload_url失效
                raise Exception(str(resp_json.get('error')))

            info.status = 'running'
            info.finished = int(
                resp_json['nextExpectedRanges'][0].split('-')[0])
            write_upload_info(info_cache_path, info)

            # 文件大小小于 chunk_size
            if info.size < chunk_size:
                chunk_size = math.floor(info.size / (1024 * 10)) * 1024 * 10

            with open(info.local_file_path, 'rb') as f:
                f.seek(info.finished, 0)
                upload_session = requests.Session()

                while True:
                    start = time.time()

                    chunk_start = f.tell()
                    chunk_end = chunk_start + chunk_size - 1

                    if chunk_end >= info.size:
                        left = info.size - chunk_start
                        # 将10KB作为上传最小单位（官方API最小是320bytes）
                        # 找一个大于left的值，使它为10KB的正整数倍，且最小
                        chunk_size = math.ceil(left / (1024 * 10)) * 1024 * 10
                        # 从文件末尾往前 chunk_size 个字节
                        chunk_start = f.seek(-chunk_size, 2)
                        chunk_end = info.size - 1

                    headers = {
                        'Content-Length': str(chunk_size),
                        'Content-Range': 'bytes {}-{}/{}'.format(chunk_start,
                                                                 chunk_end,
                                                                 info.size)
                    }
                    data = f.read(chunk_size)

                    resp = None
                    retry_cnt = 1
                    while resp is None:
                        try:
                            resp = upload_session.put(info.upload_url,
                                                      headers=headers,
                                                      data=data)
                            if resp.status_code >= 500:
                                # OneDrive服务器错误，稍后继续尝试
                                raise requests.exceptions.RequestException(
                                    resp.text)
                            elif resp.status_code >= 400:
                                # 文件未找到，因为其他原因被删除
                                raise Exception(str(resp.json().get('error')))
                        except requests.exceptions.RequestException as e:
                            resp = None
                            color_print.y(str(e))
                            delay = 2 ** retry_cnt
                            delay = delay if delay <= 60 else 60
                            color_print.y('第%d次重试，%ds后重试' % (retry_cnt, delay))
                            time.sleep(delay)
                            retry_cnt += 1

                    spend_time = time.time() - start
                    info.finished = chunk_end + 1
                    info.speed = int(chunk_size / spend_time)
                    info.spend_time += spend_time
                    write_upload_info(info_cache_path, info)

                    log_info(info)

                    resp_json = resp.json()
                    if 'id' in resp_json.keys():
                        # 上传完成，删除上传信息缓存
                        os.remove(info_cache_path)
                        color_print.g('上传成功. 文件: %s' % info.filename)
                        return

                    if self.stop_flag:
                        # 停止上传
                        color_print.y('上传停止. 文件: %s' % info.filename)
                        return
        except Exception as e:
            info.error = str(e)
            write_upload_info(info_cache_path, info)
            raise e


def read_upload_info(file: str, encoding: str = 'utf8'):
    with open(file, 'r', encoding=encoding) as f:
        return UploadInfo(**json.loads(f.read()))


def write_upload_info(file: str, info: UploadInfo, encoding: str = 'utf8'):
    with open(file, 'w', encoding=encoding) as f:
        f.write(json.dumps(dataclasses.asdict(info), indent=2, sort_keys=True))


def strip_and_replace(p: str, d: bool = False):
    r = p.strip().replace('\\', '/')
    if d and not p.endswith('/'):
        r += '/'
    return r


def utc_datetime_str():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def get_sha1(filename: str):
    sha1 = hashlib.sha1()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()


def multi_spaces(num: int):
    s = ''
    for _ in range(num):
        s += ' '
    return s


def log_info(info: UploadInfo):
    out = 'filename: %s\n' % info.filename
    out += '─────────┬───────────┬─────────┬─────────┬─────────\n'
    out += ' size    | finished  | per     | speed   | eta     \n'
    out += '---------+-----------+---------+---------+---------\n'
    size = human_size(info.size)
    finished = human_size(info.finished)
    per = '%.1f%%' % (info.finished / info.size * 100)
    speed = '%s/s' % human_size(info.speed)
    eta = human_sec(int(
        (info.size - info.finished) / info.speed)) if info.speed > 0 else '---'
    eta = eta if info.finished != info.size else '0s'
    out += ' {}{}| {}{}| {}{}| {}{}| {}\n'.format(
        size, multi_spaces(8 - len(size)),
        finished, multi_spaces(10 - len(finished)),
        per, multi_spaces(8 - len(per)),
        speed, multi_spaces(8 - len(speed)),
        eta
    )
    out += '─────────┴───────────┴─────────┴─────────┴─────────\n'
    print(out, end='')


def human_size(n: int) -> str:
    x = 1024
    if n < x:
        return '%dB' % n
    if n < 1000 * x:
        return '%dK' % int(n / x)
    x *= 1024
    if n < 1000 * x:
        return '%.1fM' % (n / x)
    x *= 1024
    if n < 1000 * x:
        return '%.2fG' % (n / x)


def human_sec(s: int) -> str:
    x = 60
    if s < x:
        return '%ds' % s
    if s < 60 * x:
        return '%dm%ds' % (int(s / x), s % x)
    x *= 60
    if s < 24 * x:
        return '%dh%dm' % (int(s / x), int((s % x) / 60))
    x *= 24
    return '>%dd' % int(s / x)
