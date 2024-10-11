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

from suep_toolkit.auth import AuthService
from suep_toolkit.util import AuthServiceError, VPNError, test_network


class CloudDrive:
    """上电云盘。"""

    sso_url = "https://pan.shiep.edu.cn/sso"

    def __init__(self, session: requests.Session) -> None:
        self._session = session
        if not test_network():
            raise VPNError(
                "you are not connected to the campus network, please turn on vpn"
            )
        response = self._session.get(
            AuthService.login_url, params={"service": self.sso_url}
        )
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        if len(dom.select("div[class=auth_page_wrapper]")) > 0:
            raise AuthServiceError("must login first")


__all__ = ("CloudDrive",)
