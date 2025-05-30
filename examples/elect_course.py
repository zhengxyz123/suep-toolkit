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

# 这是一个自动化选课脚本，帮助你快速选到心仪的课程。
# 你唯一需要做的就是以命令行参数传递一个选课列表文件，然后根据程序的提示输入一些信息。
# 选课列表文件的每一行都是一个教务系统上的课程序号（形如“xxxxxxx.xx”，其中“x”代表一位数字）。

import getpass
import os
import sys
import warnings
from pathlib import Path

from suep_toolkit import auth
from suep_toolkit import course as course_system
from suep_toolkit.util import AuthServiceError, VPNError


def main(courses_file: Path) -> int:
    warnings.simplefilter("ignore")
    if not courses_file.exists():
        print(f"文件'{courses_file}'不存在")
        return 1
    if "SUEP_USERNAME" in os.environ and "SUEP_PASSWORD" in os.environ:
        service = auth.AuthService(
            os.environ["SUEP_USERNAME"], os.environ["SUEP_PASSWORD"]
        )
    else:
        service = auth.AuthService(input("用户名: "), getpass.getpass("密码: "))
    if service.need_captcha():
        with open("captcha.jpg", "wb") as f:
            f.write(service.get_captcha_image())
        service.set_captcha_code(input("验证码: "))
        os.remove("captcha.jpg")
    try:
        service.login()
    except AuthServiceError:
        print("登陆失败")
        return 1
    try:
        course_mgr = course_system.CourseManagement(service.session)
    except VPNError:
        print("需要先启动 VPN")
        return 1
    try:
        electable_course = list(course_mgr.electable_course)
    except:
        print("读取课程列表失败, 请重试")
        return 1
    wanted_list = []
    success_list = []
    for line in courses_file.read_text().splitlines():
        course_no = line.strip()
        for course in electable_course:
            if course._no == course_no:
                wanted_list.append(course)
    print("已选课程:")
    for course in wanted_list:
        print(f"{course._no} - {course.name}")
    print("按下回车开始选课...")
    input()
    while len(success_list) != len(wanted_list):
        for course in wanted_list:
            if course.id in success_list:
                continue
            try:
                course.elect()
                print(f"{course.name}: 选课成功")
                success_list.append(course.id)
            except course_system.ElectCourseError as error:
                if "已经选过" in error.error:
                    success_list.append(course.id)
                print(f"{course.name}: {error.error}")
            except KeyboardInterrupt:
                return 0
            except:
                return 0
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("需要提供一个选课列表文件")
        exit(1)
    else:
        exit(main(Path(sys.argv[1])))
