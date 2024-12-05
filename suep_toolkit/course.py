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

import requests
from bs4 import BeautifulSoup

from suep_toolkit.util import AuthServiceError, VPNError, test_network


class ElectCourseError(Exception):
    """选课失败时引发此异常。"""

    pass


class Course:
    """一个选课类。"""

    def __init__(
        self,
        session: requests.Session,
        course_name: str,
        course_id: int,
        course_no: str,
    ) -> None:
        self._session = session
        self._name = course_name
        self._id = course_id
        self._no = course_no

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name!r}, id={self._id!r}, no={self._no!r})"

    def elect(self) -> None:
        pass


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
        if not test_network():
            raise VPNError(
                "you are not connected to the campus network, please turn on vpn"
            )
        response = self._session.get(self.login_url)
        response.raise_for_status()
        dom = BeautifulSoup(response.text, features="html.parser")

        if len(dom.select("div[class=auth_page_wrapper]")) > 0:
            raise AuthServiceError("must login first")

        self._session.get(self.course_table1_url).raise_for_status()

    @property
    def electable_course(self):
        response = self._session.get(self.elect_course1_url)
        response.raise_for_status()
        for profile_id in re.finditer(r"electionProfile.id=(\d+)", response.text):
            response = self._session.get(
                self.elect_course2_url,
                params={"electionProfile.id": profile_id.group(1)},
            )
            response.raise_for_status()
            if "不在选课时间内" in response.text:
                raise ElectCourseError("not within the time period")
            response = self._session.get(
                self.course_data_url, params={"profileId": profile_id.group(1)}
            )
            legal_json = re.sub(r"(,|{)(\w+):", r'\1"\2":', response.text[18:-1])
            legal_json = legal_json.replace("'", '"')
            course_json = json.loads(legal_json)
            for course in course_json:
                yield Course(self._session, course["name"], course["id"], course["no"])


__all__ = ("CourseManagement",)
