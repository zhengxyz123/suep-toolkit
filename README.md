> 本项目仍在开发中，请勿将其用于生产环境！

# 上电工具箱

各位上海电力大学的学子们，**上电工具箱**（suep-toolkit）将上海电力大学提供的学生事务及管理系统、教务系统和能源管理等分散在各处的系统整合到一个 Python 包中，方便大家使用。

> **请注意**：suep-toolkit 的原理是访问相对应的网站来获取、修改数据。若某系统需要连接 VPN 才能使用，则使用本工具箱的对应功能时也要打开 VPN。
>
> 建议使用 EasyConnect 的开源替代 [EasierConnect](https://github.com/TeamSUEP/EasierConnect)。

## 已经实现的功能

- [x] 统一身份认证平台（<https://ids.shiep.edu.cn>）
  - [x] 登陆下述各网站
- [ ] 上海电力大学学生事务及管理系统（<https://estudent.shiep.edu.cn>）
  - [ ] 基本信息
  - [ ] 住宿记录
- [ ] 上海电力大学教务处（<https://jwc.shiep.edu.cn>）
  - [ ] 教务系统（需要 VPN）
- [ ] 能源管理（<http://10.50.2.206>）
  - [ ] 电表（需要 VPN）
