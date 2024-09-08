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

import requests
from bs4 import BeautifulSoup
from requests.exceptions import Timeout

from suep_toolkit.util import AuthServiceError, VPNError


class ECard:
    """一卡通服务。"""

    auth_url = "http://10.168.103.76/sfrzwhlgportalHome.action"

    def __init__(self, session: requests.Session) -> None:
        self._session = session
        # 设置 5 秒的超时检测提醒用户应该开启 VPN。
        try:
            response = self._session.get(self.auth_url, timeout=5)
        except Timeout as error:
            raise VPNError(
                "response time too long, maybe you don't turn on the VPN"
            ) from error
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        if dom.find("div", attrs={"class": "auth_page_wrapper"}) is not None:
            raise AuthServiceError("must login first")
        form_data = {}
        for element in dom.find_all("input", attrs={"type": "hidden"}):
            form_data[element["name"]] = element["value"]
        response = self._session.post(self.auth_url, data=form_data)
        response.raise_for_status()


__all__ = ("ECard",)
