# 上电工具箱

各位上海电力大学的学子们，**上电工具箱**（suep-toolkit）将上海电力大学提供的一卡通服务、教务系统和能源管理等分散在各处的系统整合到一个 Python 包中，方便大家使用。

我的博客《[论上海电力大学校园网](https://zhengxyz123.github.io/coding/suep-website/)》详细讨论了各系统的前端逻辑。

> **请注意**：suep-toolkit 的原理是访问相对应的网站来获取、修改数据。若某系统需要连接 VPN 才能使用，则使用本工具箱的对应功能时也要打开 VPN。
>
> 建议使用 EasyConnect 的开源替代 [EasierConnect](https://github.com/TeamSUEP/EasierConnect)。

## 已经实现的功能

- [x] 统一身份认证平台（<https://ids.shiep.edu.cn>）
- [x] 学生事务及管理系统（<https://estudent.shiep.edu.cn>）
- [x] 教务处（<https://jwc.shiep.edu.cn>）
  - [x] 教学周显示
  - [x] 教学管理信息系统（需要 VPN）
- [ ] 一站式办事大厅（<https://ehall.shiep.edu.cn>）
  - [x] 一卡通服务（需要 VPN）
- [x] 能源管理（<http://10.50.2.206>，需要 VPN）
- [ ] 上电云盘（<https://pan.shiep.edu.cn>, 需要 VPN） 
- [x] 其它小工具

## 用法

### 统一身份认证平台

登陆统一身份认证平台并获取 cookies 是使用其余功能的前置步骤：

```python
from suep_toolkit import auth

service = auth.AuthService("用户名", "密码")
# 是否需要输入验证码？
if service.need_captcha():
    # 获取并保存验证码:
    with open("captcha.jpg", "wb") as captcha_image:
        captcha_image.write(service.get_captcha_image())
    # 填写验证码:
    service.set_captcha_code("验证码")
# 登陆:
service.login()
# 退出:
service.logout()
```

`AuthService` 有唯一的属性 `AuthService.session`，它是一个 [`requests.Session`](https://requests.readthedocs.io/en/latest/api/#requests.Session) 对象，存储了必要的 cookies。

### 学生事务及管理系统

`suep_toolkit.estudent` 模块提供了访问学生事务及管理系统的功能：

```python
from suep_toolkit import estudent

es = estudent.EStudent(service.session)
# 获取基本信息：
es.student_info
# 获取住宿信息：
for record in es.accommodation_record:
    print(record)
```

### 教学管理信息系统

`suep_toolkit.course` 提供了访问教学管理系统的功能：

```python
from suep_toolkit import course

course_system = course.CourseManagement(service.session)
# 获取选课列表（在选课期间可用）
course_list = list(course_system.electable_course)
# 选课
course_list[0].elect()
# 退课
course_list[0].cancel()
```

项目的 `examples/elect_course.py` 文件提供了一个简单的自动化选课功能，可通过如下命令使用：

```bash
python -m examples.elect_course <一个包含了一堆课程序号的文件>
```

### 能源管理

`suep_toolkit.electricity` 提供了访问能源管理系统的功能。

无论之前登陆与否，访问能源管理系统都需要再次登陆：

```python
# service 必须与下面一行所展示的精确相符，都为 22 个字符！
service = auth.AuthService("用户名", "密码", service="http://10.50.2.206:80/", renew="true")
```

> 登陆时会有大概率跳转到不存在的地址 `http://10.50.2.206:80/undefined` 并引发错误。此时 cookies 已经设置完成，忽略错误即可。

登陆成功之后，我们便能正常访问能源管理系统：

```python
from suep_toolkit import electricity

em = electricity.ElectricityManagement(service.session)
# 获取电表参数：
em.meter_state
# 要充值的电量，单位为千瓦时，类型为正整数
kwh = 100
# 充值电费（以一号学生公寓的 A101 房间为例）：
em.recharge("C1", "A101", kwh)
# 给自己的宿舍充值电费：
em.recharge_my_room(kwh)
# 获取历次的电表充值账单：
for info in em.recharge_info:
    print(info)
```

**若充值电费成功会扣除校园卡里面的钱，请慎用充值功能！**

### 一站式办事大厅

`suep_toolkit.ehall` 的子模块可以访问一站式办事大厅中的一些应用。

#### 一卡通服务

`suep_toolkit.ehall.ecard` 可以查询自己的一卡通状态及消费流水：

```python
from datetime import date
from suep_toolkit.ehall import ecard

my_card = ecard.ECard(service.session)
# 获取一卡通状态，包括余额以及冻结、挂失状态：
my_card.status
# 获取账号列表，不过正常情况下每人只有一个账号：
for account in my_card.account:
    print(account)
# 获取流水：
for transaction in my_card.get_transaction(date.today()):
    print(transaction)
```

`get_transaction` 方法比较复杂，可查看文档字符串获取更详细的用法。

### 其它小工具

`suep_toolkit.util` 提供了一些有用的小玩意儿：

```python
from suep_toolkit import util

# 测试设备是否连接到校园网：
util.test_network()
# 返回当前教学周：
util.semester_week()
```
