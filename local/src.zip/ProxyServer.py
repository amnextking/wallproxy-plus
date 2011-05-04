#!/usr/bin/env python

__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__version__ = '0.0.5'

import SocketServer
import BaseHTTPServer
import struct
import socket
import select
import threading
from util import urlinfo
import wpconfig

class ProxyServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = BaseHTTPServer.HTTPServer.allow_reuse_address
    daemon_threads = True

    def __init__(self, config, RequestHandlerClass):
        server_address = config.get('listen', ('127.0.0.1', 8086))
        self.keep_alive = config.get('keep_alive', True)
        self.logger = wpconfig.get_logger(config.get('log_file'),
                config.get('log_format', '%(clientip)s - [%(asctime)s] '
                '%(levelname)-5s %(message)s'), config.get('log_size', 1024),
                config.get('log_backup', 0))
        SocketServer.TCPServer.__init__(self, server_address,
                                           RequestHandlerClass)

    def server_bind(self):
        SocketServer.TCPServer.server_bind(self)
        self.server_address = self.server_address[:2]

    def __str__(self):
        info = ['main_ver: %s' % __version__,
                'listen: %s:%s' % self.server_address,
                'keep_alive: %s' % self.keep_alive]
        return '\n'.join(info)


class ProxyRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def log_error(self, format, *args):
        self.server.logger.error(format%args, extra={'clientip':self.client_address[0]})

    def log_message(self, format, *args):
        self.server.logger.info(format%args, extra={'clientip':self.client_address[0]})

    def parse_request(self):
        if not self.server.keep_alive:
            self.close_connection = 1
            return BaseHTTPServer.BaseHTTPRequestHandler.parse_request(self)
        if not BaseHTTPServer.BaseHTTPRequestHandler.parse_request(self):
            return False
        pcon = self.headers.get('proxy-connection', '').lower()
        if 'close' in pcon:
            self.close_connection = 1
        elif 'keep-alive' in pcon:
            self.close_connection = 0
        return True

    def write_response(self, code, headers, msg='', size=None):
        self.log_request(code, '-' if size is None else size)
        if self.request_version != 'HTTP/0.9':
            if not msg and code in self.responses:
                msg = self.responses[code][0]
            if 'Content-Length' not in headers:
                self.close_connection = 1
            con = ('Connection', 'Proxy-Connection')
            del headers[con[int(self.path[0]=='/')]]
            if self.close_connection:
                del headers['Keep-Alive']
                headers[con[int(self.path[0]!='/')]] = 'close'
            else:
                headers[con[int(self.path[0]!='/')]] = 'keep-alive'
            self.wfile.write('HTTP/1.0 %d %s\r\n%s\r\n' % (code, msg, headers))

    def handle(self):
        try:
            req = self.connection.recv(1)
            if req == '\x04': # socks4
                self.handle_socks4_request()
            elif req == '\x05': # socks5
                self.handle_socks5_request()
            else:
                self.raw_requestline = req + self.rfile.readline()
                if not self.parse_request():
                    return
                if self.command == 'CONNECT':
                    self.handle_https_request()
                else:
                    self.handle_http_request()
                    while not self.close_connection:
                        self.raw_requestline = self.rfile.readline()
                        if not self.parse_request(): break
                        self.handle_http_request()
        except socket.error:
            pass

    def _read(self, size):
        data = ''
        while size > 0:
            try:
                tmp = self.connection.recv(size)
            except socket.error, e:
                if e.args[0] == socket.EINTR:
                    continue
                raise
            if not tmp: break
            data += tmp
            size -= len(tmp)
        return data

    def copy_sock(self, sock, max_idle=180):
        lst = [self.connection, sock]
        count = 0
        while count < max_idle:
            count += 1
            r, w, e = select.select(lst, [], lst, 1)
            if e: break
            if not r: continue
            for s in r:
                out = self.connection if s is sock else sock
                data = s.recv(8192)
                if data:
                    out.sendall(data)
                    count = 0

    def end_socks(self, resp=None, success=False):
        log = self.log_message if success else self.log_error
        if hasattr(self, 'address'):
            log('%s for %s %s', self.request, self.address, self.command)
        else:
            log('try %s failed' % self.request)
        if resp:
            self.connection.sendall(resp)

    def _handle_with_plugin(self, obj):
        handler = obj[0] if isinstance(obj, (list, tuple)) else obj
        handler.handle(obj, self)

    def handle_socks4_request(self):
        self.request = 'socks4'
        req = self._read(7)
        self.command, port = struct.unpack('>BH', req[:3])
        ip = socket.inet_ntoa(req[3:7])
        req = self._read(1)
        while req[-1] != '\x00':
            req += self._read(1)
        userid = req[:-1]
        if ip.startswith('0.0.0.') and not ip.endswith('.0'):
            req = self._read(1)
            while req[-1] != '\x00':
                req += self._read(1)
            ip = req[:-1]
        self.address = ip, port
        if not wpconfig.check_client(self.client_address[0], self.request,
                (self.command, ip, port, userid)):
            return self.end_socks('\x00\x5d\x00\x00\x00\x00\x00\x00')
        handler = wpconfig.find_sock_handler(self.request,ip,port,self.command)
        if not handler:
            return self.end_socks('\x00\x5b\x00\x00\x00\x00\x00\x00')
        self._handle_with_plugin(handler)

    def handle_socks5_request(self):
        self.request = 'socks5'
        req = self._read(ord(self._read(1)))
        if '\x02' in req: #username/password authentication
            self.connection.sendall('\x05\x02')
            req = self._read(2)
            req = self._read(ord(req[1])+1)
            username = req[:-1]
            password = self._read(ord(req[-1]))
            self.connection.sendall('\x01\x00')
        elif '\x00' in req:
            username, password = None, None
            self.connection.sendall('\x05\x00')
        else:
            return self.end_socks('\x05\xff')
        req = self._read(4)
        self.command = ord(req[1])
        if req[3] == '\x01': #IPv4 address
            ip = socket.inet_ntoa(self._read(4))
        elif req[3] == '\x03': #Domain name
            ip = self._read(ord(self._read(1)))
        elif req[3] == '\x04': #IPv6 address
            ip = socket.inet_ntop(socket.AF_INET6, self._read(16))
        else:
            return self.end_socks('\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00')
        port = struct.unpack('>H', self._read(2))[0]
        self.address = ip, port
        handler = wpconfig.find_sock_handler(self.request,ip,port,self.command)
        if not handler or not wpconfig.check_client(self.client_address[0],
                self.request, (self.command, ip, port, username, password)):
            return self.end_socks('\x05\x02\x00\x01\x00\x00\x00\x00\x00\x00')
        self._handle_with_plugin(handler)

    def handle_https_request(self):
        self.request = 'https'
        self.address = ip, port = urlinfo.parse_netloc(self.path, 'https')[:2]
        self.command = 1
        if not wpconfig.check_client(self.client_address[0], self.request,
                (ip, port, self.headers)):
            return self.send_error(407)
        handler = wpconfig.find_sock_handler(self.request, ip, port, 1)
        if not handler:
            return self.send_error(417, 'find_sock_handler return None')
        self._handle_with_plugin(handler)

    def read_body(self):
        try:
            length = int(self.headers.get('content-length', 0))
        except ValueError:
            length = 0
        return self.rfile.read(length) if length>0 else ''

    def handle_http_request(self):
        self.request = 'http'
        if self.path[0] == '/':
            if (len(self.client_address) > 2 and
                str(self.client_address[2]).startswith('https://')):
                self.url = self.client_address[2] + self.path
            else:
                self.url = 'http://%s%s' % (self.headers.get('host'),self.path)
        else:
            self.url = self.path
        self.url = urlinfo.URL(self.url)
        if not wpconfig.check_client(self.client_address[0], self.request,
                (self.command, self.url, self.headers)):
            return self.send_error(407)
        handler = wpconfig.find_http_handler(self.command,self.url,self.headers)
        if not handler:
            return self.send_error(417, 'find_http_handler return None')
        self._handle_with_plugin(handler)

def main():
    msg = '-' * 78
    httpd = ProxyServer(wpconfig.get_config(), ProxyRequestHandler)
    print msg
    print httpd
    print msg
    wpconfig.set_config(False)
    t = threading.Thread(target=httpd.serve_forever)
    t.setDaemon(True); t.start(); del t
    wpconfig.set_config(True)
    print msg
    try:
        wpconfig.watch_config(msg)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            httpd.shutdown()
        except AttributeError:
            pass

if __name__ == '__main__':
    main()