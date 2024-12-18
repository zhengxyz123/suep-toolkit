# suep-toolkit, A toolkit for students at Shanghai University of Electric Power.
#
# Copyright (c) 2024 zhengxyz123
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from queue import Queue

import requests
from bs4 import BeautifulSoup


class AuthServiceError(Exception):
    """当未登陆或登陆失败时引发此异常。"""

    pass


class VPNError(Exception):
    """当疑似未开启 VPN 时引发此异常。"""

    pass


def test_network(timeout: float = 0.5) -> bool:
    """检测设备是否连接学校内网。

    若超时时间小于 0.5 秒，则可能会有误报。
    """
    ip_addrs = ["10.50.2.206", "10.166.18.114", "10.166.19.26", "10.168.103.76"]
    test_result = Queue()

    def test_helper(addr: str) -> None:
        try:
            socket.create_connection((addr, 80), timeout=timeout)
            test_result.put(1)
        except TimeoutError:
            pass

    with ThreadPoolExecutor(max_workers=5) as executor:
        for addr in ip_addrs:
            executor.submit(test_helper, addr)
    count = 0
    while not test_result.empty():
        count += test_result.get()
    return count / len(ip_addrs) >= 0.5


def semester_week() -> int:
    """获取当前教学周。

    特别地，`-1` 表示暑假，`-2` 表示寒假。
    """
    jwc_url = "https://jwc.shiep.edu.cn/"
    response = requests.get(jwc_url)
    response.raise_for_status()
    dom = BeautifulSoup(response.text, features="html.parser")

    semeter_start = date.fromisoformat(dom.select("div#semester_start")[0].text)
    semeter_end = date.fromisoformat(dom.select("div#semester_end")[0].text)
    if (date.today() - semeter_start).days < 0 or (date.today() - semeter_end).days > 0:
        return -1 if date.today().month > 5 else -2
    else:
        return (date.today() - semeter_start).days // 7


__all__ = (
    "AuthServiceError",
    "VPNError",
    "test_network",
    "semester_week",
)
