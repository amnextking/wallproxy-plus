# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__patcher__ = 'ZHRtYWppYUAxNjMuY29t'.decode('base64')

'''
see http://en.wikipedia.org/wiki/SOCKS#Protocol
    and http://www.ietf.org/rfc/rfc1928.txt
'''

import socket
import struct
import urlinfo

__all__ = ['ProxyError', 'Proxy']

hosts = [{}, []]
def map_hosts(host):
    newhost = hosts[0].get(host)
    if newhost is None:
        for k,v in hosts[1]:
            if host.endswith(k):
                newhost = v
                break
    if newhost is not None:
        return newhost
    return host

def create_connection(address, timeout=-1):
    msg = "getaddrinfo returns an empty list"
    host, port = address
    host = map_hosts(host)
    for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socket.socket(af, socktype, proto)
            if timeout is None or timeout>=0:
                sock.settimeout(timeout)
            sock.connect(sa)
            return sock
        except socket.error, msg:
            if sock is not None:
                sock.close()
    raise socket.error, msg

if not hasattr(socket, 'inet_pton'):
    def inet_pton(af, ip):
        '''inet_pton(af, ip) -> packed IP address string'''
        ip = str(ip)
        msg = 'illegal IP address string passed to inet_pton'
        if af == socket.AF_INET:
            return socket.inet_aton(ip)
        elif af == socket.AF_INET6:
            ip = ip.split('::')
            ln = len(ip)
            if ln == 1:
                ip = ip[0].split(':')
                if len(ip) != 8:
                    raise socket.error, msg
            elif ln == 2:
                ip[0] = ip[0].split(':') if ip[0] else []
                ip[1] = ip[1].split(':') if ip[1] else []
                ln = len(ip[0]) + len(ip[1])
                if ln >= 8:
                    raise socket.error, msg
                ip = ip[0] + ['0000']*(8-ln) + ip[1]
            else:
                raise socket.error, msg
            for i,v in enumerate(ip):
                ln = len(v)
                if ln==0 or ln>4:
                    raise socket.error, msg
                ip[i] = '0'*(4-ln) + v
            try:
                return ''.join(ip).decode('hex')
            except:
                raise socket.error, msg
        else:
            raise socket.error, (97, 'Address family not supported by protocol')
    socket.inet_pton = inet_pton; del inet_pton

if not hasattr(socket, 'inet_ntop'):
    def inet_ntop(af, ip):
        '''inet_ntop(af, packed_ip) -> string formatted IP address'''
        ip = str(ip)
        if af == socket.AF_INET:
            return socket.inet_ntoa(ip)
        elif af == socket.AF_INET6:
            if len(ip) != 16:
                raise ValueError, 'invalid length of packed IP address string'
            ip = ip.encode('hex')
            lst = [None] * 8
            for i in xrange(8):
                lst[i] = ip[i*4:i*4+4].lstrip('0')
                if not lst[i]: lst[i] = '0'
            beststart = bestend = -1
            i = 0
            while i < 8:
                if lst[i] == '0':
                    start = i
                    while i<8 and lst[i]=='0': i+=1
                    if i-start > bestend-beststart:
                        beststart = start
                        bestend = i
                i += 1
            if beststart!=-1 and bestend-beststart>1:
                if beststart==0 and bestend>7:
                    return '::'
                elif beststart==0 or bestend>7:
                    lst[beststart:bestend] = [':']
                else:
                    lst[beststart:bestend] = ['']
            return ':'.join(lst)
        else:
            raise ValueError, 'unknown address family %s' % af
    socket.inet_ntop = inet_ntop; del inet_ntop


class ProxyError(Exception):
    info = ('invalid response', #0
            'general SOCKS server failure', #0x01
            'connection not allowed by ruleset', #0x02
            'network unreachable', #0x03
            'host unreachable', #0x04
            'connection refused', #0x05
            'TTL expired', #0x06
            'command not supported', #0x07
            'address type not supported', #0x08
            'authentication failed', #9
            'request self') #10

class proxysocket(socket.socket):
    def __init__(self, sock, proxypeer):
        if hasattr(sock, '_sock'):
            sock = sock._sock
        socket.socket.__init__(self, _sock=sock)
        self.__proxypeer = proxypeer
    def getproxypeer(self):
        return self.__proxypeer
    def recvall(self, size):
        data = ''
        while size > 0:
            try:
                tmp = self.recv(size)
            except socket.error, e:
                if e.args[0] == socket.EINTR:
                    continue
                raise
            if not tmp: break
            data += tmp
            size -= len(tmp)
        return data

class Proxy:
    timeout = 20
    def __init__(self, proxy=None, timeout=-1):
        if timeout is None or timeout>=0:
            self.timeout = timeout
        if not proxy:
            self._proxy = None
            self.type = None, None
        else:
            if isinstance(proxy, basestring):
                proxy = (proxy,)
            self._proxy =  [None] * len(proxy)
            for i in xrange(len(proxy)-1):
                self._proxy[i] = self._parse_proxy(proxy[i])
                if self._proxy[i][0] == 'http':
                    raise ValueError('Bad proxies order')
            self._proxy[-1] = self._parse_proxy(proxy[-1])
            self.type = self._proxy[-1][0], self._proxy[-1][2]

    def _parse_proxy(self, proxy):
        url = urlinfo.URL(proxy)
        if url.port is None:
            url.port = 1080
        if url.scheme == 'socks':
            url.scheme = 'socks5'
        auth = None
        if url.scheme in ('http', 'https', 'socks5'):
            if url.username is not None and url.password is not None:
                auth = url.username, url.password
        elif url.scheme == 'socks4':
            auth = url.username or ''
        else:
            raise ValueError('Bad proxy type: '+url.scheme)
        dns = url.parse_qs().get('dns')
        if dns and dns[-1].lower() in ('true', 'yes', '1'):
            dns = True
        else:
            dns = False
        return url.scheme, (url.hostname, url.port), auth, dns

    def connect(self, addr, cmd=1, selfport=None):
        proxysock = self._connect(addr, cmd)
        if selfport is not None:
            ip, port = proxysock.getproxypeer()
            if ip==proxysock.getsockname()[0] and port==selfport:
                raise ProxyError(10) #request self
        return proxysock

    def _connect(self, addr, cmd=1):
        p = self._proxy
        if not p:
            if cmd == 1:
                return self.__connect(addr)
            raise ProxyError(7) #command not supported
        sock = self.__connect(p[0][1])
        try:
            for i in xrange(len(p)-1):
                connector = getattr(self, '_connect_in_'+p[i][0])
                sock = connector(sock, p[i][2], p[i][3], p[i+1][1], 1)
            if p[-1][0] != 'http':
                connector = getattr(self, '_connect_in_'+p[-1][0])
                sock = connector(sock, p[-1][2], p[-1][3], addr, cmd)
            return sock
        except Exception, e:
            sock.close()
            if type(e) == ProxyError: raise
            raise ProxyError(repr(e))

    def __connect(self, addr):
        try:
            sock = create_connection(addr, self.timeout)
            return proxysocket(sock, sock.getpeername()[:2])
        except socket.error:
            raise ProxyError(4) #host unreachable

    def _connect_in_socks4(self, sock, auth, dns, addr, cmd=1):
        if cmd not in (1, 2):
            raise ProxyError(7) #command not supported
        addr, port = addr
        if dns:
            try:
                addr = socket.gethostbyname(addr)
            except socket.error:
                raise ProxyError(4) #host unreachable
        try:
            addr = socket.inet_aton(addr); dns = True
            req = '\x04%s%s%s\x00' % (struct.pack('>BH',cmd,port), addr, auth)
        except socket.error: #try SOCKS 4a
            dns = False
            req = '\x04%s\x00\x00\x00\x01%s\x00%s\x00' % (
                struct.pack('>BH',cmd,port), auth, addr)
        sock.sendall(req)
        resp = sock.recvall(8)
        if resp[0] != '\x00':
            raise ProxyError(0) #invalid response
        if resp[1] != '\x5a':
            if resp[1] == '\x5b': raise ProxyError(5) #connection refused
            if resp[1] == '\x5c': raise ProxyError(4) #host unreachable
            if resp[1] == '\x5d': raise ProxyError(9) #authentication failed
            raise ProxyError(0) #invalid response
        if dns:
            return proxysocket(sock, (socket.inet_ntoa(addr), port))
        else:
            addr = (socket.inet_ntoa(resp[4:]),struct.unpack('>H',resp[2:4])[0])
            return proxysocket(sock, addr)

    def _dnsresolve(self, addr):
        addr = urlinfo.host2ip(addr)
        if addr[0]: return addr[0][0]
        elif addr[1]: return addr[1][0]
        return None

    def _connect_in_socks5(self, sock, auth, dns, addr, cmd=1):
        if cmd not in (1, 2, 3):
            raise ProxyError(7) #command not supported
        sock.sendall('\x05\x02\x00\x02' if auth else '\x05\x01\x00')
        resp = sock.recvall(2)
        if resp[0] != '\x05':
            raise ProxyError(0) #invalid response
        if resp[1] == '\x02':
            sock.sendall('\x01%s%s%s%s' % (chr(len(auth[0])), auth[0],
                chr(len(auth[1])), auth[1]))
            resp = sock.recvall(2)
        if resp[1] != '\x00':
            raise ProxyError(9) #authentication failed
        addr, port = addr
        if dns:
            addr = self._dnsresolve(addr)
            if not addr:
                raise ProxyError(4) #host unreachable
        if ':' in addr: #IPv6
            try:
                addr = '\x04' + socket.inet_pton(socket.AF_INET6, addr)
            except socket.error:
                raise ProxyError(4) #host unreachable
        else:
            try:
                addr = '\x01' + socket.inet_aton(addr) #IPv4
            except socket.error:
                addr = '\x03%s%s' % (chr(len(addr)), addr) #domain
        req = '\x05%s\x00%s%s' % (chr(cmd), addr, struct.pack('>H',port))
        sock.sendall(req)
        resp = sock.recvall(4)
        if resp[0] != '\x05':
            raise ProxyError(0) #invalid response
        if resp[1] != '\x00':
            raise ProxyError(ord(resp[1]))
        if resp[3] == '\x01': #IPv4 address
            addr = socket.inet_ntoa(sock.recvall(4))
        elif resp[3] == '\x03': #Domain name
            addr = sock.recvall(ord(sock.recvall(1)))
        elif resp[3] == '\x04': #IPv6 address
            addr = socket.inet_ntop(socket.AF_INET6, sock.recvall(16))
        else:
            raise ProxyError(8) #address type not supported
        port = struct.unpack('>H',sock.recvall(2))[0]
        return proxysocket(sock, (addr,port))

    def _connect_in_https(self, sock, auth, dns, addr, cmd=1):
        if cmd != 1:
            raise ProxyError(7) #command not supported
        addr, port = addr
        if dns:
            addr = self._dnsresolve(addr)
            if not addr:
                raise ProxyError(4) #host unreachable
        addrinfo = ('[%s]:%s' if ':' in addr else '%s:%s') % (addr, port)
        auth = 'Proxy-Authorization: Basic %s\r\n' % ('%s:%s' % auth
            ).encode('base64').strip() if auth else ''
        req = 'CONNECT %s HTTP/1.1\r\nAccept: */*\r\n%s\r\n' % (addrinfo, auth)
        sock.sendall(req)
        resp = sock.recv(1024)
        if not resp.startswith('HTTP/'):
            raise ProxyError(0) #invalid response
        while resp.find('\r\n\r\n')==-1:
            resp += sock.recv(1024)
        try:
            statuscode = int(resp.split('\n',1)[0].split(' ',2)[1])
        except:
            raise ProxyError(0) #invalid response
        if statuscode != 200:
            raise ProxyError('invalid statuscode: %d' % statuscode)
        return proxysocket(sock, (addr, port))