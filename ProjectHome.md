<a href='Hidden comment: {{{
==公告==
* wallproxy 2.1.10版发布（Windows用户[https://code.google.com/p/wallproxy-plus/issues/detail?id=144#c1 更新]或其他系统用户下载[http://goo.gl/A4swL](0.5M)，Windows用户首次使用下载完整版[http://goo.gl/dFtij](3.8M)），暂时兼容goagent 1.x版与旧版wallproxy，扩展了旧版的hosts/pac功能，YouTube视频直播两不误，增加ini配置文件，保留多线程下载，改善转发性能，转发失败自动改走GAE。
* 新版wallproxy由原作者对旧版wallproxy重写，因为goagent用户多，为了方便大多数人利用原有goagent服务端，GAE插件部分以兼容goagent为主，而非旧版wallproxy。
* 运行环境：python 2.5/2.6/2.7，建议2.7+gevent+pyOpenSSL（完整版已包含Windows下运行环境）。
* 2012.11.26 (v2.1.10)修复访问http://wallproxy/后转发http变慢的bug；修复WallProxy.exe设置IE代理后无法浏览FTP的bug；修改内置hosts与域名解析的优先级；增加truehttps选项指定使用非伪造证书的域名。
* 2012.10.27 (v2.0.14)减小服务端的超时时间，需要重新上传服务端
* 如何在手机（例如[http://code.google.com/p/wallproxy-plus/downloads/detail?name=gaeproxy-2.0.14.apk Android]）等[https://code.google.com/p/wallproxy-plus/downloads/list 移动设备上使用]？

==简易教程（[https://code.google.com/p/wallproxy-plus/downloads/detail?name=wallproxy图文教程.doc 图文教程<<<<务必下载并阅读>>>>]）==
# [https://appengine.google.com/ 申请GAE]并创建appid（内置一些公共appid[[https://code.google.com/p/wallproxy-plus/issues/detail?id=484#c4 不保证安全性]]，下载后即可使用[跳过4、5步]，为获得更好体验，建议申请并上传自己的）；
# 下载wallproxy并解压；
# 运行local文件夹下WallProxy.exe或者Run.bat（非Windows用户运行startup.py，Windows若提示是否允许安装证书，请允许）；
# 上传：运行server文件夹下uploader.bat(非Windows用户运行uploader.py)，输入appid上传（一次只能上传同一个帐号下的appid，多appid用|分隔，提示Set Proxy时可[https://code.google.com/p/wallproxy-plus/issues/detail?id=343#c2 输入1来提高上传成功率]）；
# 访问[http://127.0.0.1:8086/#proxy_ini]，找到如下部分（56行左右）并修改appid = 后面为自己的appid，点右上角的“保存”之后即可使用了；
```
[gae]
;是否启用GAE服务端
enable = 1
;服务端appid（多个用|分隔，个数不限）
appid = appid1|appid2
```
# 代理地址127.0.0.1:8087；如需使用PAC，设置[http://127.0.0.1:8087/proxy.pac]；如需使用SwitchySharp/AutoProxy等浏览器扩展（SwitchySharp用户可导入配置local\misc\SwitchyOptions.bak），与goagent设置方法相同；如需使用智能代理（使无法使用PAC或扩展的程序也做到该走代理走代理，不该走就不走），设置127.0.0.1:8086为代理即可。
# 导入[http://127.0.0.1:8086/CA.crt]为浏览器根证书可消除浏览器证书警告（cmd窗口提示时间与导入后查看到的时间相同基本就是导入成功了，升级版本时请保留cert目录，以免需要再次导入）
# 可通过[http://127.0.0.1:8086]或[http://wallproxy]访问Web配置界面
----
==FAQ==
# 访问https网站提示证书无效/警告？  由于GAE的限制，需要[http://code.google.com/p/wallproxy-plus/issues/detail?id=57#c3 导入根证书到浏览器]（[http://code.google.com/p/wallproxy-plus/issues/detail?id=193#c4 IE导入无效？]），[https://code.google.com/p/wallproxy-plus/issues/detail?id=6#c2 判断导入是否正确]，升级版本时请复制以前的cert目录到新版文件夹，以免需要重新导入根证书。
# 如何开机启动？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=34#c1 发送快捷方式到启动文件夹]或者使用[https://code.google.com/p/wallproxy-plus/issues/detail?id=94#c1 GUI]。
# 智能代理、强制代理和pac有什么区别？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=32#c2 解释]，[https://code.google.com/p/wallproxy-plus/issues/detail?id=78#c5 设置]，[https://code.google.com/p/wallproxy-plus/issues/detail?id=84#c2 https_mode含义]，[https://code.google.com/p/wallproxy-plus/issues/detail?id=116#c1 find_handler含义]，[http://code.google.com/p/wallproxy-plus/issues/detail?id=192#c1 多目标PAC/智能代理设置]，[https://code.google.com/p/wallproxy-plus/issues/detail?id=221#c10 多目标PAC/智能代理设置2] [https://code.google.com/p/wallproxy-plus/issues/detail?id=289#c23 3]。
# 与goagent的区别？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=217#c3 服务端目前通用]，[https://code.google.com/p/wallproxy-plus/issues/detail?id=29#c1 区别主要在本地端]，可以认为：wallproxy = goagent + ccproxy + autoproxy [https://code.google.com/p/wallproxy-plus/issues/detail?id=474#c1 其他说明]。
# max-threads值设为0或1或其他值有何区别？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=20#c1 解释]。
# 是否支持根据国内ip或者教育网ip选择代理？  支持，[https://code.google.com/p/wallproxy-plus/issues/detail?id=289 PAC设置方式]。
# 支持作为http/https/socks4/socks5使用是什么意思，能否为qq代理？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=17#c1 解释] [https://code.google.com/p/wallproxy-plus/issues/detail?id=88#c2 解释2] [https://code.google.com/p/wallproxy-plus/issues/detail?id=442#c1 talk.google.com错误]
# 上传多个服务端有时候要输入多次帐号和密码？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=100#c1 解决]
# 如何禁用GUI的代理切换功能或者退出GUI后恢复无代理？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=51#c1 图解]
# 纯IPv6复杂环境设置方式？  [https://docs.google.com/document/d/1gyOvYBsEFskfk_YHubYMF0ZXKgWO9rf6cVOIPj765xg/edit 参考]，建议联系rpzrpz123#gmail.com
# 运行依赖的Python库？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=145#c4 参考]
# [gae]fetch_mode说明？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=276#c7 解释]
# wallproxy看YouTube直播原理？ [https://code.google.com/p/wallproxy-plus/issues/detail?id=399#c5 解释]
# 访问google.com禁止跳转到google.com.hk？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=418#c4 设置]
# 筛选合适的hosts？  [https://code.google.com/p/wallproxy-plus/issues/detail?id=431#c18 方法]

==计划==
* 重新编写（进行中）
* Web配置界面（进行中，暂时需要直接编辑文件，作为替代，实现了ini转py）
* 支持通配符证书（已实现）
* PAC支持China IP List等IP列表，修复bug（已实现）
* 改善对GAE的支持（进行中，暂时先兼容goagent）
* 更通用的多ip连接，而非仅仅针对.appspot.com（已实现）
* 结合gevent，改善并发访问（已实现）
* 更方便的局域网共享，更方便对用户进行身份认证（已实现）
* 完善作为http、https、socks4、socks5代理使用，可socks转https/http，https转http（已实现）
* 完善对http、https、socks4、socks5代理的支持，支持basic/digest认证，修复bug（已实现）
----
* This project is used for issues of [https://github.com/wallproxy/wallproxy/ wallproxy@github]。
}}}'></a>