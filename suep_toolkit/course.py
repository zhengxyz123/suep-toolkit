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

import json
import re
import socket
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from suep_toolkit.util import AuthServiceError, VPNError


class ElectCourseError(Exception):
    """选课失败时引发此异常。"""

    def __init__(self, error: str) -> None:
        super().__init__(error)
        self.error = error


class Course:
    """一个选课类。"""

    operator_url = "https://jw.shiep.edu.cn/eams/stdElectCourse!batchOperator.action"

    def __init__(
        self,
        session: requests.Session,
        course_name: str,
        course_id: int,
        course_no: str,
        profile_id: str,
    ) -> None:
        self._session = session
        self._name = course_name
        self._id = course_id
        self._no = course_no
        self._profile_id = profile_id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name!r}, id={self._id!r}, no={self._no!r})"

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> int:
        return self._id

    @property
    def no(self) -> str:
        return self._no

    def elect(self) -> None:
        response = self._session.post(
            self.operator_url,
            params={"profileId": self._profile_id},
            data={"optype": "true", "operator0": f"{self._id}:true:0"},
            verify=False,
        )
        response.raise_for_status()

        dom = BeautifulSoup(response.text, features="html.parser")
        try:
            result = dom.select("table>tr>td>div")[0].text.strip()
        except:
            raise ElectCourseError("其它错误")
        if any([s in result for s in ["失败", "内部错误", "过快点击"]]):
            raise ElectCourseError(result)

    def cancel(self) -> None:
        response = self._session.post(
            self.operator_url,
            params={"profileId": self._profile_id},
            data={"optype": "false", "operator0": f"{self._id}:false"},
            verify=False,
        )
        response.raise_for_status()

        dom = BeautifulSoup(response.text, features="html.parser")
        try:
            result = dom.select("table>tr>td>div")[0].text.strip()
        except:
            raise ElectCourseError("其它错误")
        if any([s in result for s in ["失败", "内部错误", "过快点击"]]):
            raise ElectCourseError(result)


class CourseManagement:
    """教学管理信息系统。"""

    login_url = "https://jw.shiep.edu.cn/eams/login.action"
    course_table1_url = "https://jw.shiep.edu.cn/eams/courseTableForStd.action"
    course_table2_url = (
        "https://jw.shiep.edu.cn/eams/courseTableForStd!courseTable.action"
    )
    elect_course1_url = "https://jw.shiep.edu.cn/eams/stdElectCourse.action"
    elect_course2_url = "https://jw.shiep.edu.cn/eams/stdElectCourse!defaultPage.action"
    course_data_url = "https://jw.shiep.edu.cn/eams/stdElectCourse!data.action"

    def __init__(self, session: requests.Session) -> None:
        self._session = session
        self._course_list: list[Course] = []
        try:
            socket.create_connection(("jw.shiep.edu.cn", 443), timeout=0.5)
        except TimeoutError as error:
            raise VPNError(
                "you are not connected to the campus network, please turn on vpn"
            ) from error
        response = self._session.get(self.login_url, verify=False)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        if len(dom.select("div[class=auth_page_wrapper]")) > 0:
            raise AuthServiceError("must login first")

        self._session.get(self.course_table1_url, verify=False).raise_for_status()

    def _get_course_list(self) -> None:
        response = self._session.get(self.elect_course1_url, verify=False)
        response.raise_for_status()
        for profile_id in re.finditer(r"electionProfile.id=(\d+)", response.text):
            response = self._session.get(
                self.elect_course2_url,
                params={"electionProfile.id": profile_id.group(1)},
                verify=False,
            )
            response.raise_for_status()
            if "不在选课时间内" in response.text:
                raise ElectCourseError("not within the time period")
            response = self._session.get(
                self.course_data_url,
                params={"profileId": profile_id.group(1)},
                verify=False,
            )
            legal_json_str = re.sub(
                r"(,|{)(\w+):", r'\1"\2":', response.text[18:-1]
            ).replace("'", '"')
            legal_json = json.loads(legal_json_str)
            for course in legal_json:
                self._course_list.append(
                    Course(
                        self._session,
                        course["name"],
                        course["id"],
                        course["no"],
                        profile_id.group(1),
                    )
                )

    @property
    def electable_course(self) -> Iterable[Course]:
        if len(self._course_list) == 0:
            self._get_course_list()
        yield from self._course_list


__all__ = ("CourseManagement",)
