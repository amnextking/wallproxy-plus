

# 概要 #
`wallproxy-plus`真正的配置文件是`config.py`，该文件要求符合`Python`语法并调用相关插件，对于一般用户来说会有点难以使用；所以也支持使用INI格式的`proxy.ini`作为配置文件，程序会自动转换出`config.py`，相比于自编辑`config.py`功能上有点弱化，但对于一般人来说足够了。另外`wallproxy-plus`支持插件形式，提供了一些`api`，以便提供更丰富的功能，当然这要求对`Python`有更深入的了解，一般用户无视即可。

# proxy.ini 说明 #
```
;见proxy.ini
```

# config.py 说明 #
  1. 无需求或看不懂者请无视！！
  1. 由`proxy.ini`生成的`config.py`能满足大部分需求，但有些人可能需要更自由的设置，本节说明如何手工修改`config.py`。`config.py`分两部分，一部分设置一些变量用于指示主模块如何初始化（例如监听的ip、端口等），另一部分是定义一个`config()`函数，该函数需要返回一个`find_proxy_handler(req)`函数用于决定如何处理。
  1. 第一部分
```
# 是否使用ini作为配置文件，0不使用
ini_config = 0
# 监听ip
listen_ip = '127.0.0.1'
# 监听端口
listen_port = 8086
# 是否使用通配符证书
cert_wildcard = 1
# 更新PAC时也许还没联网，等待tasks_delay秒后才开始更新
tasks_delay = 0
# WEB界面是否对本机也要求认证
web_authlocal = 1
# 登录WEB界面的用户名
web_username = 'admin'
# 登录WEB界面的密码
web_password = 'admin'
# 全局代理
global_proxy = None
```
  1. 第二部分
    * config()是运行在另一个模块（非config.py）中，你可以使用以下3个全局函数：
```
# import_from(plugin_name)，因为插件无法通过Python语法from ... import ...进行导入，所以提供完成类似功能的import_from函数
# 例入某插件mm提供A, B, C三个对象，可以
A = import_from('mm')
A, B, C = import_from('mm')

# install(plugin_name, init_function)，用于安装外部插件，例如
from plugins import m
m = install('mm', m)
# 安装之后可以通过m.A, m.B访问插件内的对象，也可通过import_from进行导入，例如
A, B, C = import_from('mm')
# 或者
A, B, C = import_from(m)

# use(plugin_name, ...)，返回插件，也可以导入对象到全局空间（建议尽量使用import_from），例如
m = use('mm')
use('mm', 'A', 'B', 'C')
use('mm', '*') #类似于from mm import *
```
    * 状态变换
> > find\_proxy\_handler(req)的参数req提供以下属性：
```
req.proxy_type: 代理类型，socks4/socks5/socks2http/https/https2http/http
req.proxy_host: 被代理的主机，例如('www.baidu.com', 80)
req.server_address: 代理自身的地址，例如('127.0.0.1', 8086)
req.client_address: 客户端的地址，例如('192.168.1.101', 1234)
req.userid: 代理用户信息
当proxy_type以http结尾（即socks2http/https2http/http）时，以下属性可用：

```
    * 内置插件
```
# 内置插件无需使用install安装，可直接通过import_from使用
digest_auth, check_auth, set_hosts, redirect_https, Forward = import_from('util')

digest_auth(req, username, password) # 进行digest认证，认证通过返回None，失败返回digest Authenticate，例如
def find_proxy_handler(req):
    if req in ('http', 'https'):
        auth = digest_auth(req, 'username', 'password')
        if auth: #失败
            return auth
        # 成功

dnsDomainIs, dnsResolve, dnsResolve2, ip2int, IpList, RuleList, PacFile, HostList = import_from('pac')

```