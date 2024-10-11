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
from typing import Any, Iterable

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
        response = self._session.get(self.estudent_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        if len(dom.select("div[class=auth_page_wrapper]")) > 0:
            raise AuthServiceError("must login first")

    @property
    def student_info(self) -> StudentInfo:
        """获取基本信息。"""
        response = self._session.get(self.student_info_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        student_number = dom.select("input[name=XueHao]")[0].attrs["value"]
        name = dom.select("input[name=XingMing]")[0].attrs["value"]
        gender = dom.select("input[name=XingBie]")[0].attrs["value"]
        id_number = dom.select("input[name=ShenFZH]")[0].attrs["value"]
        nation = dom.select("input[name=MinZu]")[0].attrs["value"]
        field = dom.select("input[name=ZhuanYe]")[0].attrs["value"]
        college = dom.select("input[name=ErJXY]")[0].attrs["value"]
        class_ = dom.select("input[name=BanJi]")[0].attrs["value"]
        level = dom.select("input[name=CengCi]")[0].attrs["value"]
        # 请跟我读：学（xue）制（zhi）！
        # 这么明显的一个错误放在这里这么多年愣是没有改！
        length_of_schooling = int(dom.select("input[name=XueZi]")[0].attrs["value"])
        grade = dom.select("input[name=SuoZNJ]")[0].attrs["value"]
        counselor_id = dom.select("input[name=FuDYGH]")[0].attrs["value"]
        counselor_name = dom.select("input[name=FuDYXM]")[0].attrs["value"]
        status = dom.select("option[selected=selected]")[0].text
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
    def accommodation_record(self) -> Iterable[RoomInfo]:
        """获取住宿记录。"""
        response = self._session.get(self.accommodation_record_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        for line in dom.select("table>tr"):
            if len(line.select("th")) > 0:
                continue
            info: list[Any] = [tag.text for tag in line.select("td")]
            info[3] = int(info[3])
            info[4] = not info[4] == "无"
            yield RoomInfo(*info)


__all__ = "StudentInfo", "RoomInfo", "EStudent"
