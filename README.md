# Onedrive 上传文件命令行工具

## 安装

1. 安装 [`python3`](https://www.python.org/)
2. 安装依赖

   ```bash
   git clone https://github.com/gene9831/one-uploader.git
   cd one-uploader
   # 需要虚拟环境请自行创建
   pip install -r requirements.txt
   ```

## 使用

### Step1

编辑`.env`文件，填入以下信息。获取 `app_id` 和 `app_secret` 的具体步骤可参考[这里](https://docs.microsoft.com/zh-cn/graph/tutorials/python?tutorial-step=2)

```ini
# .env
APP_ID=your_app_id
APP_SECRET=you_app_secret
REDIRECT_URL=http://localhost:5000/callback
```

### Step2

添加用户，输入以下命令，按步骤操作即可

```bash
python account.py -a
```

其他用户操作使用 `-h` 或 `--help` 参数获取帮助

### Step3

上传文件，暂时只支持单个文件

```bash
# 上传文件帮助信息
$ python upload.py -h
usage: upload.py [-h] -f FILE -o ONE_DIR [-u USER]

Onedrive file upload tool

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  file to be uploaded
  -o ONE_DIR, --one_dir ONE_DIR
                        upload to this directory
  -u USER, --user USER  specify Onedrive user, default the first one
```

例如

```bash
$ python upload.py -f /local/file -o /Onedrive/directory -u username@mail.com
 filename  |  size   |   per   |  speed  |   eta
-----------+---------+---------+---------+---------
 file      |  100.0M |   99.9% |  8.8M/s |  23m59s
```

> 使用 `nohup` 和 `&` 可在后台运行
