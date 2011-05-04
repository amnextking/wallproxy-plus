__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__version__ = '0.0.1'

import random
import socket
import struct
from util import proxylib, urlfetch

class Handler:
    def __init__(self, proxy):
        self.proxy = proxylib.Proxy(proxy)

    def handle(self, handler, req):
        if isinstance(handler, (list, tuple)):
            handler = random.choice(handler)
        handler = getattr(handler, 'handle_%s_request' % req.request)
        if req.request!='http' and self.proxy.type[0]=='http':
            req.log_error('Please select a socks proxy for %s', req.address)
        else:
            handler(req)

    def handle_http_request(self, req):
        if req.url.scheme == 'https':
            if self.proxy.type[0] == 'http':
                return req.send_error(417, 'http proxy does not support https')
            opener = urlfetch.HTTPSFetch(self.proxy, False,
                                         req.server.server_address[1])
        else:
            opener = urlfetch.HTTPFetch(self.proxy, False,
                                        req.server.server_address[1])
        #opener.set_debuglevel(1)
        data = req.read_body()
        try:
            resp = opener.open(req.url, data, req.command, req.headers)
            req.write_response(resp.status, resp.msg, resp.reason, resp.length)
            data = resp.read(8192)
            while data:
                req.wfile.write(data)
                data = resp.read(8192)
            resp.close()
        except proxylib.ProxyError, e:
            if e.args[0] == 10:
                return req.send_error(200, 'WallProxy Local Server is Running')
            req.send_error(502, 'Connect porxy/host failed')
        except socket.error, e:
            req.log_error('"%s" %s', req.requestline, e)
            req.wfile.close()
            raise

    def handle_socks4_request(self, req):
        try:
            sock = self.proxy.connect(req.address, req.command,
                                      req.server.server_address[1])
        except proxylib.ProxyError, e:
            e = {4:'\x5c', 9:'\x5d'}.get(e.args[0], '\x5b')
            return req.end_socks('\x00%s\x00\x00\x00\x00\x00\x00' % e)
        ip, port = sock.getproxypeer()
        try:
            ip = socket.gethostbyname(ip)
        except socket.error:
            ip = '0.0.0.0'
        ip = socket.inet_aton(ip)
        req.end_socks('\x00\x5a%s%s'%(struct.pack('>H',port),ip), True)
        req.copy_sock(sock)

    def handle_socks5_request(self, req):
        try:
            sock = self.proxy.connect(req.address, req.command,
                                      req.server.server_address[1])
        except proxylib.ProxyError, e:
            e = e.args[0]
            if type(e)!=int or e<1 or e>8: e = 1
            return req.end_socks('\x05%s\x00\x01\x00\x00\x00\x00\x00\x00'
                                  % chr(e))
        ip, port = sock.getproxypeer()
        if ':' in ip:
            try:
                ip = '\x04' + socket.inet_pton(socket.AF_INET6, ip)
            except socket.error:
                ip = '\x01\x00\x00\x00\x00'
        else:
            try:
                ip = '\x01' + socket.inet_aton(ip) #IPv4
            except socket.error:
                ip = '\x03%s%s' % (chr(len(ip)), ip) #domain
        req.end_socks('\x05\x00\x00%s%s' % (ip, struct.pack('>H',port)), True)
        req.copy_sock(sock)

    def handle_https_request(self, req):
        try:
            sock = self.proxy.connect(req.address, req.command,
                                      req.server.server_address[1])
        except proxylib.ProxyError, e:
            return req.send_error(502, 'Connect porxy/host failed')
        req.log_request(200)
        req.connection.sendall('HTTP/1.0 200 OK\r\n\r\n')
        req.copy_sock(sock)


init_time = 0
plugin_name = 'General Proxy'

def init_plugin(proxies):
    proxy = [None] * len(proxies)
    for i,p in enumerate(proxies):
        proxy[i] = Handler(p)
    return proxy