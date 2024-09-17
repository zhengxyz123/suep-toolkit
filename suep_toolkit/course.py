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


class CourseManagement:
    """教学管理系统。"""

    login_url = "https://jw.shiep.edu.cn/eams/login.action"
    course_table1_url = "https://jw.shiep.edu.cn/eams/courseTableForStd.action"
    course_table2_url = (
        "https://jw.shiep.edu.cn/eams/courseTableForStd!courseTable.action"
    )

    def __init__(self, session: requests.Session) -> None:
        self._session = session
        # 设置 5 秒的超时检测提醒用户应该开启 VPN。
        try:
            response = self._session.get(self.login_url, timeout=5)
        except Timeout as error:
            raise VPNError(
                "response time too long, maybe you don't turn on the VPN"
            ) from error
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        if dom.find("div", attrs={"class": "auth_page_wrapper"}) is not None:
            raise AuthServiceError("must login first")


__all__ = ("CourseManagement",)
