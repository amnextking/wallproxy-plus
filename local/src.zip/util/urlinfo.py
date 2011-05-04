__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')

import os
import urlparse, urllib

__all__ = ['url2path', 'path2url', 'parse_netloc', 'unparse_netloc',
           'host2ip', 'URL']

default_ports = {'http':80, 'https':443, 'ftp':21}

def url2path(path):
    """url2path('/a%20b.txt') -> '/a b.txt' or url2path('/C:/a%20b.txt')
-> 'C:\\a b.txt'"""
    if os.name == 'nt':
        i = path.find(':')
        if i > 0: path = path[i-1:]
    path = urllib.unquote(path)
    if os.sep != '/':
        path = path.replace('/', os.sep)
    return path

def path2url(path):
    """path2url('/a b.txt') -> '/a%20b.txt' or path2url('C:\\a b.txt') ->
'/C:/a%20b.txt'"""
    if os.name == 'nt':
        driver, s, path = path.rpartition(':')
    if os.sep != '/':
        path = path.replace(os.sep, '/')
    path = urllib.quote(path)
    if os.name=='nt' and s:
        path = '/%s%s%s' % (driver, s, path)
    return path

def parse_netloc(netloc, scheme=None):
    """parse_netloc('user:pass@Example.com', 'http') -> ('example.com', 80,
'user', 'pass')"""
    username = password = port = None
    if '@' in netloc:
        username, netloc = netloc.rsplit('@', 1)
        if ':' in username:
            username, password = username.split(':', 1)
    i = netloc.rfind(':')
    j = netloc.rfind(']')
    if i != -1:
        if (j==-1 and netloc.find(':')==i) or (j!=-1 and i>j):
            try:
                port = int(netloc[i+1:])
            except ValueError:
                pass
            netloc = netloc[:i]
    if j != -1:
        netloc = netloc[netloc.find('[')+1:j]
    if port is None:
        port = default_ports.get(scheme)
    hostname = netloc.lower()
    return hostname, port, username, password

def unparse_netloc(hostname, port=None, username=None,
        password=None, scheme=None):
    """unparse_netloc('example.com', 80, 'user', 'pass', 'http') ->
'user:pass@example.com'"""
    if ':' in hostname:
        hostname = '[%s]' % hostname
    if port is not None and port!=default_ports.get(scheme):
        hostname = '%s:%s' % (hostname, port)
    if username is not None:
        if password is not None:
            hostname = '%s:%s@%s' % (username, password, hostname)
        else:
            hostname = '%s@%s' % (username, hostname)
    return hostname

def host2ip(hostname):
    """host2ip('localhost') -> (['127.0.0.1'], ['::1'])"""
    ip = [], []
    try:
        import socket
        dic = {socket.AF_INET:ip[0], socket.AF_INET6:ip[1]}
        for i in socket.getaddrinfo(hostname, 80, 0, socket.SOCK_STREAM):
            dic[i[0]].append(i[4][0])
    except:
        pass
    return ip

class URL(object):

    def __init__(self, url):
        url = urlparse.urlparse(url)
        if url[0] == 'file':
            self.scheme = url[0]
            self.path = url2path(url[1] + url[2])
            return
        (self.scheme, netloc, path, self.params,
            self.query, self.fragment) = url
        self.path = path or '/'
        (self.hostname, self.port, self.username,
            self.password) = parse_netloc(netloc, self.scheme)

    @property
    def ip(self):
        if not hasattr(self, '_ip') or self._ip[0]!=self.hostname:
            self._ip = (self.hostname, host2ip(self.hostname))
        return self._ip[1]

    @property
    def host(self):
        return unparse_netloc(self.hostname, self.port, scheme=self.scheme)

    @property
    def uri(self):
        if self.scheme == 'file':
            return self.path
        return urlparse.urlunparse(('', '', self.path,
            self.params, self.query, ''))

    def geturl(self, userinfo=False, fragment=False):
        if self.scheme == 'file':
            return 'file://' + path2url(self.path)
        netloc = unparse_netloc(self.hostname, self.port, self.username
            if userinfo else None, self.password, self.scheme)
        return urlparse.urlunparse((self.scheme, netloc, self.path,
            self.params, self.query, self.fragment if fragment else ''))

    def parse_qs(self, keep_blank_values=0, strict_parsing=0):
        if not hasattr(urlparse, 'parse_qs'):
            import cgi
            urlparse.parse_qs = cgi.parse_qs
        return urlparse.parse_qs(self.query, keep_blank_values, strict_parsing)

    def __getstate__(self):
        if self.scheme == 'file':
            return (self.scheme, self.path)
        return (self.scheme, self.hostname, self.port, self.username,
            self.password, self.path, self.params, self.query, self.fragment)

    def __setstate__(self, data):
        self.scheme, data = data[0], data[1:]
        if self.scheme == 'file':
            self.path = data[0]
        else:
            (self.hostname, self.port, self.username, self.password,
                self.path, self.params, self.query, self.fragment) = data[:8]

    def __repr__(self):
        if self.scheme == 'file':
            fmt = "URL(scheme='%s', path='%s')"
        else:
            fmt = ("URL(scheme='%s', hostname='%s', port=%r, username=%r, "
             "password=%r, path='%s', params='%s', query='%s', fragment='%s')")
        return fmt % self.__getstate__()