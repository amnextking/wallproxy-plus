文件说明：
1、使用GUI的用户，除startup.py、win-patch.py可删除外，其他文件应该保留，首次运行或
   修改配置文件后出错请运行proxy.exe查看出错信息，配置正确后运行WallProxy.exe即可。
   强烈建议使用WallProxy管理IE代理以实现更快速准确高效的自动代理选择，且可对IE、
   Chrome、Firefox等浏览器均有效，支持局域网模式和拨号连接(连接名称如“宽带连接”)。
2、Linux/Mac等类Unix用户，可仅保留startup.py、src.zip、proxy.conf，运行startup.py。
   如果提示缺少OpenSSL且该系统没有其实现，可从其他地方复制cert目录（含_ca.key和
   _ca.crt）；如果提示缺少AES等加密模块且该系统没有其实现，可以改用XOR--0加密模式。
   AutoProxy插件生成的PAC能实现更快速准确高效的自动代理选择，可配合FoxyProxy等浏览
   器扩展使用。
3、Windows下使用源码的用户，可使用解压软件从proxy.exe中提取出OpenSSL和Crypto，然后
   运行win-patch.py对版本进行修改（Python2.5下修改后OpenSSL可正常使用，加密模块不能，
   解决办法是寻找Crypto适用于Python2.5的版本或换Python或改用XOR--0；Python2.6/2.7
   下修改后均可正常使用），需要保留的文件（夹）有startup.py、src.zip、proxy.conf、
   OpenSSL、Crypto，运行startup.py。
4、虽然很少有人报告用于Android的情况，但如果GAppProxy能够运行，WallProxy肯定也是能够
   运行的（保留startup.py、src.zip、proxy.conf及cert目录）；“根据AutoProxy规则
   提供判断函数用于find_http_handler”也许此时才真正派上用场（PAC可用时建议用PAC）。
5、proxy.conf提供简洁配置，新用户上传服务端后修改proxy.conf中地址即可开始使用。
   首次运行后导入cert目录下_ca.crt到浏览器根证书中可去掉烦人的https证书提示，如果
   出问题请先删除旧证书再重新导入。如果需要进一步配置例如使用加密，重命名"proxy_
   重命名.conf"为proxy.conf。

6、服务端参数含义
   cfgCacheTime配置缓存时间（不用改） cacheTime资源缓存时间（不用改）
   maxSize能够下载的最大尺寸（不用改）
   siteKey密码（可以改） cryptoMode加密模式（可以改）

7、默认加密模式XOR--32，默认密码空(也是加密的)，maxSize默认值9000000，
   range0默认值200000，range默认值500000，max_threads默认值10
