# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')

import httplib
import threading
import httpheaders, proxylib, urlinfo

from httplib import error
def addheader(self, key, value):
    prev = self.dict.get(key)
    if prev is None:
        self.dict[key] = value
    else:
        self.dict[key] = '%s\r\n%s: %s' % (prev, key.title(), value)
httplib.HTTPMessage.addheader = addheader; del addheader

__all__ = ['HTTPFetch', 'fetch']

class HTTPFetch(httplib.HTTPConnection, threading.local):

    _user_agent = 'Mozilla/5.0'

    def __init__(self, proxy=None,keep_alive=False,selfport=None,timeout=-1):
        if not isinstance(proxy, proxylib.Proxy):
            proxy = proxylib.Proxy(proxy, timeout)
        elif timeout is None or timeout>=0:
            proxy.timeout = timeout
        self.proxy = proxy
        self.keep_alive = keep_alive
        self.selfport = selfport
        self.sock = None
        self._buffer = []
        self._HTTPConnection__response = None
        self._HTTPConnection__state = httplib._CS_IDLE
        self.addr = None

    def __del__(self):
        self.close()

    def connect(self):
        self.sock = self.proxy.connect(self.addr, 1, self.selfport)

    def putrequest(self, method, url, headers):
        proxy_type, proxy_auth = self.proxy.type
        if proxy_type != 'http':
            addr = url.hostname, url.port
            if addr != self.addr:
                self.close()
                self.addr = addr
        if self._HTTPConnection__state == httplib._CS_IDLE:
            self._HTTPConnection__state = httplib._CS_REQ_STARTED
        else:
            raise httplib.CannotSendRequest()
        self._method = method
        if proxy_type == 'http':
            self._output('%s %s %s' % (method,url.geturl(),self._http_vsn_str))
            if proxy_auth:
                self.putheader('Proxy-Authorization', 'Basic %s' % (
                               '%s:%s'%proxy_auth).encode('base64').strip())
            self.putheader('Proxy-Connection',
                           'keep-alive' if self.keep_alive else 'close')
        else:
            self._output('%s %s %s' % (method,url.uri,self._http_vsn_str))
            self.putheader('Connection',
                           'keep-alive' if self.keep_alive else 'close')
        if self._http_vsn == 11:
            if 'Host' not in headers:
                self.putheader('Host', url.host)
            if 'Accept-Encoding' not in headers:
                self.putheader('Accept-Encoding', 'identity')
            if 'User-Agent' not in headers:
                self.putheader('User-Agent', self._user_agent)

    def _send_request(self, method, url, body, headers):
        self.putrequest(method, url, headers)
        if body:
            if 'Content-Type' not in headers:
                self.putheader('Content-Type',
                               'application/x-www-form-urlencoded')
            if 'Content-Length' not in headers:
                try:
                    self.putheader('Content-Length', str(len(body)))
                except TypeError:
                    import os
                    try:
                        self.putheader('Content-Length',
                                       str(os.fstat(body.fileno()).st_size))
                    except (AttributeError, OSError):
                        if self.debuglevel > 0: print 'Cannot stat!!'
        for k,v in headers.iteritems():
            self.putheader(k, v)
        self.endheaders()
        if body:
            self.send(body)

    def open(self,url,body=None,method=None,headers=httpheaders.HTTPHeaders()):
        if not method: method = 'POST' if body else 'GET'
        if not isinstance(url, urlinfo.URL):
            url = urlinfo.URL(url)
        if not isinstance(headers, httpheaders.HTTPHeaders):
            headers = httpheaders.HTTPHeaders(headers)
        del headers['Connection'], headers['Proxy-Connection']
        try:
            self.request(method, url, body, headers)
            return self.getresponse()
        except (httplib.socket.error, error):
            self.close()
            self.request(method, url, body, headers)
            return self.getresponse()

try:
    import ssl
except ImportError:
    pass
else:
    class HTTPSFetch(HTTPFetch):
        def connect(self):
            proxysock = self.proxy.connect(self.addr, 1, self.selfport)
            self.sock = ssl.wrap_socket(proxysock)
    __all__.append('HTTPSFetch')

_proxy = [None, None]
def fetch(url, body=None, method=None, headers=None, proxy=None):
    if not isinstance(url, urlinfo.URL):
        url = urlinfo.URL(url)
    if url.scheme == 'http':
        opener = HTTPFetch(proxy if proxy else _proxy[0], False)
    else:
        opener = HTTPSFetch(proxy if proxy else _proxy[1], False)
    #opener.set_debuglevel(1)
    return opener.open(url, body, method, headers)