# -*- coding: utf-8 -*-
def rs(s: str) -> str:
    return "\033[31m%s\033[0m" % s


def gs(s: str) -> str:
    return "\033[32m%s\033[0m" % s


def ys(s: str) -> str:
    return "\033[33m%s\033[0m" % s


def bs(s: str) -> str:
    return "\033[34m%s\033[0m" % s


def r(s: str):
    print(rs(s))


def g(s: str):
    print(gs(s))


def y(s: str):
    print(ys(s))


def b(s: str):
    print(bs(s))
