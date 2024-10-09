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

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from suep_toolkit.util import AuthServiceError, VPNError, test_network


@dataclass
class AccountInfo:
    """校园卡账号信息。"""

    id: int
    name: str


@dataclass
class CardTransaction:
    """校园卡流水。"""

    pass


class ECard:
    """一卡通服务平台。"""

    auth_url = "http://10.168.103.76/sfrzwhlgportalHome.action"
    account_select_url = "http://10.168.103.76/accounttodayTrjn.action"

    def __init__(self, session: requests.Session) -> None:
        self._session = session
        self._account_info: tuple[AccountInfo] | None = None
        if not test_network():
            raise VPNError(
                "you are not connected to the campus network, please turn on vpn"
            )
        response = self._session.get(self.auth_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        if dom.find("div", attrs={"class": "auth_page_wrapper"}) is not None:
            raise AuthServiceError("must login first")
        form_data = {}
        for element in dom.find_all("input", attrs={"type": "hidden"}):
            form_data[element["name"]] = element["value"]
        response = self._session.post(self.auth_url, data=form_data)
        response.raise_for_status()

    @property
    def account(self) -> Iterable[AccountInfo]:
        if self._account_info is not None:
            yield from self._account_info
            return

        response = self._session.get(self.account_select_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        result = []
        for element in dom.select("select#account>option"):
            account_id = int(element.attrs["value"])
            account_name = element.text.strip()
            account_name = account_name[account_name.find("---") + 3 :]
            result.append(AccountInfo(account_id, account_name))
        self._account_info = tuple(result)
        yield from self._account_info

    def get_transaction(
        self,
        start_date: date,
        end_date: date | None = None,
        *,
        account: AccountInfo | None = None
    ) -> Iterable[CardTransaction]:
        if account is None:
            account = list(self.account)[0]
        if start_date == date.today() and end_date is None:
            return self._get_today_transaction(account)
        else:
            if end_date is None:
                end_date = start_date
            return self._get_history_transaction(start_date, end_date, account)

    def _get_today_transaction(self, account: AccountInfo) -> Iterable[CardTransaction]:
        yield CardTransaction()

    def _get_history_transaction(
        self, start_date: date, end_date: date, account: AccountInfo
    ) -> Iterable[CardTransaction]:
        if end_date > start_date:
            raise ValueError("end_date must be before start_date")
        if (date.today() - end_date).days > 30:
            raise ValueError("data can only be queried within 30 days")
        yield CardTransaction()


__all__ = ("ECard",)
