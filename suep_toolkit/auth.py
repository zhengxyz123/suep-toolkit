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


import time

import requests
import requests.cookies
from bs4 import BeautifulSoup

from suep_toolkit import user_agent


class AuthServiceError(Exception):
    pass


class AuthService:
    """登陆统一身份认证平台。"""

    login_url = "https://ids.shiep.edu.cn/authserver/login"
    logout_url = "https://ids.shiep.edu.cn/authserver/logout"
    need_captcha_url = "https://ids.shiep.edu.cn/authserver/needCaptcha.html"
    captcha_image_url = "https://ids.shiep.edu.cn/authserver/captcha.html"

    def __init__(
        self,
        service: str,
        user_name: str,
        password: str,
        remember_me: bool = False,
        **kwargs
    ) -> None:
        self._service = service

        response = requests.get(
            self.login_url,
            params={"service": self._service} | kwargs,
            headers={"User-Agent": user_agent},
        )
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        if "应用未注册" in response.text:
            raise AuthServiceError("unregistered application")
        self._session_id = response.cookies["JSESSIONID_ids2"]
        # 以下字典存储的是 web 端登陆界面中表单里的各个字段名和值。
        self._form_data = {"username": user_name, "password": password}
        if remember_me:
            self._form_data["rememberMe"] = "on"
        # 获取不在浏览器中显示的 input 标签的字段名和值，它们对于登陆来说也是必须的。
        # 这些值可能是随机的生成的，需要解析 HTML 并获取。
        for element in dom.find_all("input", attrs={"type": "hidden"}):
            self._form_data[element["name"]] = element["value"]

        self._status = 0
        self._need_captcha = False

    def need_captcha(self) -> bool:
        """检查需要登陆的用户是否需要填写验证码。"""
        if self._status != 0:
            raise AuthServiceError("wrong auth step")
        self._status += 1

        # 是否需要填写验证码是动态获取的，其核心逻辑未知。
        jar = requests.cookies.RequestsCookieJar()
        jar.set("JSESSIONID_ids2", self._session_id)
        response = requests.get(
            self.need_captcha_url,
            params={"username": self._form_data["username"], "_": int(time.time())},
            headers={"User-Agent": user_agent},
            cookies=jar,
        )
        response.raise_for_status()

        if "true" in response.text:
            self._need_captcha = True
            return True
        self._status += 1
        return False

    def get_captcha_image(self) -> bytes:
        """获取验证码。

        若无需填写验证码，则返回长度为 0 的字节对象；否则返回一定长度的字节对象，其可直接保存为一个 jpeg 图像。
        """
        if self._status != 1:
            raise AuthServiceError("wrong auth step")
        if self._need_captcha:
            return b""

        jar = requests.cookies.RequestsCookieJar()
        jar.set("JSESSIONID_ids2", self._session_id)
        response = requests.get(
            self.captcha_image_url,
            params={"ts": int(time.time())},
            headers={"User-Agent": user_agent},
            cookies=jar,
        )
        response.raise_for_status()

        # 根据魔术字检测文件类型是否为 jpeg 格式。
        if not (
            response.content.startswith(b"\xff\xd8\xff")
            and response.content.endswith(b"\xff\xd9")
        ):
            raise AuthServiceError("captcha image format should be jpeg")
        return response.content

    def set_captcha_code(self, captcha_code: str) -> None:
        """填写验证码。"""
        if self._status == 1 and self._need_captcha:
            assert captcha_code != ""
            self._form_data["captchaResponse"] = captcha_code
            self._status += 1

    def login(self) -> requests.Session:
        """登陆。"""
        if self._need_captcha and "captchaResponse" not in self._form_data:
            raise AuthServiceError("must provide the captcha code")
        if self._status != 2:
            raise AuthServiceError("wrong auth step")

        session = requests.Session()
        session.headers["User-Agent"] = user_agent
        session.cookies.set("JSESSIONID_ids2", self._session_id)
        response = session.post(
            self.login_url,
            data=self._form_data,
        )
        response.raise_for_status()

        if not (
            "iPlanetDirectoryPro" in session.cookies and "CASTGC" in session.cookies
        ):
            raise AuthServiceError("wrong username or password")
        return session

    @classmethod
    def logout(cls, session: requests.Session) -> None:
        """退出。"""
        response = session.get(cls.logout_url)
        response.raise_for_status()


__all__ = "AuthService", "AuthServiceError"
