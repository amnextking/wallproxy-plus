__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__version__ = '1.0.4'

from util import crypto as _crypto, httpheaders, proxylib, urlfetch, urlinfo
import zlib, time, re, struct, random
import cPickle as pickle
import threading

class Handler:
    _dirty_headers = ('connection', 'proxy-connection', 'proxy-authorization',
                     'content-length', 'host', 'vary', 'via', 'x-forwarded-for')
    _range_re = re.compile(r'(\d+)?-(\d+)?')
    _crange_re = re.compile(r'bytes\s+(\d+)-(\d+)/(\d+)')
    crypto = _crypto.Crypto('XOR--32'); key = ''
    proxy = proxylib.Proxy()
    headers = httpheaders.HTTPHeaders('Content-Type: application/octet-stream')
    range0 = 200000; range = 500000; max_threads = 10

    def __init__(self, config):
        dic = {'crypto': _crypto.Crypto, 'key': lambda v:v,
               'proxy': proxylib.Proxy, 'headers': httpheaders.HTTPHeaders,
               'range0': lambda v:v if v>=10000 else self.__class__.range0,
               'range': lambda v:v if v>=100000 else self.__class__.range,
               'max_threads': lambda v:v if v>0 else self.__class__.max_threads}
        self.url = urlinfo.URL(config['url'])
        for k,v in dic.iteritems():
            if k in config:
                setattr(self.__class__, k, v(config[k]))
            setattr(self, k, getattr(self.__class__, k))
        opener_cls = urlfetch.HTTPSFetch if (self.url.scheme == 
                'https') else urlfetch.HTTPFetch
        self.opener = opener_cls(self.proxy, True)
        del self.proxy

    def __str__(self):
        return ' %s %s %d %d %d' % (self.url.geturl(), self.crypto.getmode(),
                self.range0, self.range, self.max_threads)

    def _process_range(self, headers):
        for k in self._dirty_headers:
            del headers[k]
        range = headers.get('Range', '')
        m = self._range_re.search(range)
        if m:
            m = m.groups()
            if m[0] is None:
                if m[1] is None: m = None
                else:
                    m = 1, int(m[1])
                    if m[1] > self.range0: range = 'bytes=-1024'
            else:
                if m[1] is None:
                    m = 0, int(m[0])
                    range = 'bytes=%d-%d' % (m[1], m[1]+self.range0-1)
                else:
                    m = 2, int(m[0]), int(m[1])
                    if m[2]-m[1]+1 > self.range0:
                        range = 'bytes=%d-%d' % (m[1], m[1]+self.range0-1)
        if m is None:
            range = 'bytes=0-%d' % (self.range0 - 1)
        return m, range

    def _process_request(self, req):
        data = req.read_body()
        rawrange, range = self._process_range(req.headers)
        headers = httpheaders.HTTPHeaders(req.headers).__getstate__()
        request = {'method':req.command, 'url':req.url.geturl(), 'body':data,
                   'headers':headers, 'range':range}
        #print request
        return request, rawrange

    def _fetch(self, data):
        data = self.crypto.encrypt(data, self.key)
        try:
            resp = self.opener.open(self.url, data, 'POST', self.headers)
        except proxylib.ProxyError, e:
            return -1, 'Connect porxy/host failed'
        except Exception, e:
            return -1, str(e)
        if resp.status != 200:
            resp.close()
            return -1, '%s: %s' % (resp.status, resp.reason)
        return 0, resp

    def fetch(self, data):
        data, resp = self._fetch(data)
        if data == -1: return data, resp
        crypto = self.crypto.getcrypto(self.key)
        headers = httpheaders.HTTPHeaders()
        try:
            #print resp.read()
            zip, code, hlen = struct.unpack('>BHI', resp.read(7))
            if zip == 1:
                data = self.crypto.unpaddata(crypto.decrypt(resp.read()))
                data = zlib.decompress(data)
                content = data[hlen:]
                if code == 555:
                    raise ValueError('Server: '+content)
                headers.__setstate__(self.load_data(data[:hlen]))
                resp.close()
                return 1, code, headers, content
            elif zip == 0:
                if code == 555:
                    content = crypto.decrypt(resp.read()[hlen:])
                    raise ValueError('Server: '+self.crypto.unpaddata(content))
                h = crypto.decrypt(resp.read(hlen))
                headers.__setstate__(self.load_data(self.crypto.unpaddata(h)))
                return 0, code, headers, (resp, crypto)
            else:
                raise ValueError('Data format not match(%s)'%self.url.geturl())
        except Exception, e:
            resp.close()
            return -1, str(e)

    def read_data(self, type, data):
        if type == 1: return data
        resp, crypto = data
        data = self.crypto.unpaddata(crypto.decrypt(resp.read()))
        resp.close()
        return data

    def write_data(self, req, type, data):
        try:
            if type == 1:
                req.wfile.write(data)
            else:
                resp, crypto = data
                size = self.crypto.getsize(16384)
                data = crypto.decrypt(resp.read(size))
                req.wfile.write(self.crypto.unpaddata(data))
                data = resp.read(size)
                while data:
                    req.wfile.write(crypto.decrypt(data))
                    data = resp.read(size)
                resp.close()
        except proxylib.socket.error:
            req.wfile.close()
            raise

    def _need_range_fetch(self, req, res, range):
        headers = res[2]
        m = self._crange_re.search(headers.get('Content-Range', ''))
        if not m: return None
        m = map(int, m.groups())#bytes %d-%d/%d
        if range is None:
            start=0; end=m[2]-1
            code = 200
            del headers['Content-Range']
        else:
            if range[0] == 0: #bytes=%d-
                start=range[1]; end=m[2]-1
            elif range[0] == 1: #bytes=-%d
                start=m[2]-range[1]; end=m[2]-1
            else: #bytes=%d-%d
                start=range[1]; end=range[2]
            code = 206
            headers['Content-Range'] = 'bytes %d-%d/%d' % (start, end, m[2])
        headers['Content-Length'] = str(end-start+1)
        req.write_response(code, headers, size=headers['Content-Length'])
        if start == m[0]: #Valid
            self.write_data(req, res[0], res[3])
            start = m[1] + 1
        return start, end

    def _range_fetch(self, req, handler, request, start, end):
        t = time.time()
        if self.__range_fetch(req, handler, request, start, end):
            t = time.time() - t
            t = (end - start + 1) / 1000.0 / 1000 / t
            print '>>>>>>>>>> Range Fetch ended (all @ %sM/s)' % t
        else:
            req.close_connection = 1
            print '>>>>>>>>>> Range Fetch failed'

    def __range_fetch(self, req, handler, request, start, end):
        request['range'] = '' # disable server auto-range-fetch
        size = xrange(start+self.range0, end+1, self.range)
        tasks = [(0, start, start+self.range0-1)] + [None] * len(size)
        for i,s in enumerate(size, 1):
            e = s + self.range - 1
            if e > end: e = end
            tasks[i] = i, s, e
        size = min(len(tasks), len(handler)*2, self.max_threads)
        print ('>>>>>>>>>> Range Fetch started: threads=%d blocks=%d '
                'bytes=%d-%d' % (size, len(tasks), start, end))
        if size == 1:
            return self._single_fetch(req, handler, request, tasks)
        handler = list(handler); random.shuffle(handler)
        if size > len(handler): handler += handler[:size-len(handler)]
        results = [None] * len(tasks)
        mutex = threading.Lock()
        threads = {}
        for i in xrange(size):
            t = threading.Thread(target=handler[i]._range_thread,
                    args=(request, tasks, results, threads, mutex))
            threads[t] = set([])
            t.setDaemon(True)
        size = len(tasks)
        for t in threads: t.start()
        i = 0; t = False
        while i < size:
            if results[i] is not None:
                try:
                    self.write_data(req, 1, results[i])
                    results[i] = None
                    i += 1
                    continue
                except:
                    mutex.acquire()
                    del tasks[:]
                    mutex.release()
                    break
            if not threads: #All threads failed
                if t: break
                t = True; continue
            time.sleep(1)
        else:
            return True
        return False

    def _single_fetch(self, req, handler, request, tasks):
        try:
            for task in tasks:
                request['headers']['Range'] = 'bytes=%d-%d' % task[1:]
                data = zlib.compress(self.dump_data(request))
                for i in xrange(3):
                    self = random.choice(handler)
                    res = self.fetch(data)
                    if res[0] == -1:
                        time.sleep(2)
                    elif res[1] == 206:
                        #print res[2]
                        print '>>>>>>>>>> block=%d bytes=%d-%d' % task
                        self.write_data(req, res[0], res[3])
                        break
                else:
                    raise StopIteration('Failed')
        except:
            return False
        return True

    def _range_thread(self, request, tasks, results, threads, mutex):
        ct = threading.current_thread()
        while True:
            mutex.acquire()
            try:
                if threads[ct].intersection(*threads.itervalues()):
                    raise StopIteration('All threads failed')
                for i,task in enumerate(tasks):
                    if task[0] not in threads[ct]:
                        task = tasks.pop(i)
                        break
                else:
                    raise StopIteration('No task for me')
                request['headers']['Range'] = 'bytes=%d-%d' % task[1:]
                data = self.dump_data(request)
            except StopIteration, e:
                #print '>>>>>>>>>> %s: %s' % (ct.name, e)
                del threads[ct]
                break
            finally:
                mutex.release()
            data = zlib.compress(data)
            success = False
            for i in xrange(2):
                res = self.fetch(data)
                if res[0] == -1:
                    time.sleep(2)
                elif res[1] == 206:
                    try: data = self.read_data(res[0], res[3])
                    except: continue
                    if len(data) == task[2]-task[1]+1:
                        success = True
                        break
            mutex.acquire()
            if success:
                print '>>>>>>>>>> block=%d bytes=%d-%d'%task, len(data)
                results[task[0]] = data
            else:
                threads[ct].add(task[0])
                tasks.append(task)
                tasks.sort(key=lambda x: x[0])
            mutex.release()

    def dump_data(self, data):
        return pickle.dumps(data, 1)

    def load_data(self, data):
        return pickle.loads(data)

    def handle(self, handler, req):
        if not isinstance(handler, (list, tuple)):
            handler = handler,
        if len(handler) == 1:
            handlers = handler[0], handler[0]
        else:
            handlers = random.sample(handler, 2)
        request, range = self._process_request(req)
        data = zlib.compress(self.dump_data(request))
        errors = []
        for self in handlers:
            res = self.fetch(data)
            if res[0]!=-1: break
            errors.append(res[1])
        else:
            return req.send_error(502, str(errors))
        if res[1]==206 and req.command=='GET':
            data = self._need_range_fetch(req, res, range)
            if data:
                start, end = data
                if start > end: return #end
                return self._range_fetch(req, handler, request, start, end)
        req.write_response(res[1], res[2], size=res[2].get('Content-Length'))
        self.write_data(req, res[0], res[3])


init_time = 1
plugin_name = 'Proxy based on GAE'

def init(cls, config):
    import traceback
    server = [None] * len(config)
    for i,v in enumerate(config):
        if isinstance(v, basestring):
            v = {'url': v}
        try:
            server[i] = cls(v)
            print server[i]
        except:
            traceback.print_exc()
    return server

def init_plugin(config):
    return init(Handler, config)