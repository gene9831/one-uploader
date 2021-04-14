# -*- coding: utf-8 -*-
import os

from dotenv import load_dotenv
import pathlib

load_dotenv()

# 工作目录
WORK_DIR = pathlib.Path(__file__).parent.absolute()
# 缓存信息基础路径
CACHE_DIR = os.path.join(WORK_DIR, '.cache')

if not os.path.exists(CACHE_DIR):
    # 创建目录
    os.mkdir(CACHE_DIR)
elif not os.path.isdir(CACHE_DIR):
    # 不是目录
    raise Exception('%s is not a directory' % CACHE_DIR)

# token保存路径
SERIALIZED_TOKEN = os.path.join(CACHE_DIR, 'serialized_token.json')
# 上传分片大小(MB): 5的正整数倍，最大60。根据自己的上传速度调节
UPLOAD_CHUNK_SIZE = 10
