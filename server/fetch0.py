__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__version__ = '0.4.2'

import fetch
from fetch import struct, zlib, logging, memcache

class MainHandler(fetch.MainHandler):
    _cfg = fetch._init_config(fetch.crypto.Crypto2)

    _unquote_map = {'0':'\x10', '1':'=', '2':'&'}
    def _quote(self, s):
        return (str(s).replace('\x10', '\x100').
                replace('=','\x101').replace('&','\x102'))
    def dump_data(self, dic):
        res = []
        for k,v in dic.iteritems():
            res.append('%s=%s' % (self._quote(k), self._quote(v)))
        return '&'.join(res)
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

    def _pack_data(self, code, headers, data):
        ct = headers.get('Content-Type', '').lower()
        headers = self.dump_data(headers)
        info = struct.pack('>3I', code, len(headers), len(data))
        data = ''.join((info, headers, data))
        if ct.find('text')>=0 or ct.find('application')>=0:
            cdata = zlib.compress(data)
            data = '1'+cdata if len(data)>len(cdata) else '0'+data
        else:
            data = '0'+data
        return data

    def _send_data(self, data, length):
        self.response.headers['Content-Type'] = 'application/octet-stream'
        self.response.headers['Content-Length'] = str(length)
        data = self._cfg['crypto'].encrypt(data, self._cfg['siteKey'])
        self.response.out.write(data)

    def sendResponse(self, code, headers, content, method, url):
        need_cache = self._need_cache(method, code, headers)
        data = self._pack_data(code, headers, content)
        length = len(data)
        if need_cache and length<1000000:
            if not memcache.set(url, data, self._cfg['cacheTime'], namespace='wp_cache0'):
                logging.warning('Memcache set wp_cache0(%s) failed' % url)
        if code == 555:
            logging.warning('Response: "%s %s" %s' % (method, url, content))
        else:
            logging.debug('Response: "%s %s" %d %d/%d' % (
                          method, url, code, len(content), length))
        self._send_data(data, length)

    def _check_cache(self, method, url, headers):
        data = None
        if self._cfg['cacheTime'] and method=='GET':
            data = memcache.get(url, namespace='wp_cache0')
        if data is not None:
            if 'If-Modified-Since' in headers:
                self.sendResponse(304, {}, '', method, url)
            else:
                length = len(data)
                logging.debug('Memcache hits: "%s %s" %d %d' % (method, url, 200, length))
                self._send_data(data, length)
            return True
        return False

def main():
    application = fetch.webapp.WSGIApplication([(r'/.*', MainHandler)], debug=True)
    fetch.run_wsgi_app(application)

if __name__ == '__main__':
    main()