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

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
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
class CardStatus:
    """校园卡状态。"""

    reminder: float
    frozen: bool
    lost: bool


@dataclass
class CardTransaction:
    """校园卡流水。"""

    time: datetime
    type: str
    shop_name: str
    amount: float
    status: str
    comment: str


class ECard:
    """一卡通服务平台。"""

    auth_url = "http://10.168.103.76/sfrzwhlgportalHome.action"
    account_select_url = "http://10.168.103.76/accounttodayTrjn.action"
    card_status_url = "http://10.168.103.76/accountcardUser.action"
    today_transaction_url = "http://10.168.103.76/accounttodatTrjnObject.action"
    history_transaction0_url = "http://10.168.103.76/accounthisTrjn.action"
    history_transaction1_url = "http://10.168.103.76/accounthisTrjn1.action"
    history_transaction2_url = "http://10.168.103.76/accounthisTrjn2.action"
    history_transaction3_url = "http://10.168.103.76/accounthisTrjn3.action"
    history_transaction_list_url = "http://10.168.103.76/accountconsubBrows.action"

    def __init__(self, session: requests.Session) -> None:
        self._session = session
        self._account_info: list[AccountInfo] = []
        if not test_network():
            raise VPNError(
                "you are not connected to the campus network, please turn on vpn"
            )
        response = self._session.get(self.auth_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        if len(dom.select("div[class=auth_page_wrapper]")) > 0:
            raise AuthServiceError("must login first")
        form_data = {}
        for element in dom.select("input[type=hidden]"):
            form_data[element.attrs["name"]] = element.attrs["value"]
        response = self._session.post(self.auth_url, data=form_data)
        response.raise_for_status()

    @property
    def account(self) -> Iterable[AccountInfo]:
        """获取账号列表。"""
        if len(self._account_info) > 0:
            yield from self._account_info
            return

        response = self._session.get(self.account_select_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        for element in dom.select("select#account>option"):
            account_id = int(element.attrs["value"])
            account_name = element.text.strip()
            account_name = account_name[account_name.find("---") + 3 :]
            account = AccountInfo(account_id, account_name)
            self._account_info.append(account)
            yield account

    @property
    def status(self) -> CardStatus:
        """获取校园卡状态。"""
        response = self._session.get(self.card_status_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")
        text = (
            dom.text.replace("\n", "")
            .replace("\t", "")
            .replace("\xa0", "")
            .replace(" ", "")
        )

        reminder = float(re.search(r"余额：(\d+\.\d+)元", text).group(1))
        frozen = re.search(r"冻结状态：(.{2})", text).group(1) != "正常"
        lost = re.search(r"挂失状态：(.{2})", text).group(1) != "正常"
        return CardStatus(reminder, frozen, lost)

    def get_transaction(
        self,
        date1: date,
        date2: date | None = None,
        *,
        account: AccountInfo | None = None,
    ) -> Iterable[CardTransaction]:
        """查询流水。

        在 `date1` 和 `date2` 中：

        1. 如果只提供了 `date1`，那么返回 `date1` 那天的流水；
        2. 如果 `date1` 和 `date2` 都提供了且不是同一天，那么返回两天之间的所有流水（包括 `date1` 和 `date2`）；
        3. 如果 `date1` 和 `date2` 是同一天，那么和 (1) 相同。

        由于一卡通服务的限制，最多只能查询 30 天的历史流水和 1 天的当日流水。
        """
        if account is None:
            account = list(self.account)[0]
        if date1 == date2:
            date1, date2 = date1, None
        if date2 is not None:
            if date2 > date.today() or date1 > date.today():
                raise ValueError("date cannot be in the future")
            if date1 >= date2:
                date1, date2 = date2, date1
            if date2 == date.today():
                yield from self._get_today_transaction(account)
                yield from self._get_history_transaction(
                    date1, date2 - timedelta(days=1), account
                )
            else:
                yield from self._get_history_transaction(date1, date2, account)
        else:
            if date1 > date.today():
                raise ValueError("date cannot be in the future")
            if date1 == date.today():
                yield from self._get_today_transaction(account)
            else:
                yield from self._get_history_transaction(date1, date1, account)

    def _get_today_transaction(self, account: AccountInfo) -> Iterable[CardTransaction]:
        response = self._session.post(
            self.today_transaction_url,
            data={"account": account.id, "inputObject": "all"},
        )
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        pages_info = dom.select("tr.bl>td>div[align=center]")[0].text
        page_count = int(re.search(r"共(\d+)页", pages_info).group(1))
        for page in range(1, page_count + 1):
            response = self._session.post(
                self.today_transaction_url,
                data={
                    "pageVo.pageNum": page,
                    "inputObject": "all",
                    "account": account.id,
                },
            )
            dom = BeautifulSoup(response.text, features="html.parser")
            for element in dom.select("tr.listbg,tr.listbg2"):
                tran_time = datetime.fromisoformat(
                    element.find_all("td")[0].text.replace("/", "-")
                )
                tran_type = element.find_all("td")[3].text
                shop_name = element.find_all("td")[4].text.strip()
                amount = float(element.find_all("td")[5].text)
                status = element.find_all("td")[8].text
                comment = element.find_all("td")[9].text.strip()
                yield CardTransaction(
                    tran_time, tran_type, shop_name, amount, status, comment
                )

    def _get_history_transaction(
        self, start_date: date, end_date: date, account: AccountInfo
    ) -> Iterable[CardTransaction]:
        if (end_date - start_date).days > 30:
            raise ValueError("data can only be queried within 30 days")
        response = self._session.get(self.history_transaction0_url)
        response.raise_for_status()
        response = self._session.post(
            self.history_transaction1_url,
            data={"account": account.id, "inputObject": "all"},
        )
        response.raise_for_status()
        input_start_date = f"{start_date:%Y%m%d}"
        input_end_date = f"{end_date:%Y%m%d}"
        response = self._session.post(
            self.history_transaction2_url,
            data={"inputStartDate": input_start_date, "inputEndDate": input_end_date},
        )
        response.raise_for_status()
        response = self._session.post(self.history_transaction3_url)
        response.raise_for_status()

        dom = BeautifulSoup(response.text, features="html.parser")
        pages_info = dom.select("tr.bl>td>div[align=center]")[0].text
        page_count = int(re.search(r"共(\d+)页", pages_info).group(1))
        for page in range(1, page_count + 1):
            response = self._session.post(
                self.history_transaction_list_url,
                data={
                    "inputStartDate": input_start_date,
                    "inputEndDate": input_end_date,
                    "pageNum": page,
                },
            )
            response.raise_for_status()
            dom = BeautifulSoup(response.text, features="html.parser")
            for element in dom.select("tr.listbg,tr.listbg2"):
                tran_time = datetime.fromisoformat(
                    element.find_all("td")[0].text.replace("/", "-")
                )
                tran_type = element.find_all("td")[3].text
                shop_name = element.find_all("td")[4].text.strip()
                amount = float(element.find_all("td")[5].text)
                status = element.find_all("td")[8].text
                comment = element.find_all("td")[9].text.strip()
                yield CardTransaction(
                    tran_time, tran_type, shop_name, amount, status, comment
                )


__all__ = ("ECard",)
