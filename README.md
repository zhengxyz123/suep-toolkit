> 本项目仍在开发中，请勿将其用于生产环境！

# 上电工具箱

各位上海电力大学的学子们，**上电工具箱**（suep-toolkit）将上海电力大学提供的学生事务及管理系统、教务系统和能源管理等分散在各处的系统整合到一个 Python 包中，方便大家使用。

我的博客《[论上海电力大学校园网](https://zhengxyz123.github.io/coding/suep-website/)》详细讨论了各系统的前端逻辑。

> **请注意**：suep-toolkit 的原理是访问相对应的网站来获取、修改数据。若某系统需要连接 VPN 才能使用，则使用本工具箱的对应功能时也要打开 VPN。
>
> 建议使用 EasyConnect 的开源替代 [EasierConnect](https://github.com/TeamSUEP/EasierConnect)。

## 已经实现的功能

- [x] 统一身份认证平台（<https://ids.shiep.edu.cn>）
  - [x] 登陆下述各网站
- [x] 上海电力大学学生事务及管理系统（<https://estudent.shiep.edu.cn>）
  - [x] 基本信息
  - [x] 住宿记录
- [ ] 上海电力大学教务处（<https://jwc.shiep.edu.cn>）
  - [ ] 教务系统（需要 VPN）
- [ ] 一站式办事大厅（<https://ehall.shiep.edu.cn>）
  - [ ] 一卡通服务

## 用法

登陆统一身份认证平台并获取 cookies 是使用其余功能的前置步骤：

```python
from suep_toolkit import auth

# 第一个参数是想要登陆的服务的 URL，留空即可。
service = auth.AuthService("", "用户名", "密码")
# 是否需要输入验证码？
if service.need_captcha():
    # 获取并保存验证码:
    with open("captcha.jpg", "wb") as captcha_image:
        captcha_image.write(service.get_captcha_image())
    # 填写验证码:
    service.set_captcha_code("验证码")
# 登陆:
session = service.login()
# 退出:
auth.AuthService.logout(session)
```

`session` 是一个 [`requests.Session`](https://requests.readthedocs.io/en/latest/api/#requests.Session) 对象，存储了必要的 cookies。

`suep_toolkit.estudent` 模块提供了访问学生事务及管理系统的功能：

```python
from suep_toolkit import estudent

# session 即上文 service.login 的返回值，之后不再说明。
es = estudent.EStudent(session)
# 获取基本信息：
es.student_info
# 获取住宿信息：
es.accommodation_record
```
