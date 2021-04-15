# -*- coding: utf-8 -*-
from urllib.parse import unquote_plus

from graph.auth import MSALAuth
from utils import color_print


class AccountHelper:
    def __init__(self, msal_auth: MSALAuth):
        self.msal_auth = msal_auth

    def list(self, show_all=False):
        accounts = self.msal_auth.get_accounts()

        if show_all:
            fields = ['username', 'authority_type', 'environment',
                      'home_account_id', 'local_account_id', 'realm']
        else:
            fields = ['username', 'authority_type', 'environment']

        s_line = 'No.  '
        ls = [len(s_line.strip())]
        for f in fields:
            le = len(f)
            for a in accounts:
                le = max(le, len(a[f]))

            s_line += '%s%s  ' % (f.upper(), ' ' * (le - len(f)))
            ls.append(le)

        print(s_line.strip())
        for i, a in enumerate(accounts, start=1):
            line = '%d%s  ' % (i, ' ' * (ls[0] - len(str(i))))
            for j, f in enumerate(fields, start=1):
                line += '%s%s  ' % (a[f], ' ' * (ls[j] - len(a[f])))
            print(line.strip())

        print('当前用户数: %d' % len(accounts))
        return accounts

    def add(self):
        auth_flow = self.msal_auth.initiate_auth_code_flow()
        print(auth_flow['auth_uri'])
        color_print.y('打开上面的链接，登录认证成功后会重定向到localhost，将此链接复制输入并确认')

        callback_url = input('输入localhost链接: ')
        queries = parse_queries(callback_url)

        try:
            token = self.msal_auth.acquire_token_by_auth_code_flow(auth_flow,
                                                                   queries)
            self.msal_auth.save_token()
            if 'error' in token:
                color_print.r(token)
                color_print.r(
                    '用户添加失败. 当前用户数: %d' % len(self.msal_auth.get_accounts()))
                return
        except ValueError as e:
            color_print.r(str(e))
            print('没有用户被添加')
            return

        color_print.g('用户添加成功. 当前用户数: %d' % len(self.msal_auth.get_accounts()))

    def remove(self):
        accounts = self.list()
        len_ac = len(accounts)
        print('输入你想要删除的用户的序号，多个序号使用","分隔')
        nums_str = input('序号: ')

        nums = []

        for num_str in nums_str.split(','):
            try:
                num_str = num_str.strip()
                if not num_str:
                    continue
                num = int(num_str)
                if 1 <= num <= len_ac:
                    nums.append(num)
            except ValueError as e:
                color_print.r(str(e))

        if len(nums) > 0:
            color_print.r('确认删除以下用户?')
            for num in nums:
                print('%d: %s' % (num, accounts[num - 1]['username']))

            flag = input('[N/y]: ')
        else:
            flag = 'n'

        if flag.lower() == 'y':
            for num in nums:
                self.msal_auth.remove_account(accounts[num - 1])
                self.msal_auth.save_token()
            color_print.g(
                '用户删除成功. 当前用户数: %d' % len(self.msal_auth.get_accounts()))
        else:
            print('没有用户被删除')


def parse_queries(url: str) -> dict:
    a = url.split('?', 1)
    query_str = a[1] if len(a) > 1 else ''

    queries = {}
    for kv_str in query_str.split('&'):
        kv = kv_str.split('=')
        if len(kv) == 2:
            queries[unquote_plus(kv[0])] = unquote_plus(kv[1])

    return queries
