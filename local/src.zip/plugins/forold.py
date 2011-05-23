# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__version__ = '0.4.1'

from util import crypto as _crypto, httpheaders
import gaeproxy
import zlib, struct

class Handler(gaeproxy.Handler):
    crypto = _crypto.Crypto2('XOR--32')

    _unquote_map = {'0':'\x10', '1':'=', '2':'&'}
    def _quote(self, s):
        return str(s).replace('\x10', '\x100').replace('=','\x101').replace('&','\x102')
    def dump_data(self, dic):
        return '&'.join('%s=%s' % (self._quote(k), self._quote(v)) for k,v in dic.iteritems())
    def _unquote(self, s):
        res = s.split('\x10')
        for i in xrange(1, len(res)):
            item = res[i]
            try:
                res[i] = self._unquote_map[item[0]] + item[1:]
            except KeyError:
                res[i] = '\x10' + item
        return ''.join(res)
    def load_data(self, qs):
        pairs = qs.split('&')
        dic = {}
        for name_value in pairs:
            if not name_value:
                continue
            nv = name_value.split('=', 1)
            if len(nv) != 2:
                continue
            if len(nv[1]):
                dic[self._unquote(nv[0])] = self._unquote(nv[1])
        return dic

    def __init__(self, config):
        if 'crypto' in config:
            self.__class__.crypto = _crypto.Crypto2(config.pop('crypto'))
        gaeproxy.Handler.__init__(self, config)

    def _process_request(self, req):
        data = req.read_body()
        rawrange, range = self._process_range(req.headers)
        if req.command=='GET' and self.add_range(req.url, req.headers):
            req.headers['Range'] = range
        request = {'url':req.url.geturl(), 'method':req.command,
                   'headers':req.headers, 'payload':data, 'range':range}
        return request, rawrange

    def fetch(self, data):
        data, resp = self._fetch(data)
        if data == -1: return data, resp
        try:
            raw_data = resp.read(); resp.close()
            data = self.crypto.decrypt(raw_data, self.key)
            if data[0] == '0':
                data = data[1:]
            elif data[0] == '1':
                data = zlib.decompress(data[1:])
            else:
                return -1, 'Data format not match(%s:%s)' % (self.url.geturl(),raw_data)
            code, hlen, clen = struct.unpack('>3I', data[:12])
            if len(data) != 12+hlen+clen:
                return -1, 'Data length not match'
            content = data[12+hlen:]
            if code == 555:     #Urlfetch Failed
                return -1, 'Server: '+content
            headers = httpheaders.HTTPHeaders(self.load_data(data[12:12+hlen]))
            return 1, code, headers, content
        except Exception, e:
            return -1, str(e)


init_time = 2
plugin_name = 'Plugin for WallProxy 0.4.0'

def init_plugin(config):
    return gaeproxy.init(Handler, config)