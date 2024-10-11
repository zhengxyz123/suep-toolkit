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
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from suep_toolkit.util import AuthServiceError, VPNError, test_network


@dataclass
class MeterState:
    """电表状态。"""

    recharges: int
    reskwh: float
    power: int
    voltage: int
    power_factor: float
    limit: int
    state: int


@dataclass
class RechargeInfo:
    """充值信息。"""

    oid: int
    type: str
    money: float
    quantity: int
    time: datetime


class ElectricityManagement:
    """能源管理。"""

    home_url = "http://10.50.2.206"
    meter_state_url = "http://10.50.2.206/api/charge/query"
    recharge_info_url = "http://10.50.2.206/api/charge/user_account"
    recharge_url = "http://10.50.2.206/api/charge/Submit"
    get_room_url = "http://10.50.2.206/api/charge/GetRoom"

    def __init__(self, session: requests.Session) -> None:
        self._session = session
        if not test_network():
            raise VPNError(
                "you are not connected to the campus network, please turn on vpn"
            )
        response = self._session.get(self.home_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        if len(dom.select("div[class=auth_page_wrapper]")) > 0:
            raise AuthServiceError("must login first")

    @property
    def meter_state(self) -> MeterState:
        """获取电表状态。"""
        response = self._session.get(
            self.meter_state_url, params={"_dc": int(time.time())}
        )
        response.raise_for_status()
        data = response.json()

        if not data["success"]:
            raise ValueError("api returned an error")
        recharges = int(data["info"][0]["recharges"])
        reskwh = float(data["info"][0]["reskwh"])
        power = int(data["info"][0]["P"])
        voltage = int(data["info"][0]["U"])
        power_factor = float(data["info"][0]["FP"])
        limit = int(data["info"][0]["limit"])
        state = int(data["info"][0]["state"])
        return MeterState(recharges, reskwh, power, voltage, power_factor, limit, state)

    @property
    def recharge_info(self) -> Iterable[RechargeInfo]:
        """获取历次的电表充值账单。"""
        response = self._session.get(
            self.recharge_info_url, params={"_dc": int(time.time())}
        )
        response.raise_for_status()
        data = response.json()

        if not data["success"]:
            raise ValueError("api returned an error")
        for info in data["info"]:
            oid = int(info["oid"])
            recharge_type = info["type"]
            money = float(info["money"])
            quantity = int(info["quantity"])
            recharge_time = datetime.fromisoformat(info["datetime"])
            yield RechargeInfo(oid, recharge_type, money, quantity, recharge_time)

    def recharge(self, building: str, room: str, kwh: int) -> None:
        """充值电费。"""
        response = self._session.post(
            self.recharge_url,
            params={"_dc": int(time.time())},
            data={"building": building, "room": room, "kwh": kwh},
        )
        response.raise_for_status()
        data = response.json()

        if not data["success"]:
            raise ValueError(data["info"])

    def recharge_my_room(self, kwh: int) -> None:
        """给自己的宿舍充值电费。"""
        response = self._session.get(
            self.get_room_url, params={"_dc": int(time.time())}
        )
        response.raise_for_status()
        data = response.json()

        if not data["success"]:
            raise ValueError("api returned an error")
        self.recharge(data["info"][0]["building"], data["info"][0]["room"], kwh)


__all__ = ("ElectricityManagement",)
