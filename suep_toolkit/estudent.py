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

import requests
from bs4 import BeautifulSoup

from suep_toolkit.auth import AuthServiceError


@dataclass
class StudentInfo:
    """基本信息。"""

    student_number: str
    name: str
    gender: str
    id_number: str
    nation: str
    field: str
    college: str
    class_: str
    level: str
    length_of_schooling: int
    grade: str
    counselor_id: str
    counselor_name: str
    status: str


@dataclass
class RoomInfo:
    """住宿记录。"""

    campus: str
    building_number: str
    room_number: str
    bed_number: int
    air_conditioner_available: bool
    room_type: str
    status: str


class EStudent:
    """学生事务及管理系统。"""

    estudent_url = "https://estudent.shiep.edu.cn"
    student_info_url = "https://estudent.shiep.edu.cn/GeRCZ/JiBXX.aspx"
    accommodation_record_url = "https://estudent.shiep.edu.cn/GeRCZ/ZhuSJL.aspx"

    def __init__(self, session: requests.Session) -> None:
        self._session = session
        if not (
            "iPlanetDirectoryPro" in self._session.cookies
            and "CASTGC" in self._session.cookies
        ):
            raise AuthServiceError("must login first")

        response = self._session.get(self.estudent_url)
        response.raise_for_status()
        self._dom = BeautifulSoup(response.text, features="html.parser")

    @property
    def student_info(self) -> StudentInfo:
        """获取基本信息。"""
        response = self._session.get(self.student_info_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        student_number = dom.find_all("input", {"name": "XueHao"})[0]["value"]
        name = dom.find_all("input", {"name": "XingMing"})[0]["value"]
        gender = dom.find_all("input", {"name": "XingBie"})[0]["value"]
        id_number = dom.find_all("input", {"name": "ShenFZH"})[0]["value"]
        nation = dom.find_all("input", {"name": "MinZu"})[0]["value"]
        field = dom.find_all("input", {"name": "ZhuanYe"})[0]["value"]
        college = dom.find_all("input", {"name": "ErJXY"})[0]["value"]
        class_ = dom.find_all("input", {"name": "BanJi"})[0]["value"]
        level = dom.find_all("input", {"name": "CengCi"})[0]["value"]
        length_of_schooling = int(dom.find_all("input", {"name": "XueZi"})[0]["value"])
        grade = dom.find_all("input", {"name": "SuoZNJ"})[0]["value"]
        counselor_id = dom.find_all("input", {"name": "FuDYGH"})[0]["value"]
        counselor_name = dom.find_all("input", {"name": "FuDYXM"})[0]["value"]
        status = dom.find_all("option", {"selected": "selected"})[0].text
        return StudentInfo(
            student_number,
            name,
            gender,
            id_number,
            nation,
            field,
            college,
            class_,
            level,
            length_of_schooling,
            grade,
            counselor_id,
            counselor_name,
            status,
        )

    @property
    def accommodation_record(self) -> tuple[RoomInfo]:
        """获取住宿记录。"""
        response = self._session.get(self.accommodation_record_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        result = []
        for tr_tag in dom.find_all("tr"):
            if len(tr_tag.find_all("td")) == 0:
                continue
            info = [tag.text for tag in tr_tag.find_all("td")]
            info[3] = int(info[3])
            info[4] = not info[4] == "无"
            result.append(RoomInfo(*info))
        return tuple(result)


__all__ = "StudentInfo", "RoomInfo", "EStudent"
