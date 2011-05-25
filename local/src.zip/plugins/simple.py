# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'ZHRtYWppYUAxNjMuY29t'.decode('base64')
__version__ = '0.0.2'

import gaeproxy

class Handler(gaeproxy.Handler):
    def dump_data(self, dic):
        return '&'.join('%s=%s' % (k,str(v).encode('hex')) for k,v in dic.iteritems())

    def load_data(self, qs):
        return dict((k,v.decode('hex')) for k,v in (x.split('=') for x in qs.split('&'))) if qs else {}

    def _process_request(self, req):
        data = req.read_body()
        rawrange, range = self._process_range(req.headers)
        if req.command=='GET' and self.add_range(req.url, req.headers):
            req.headers['Range'] = range
        request = {'method':req.command, 'url':req.url.geturl(), 'body':data,
                   'headers':req.headers, 'range':range}
        return request, rawrange


init_time = 2
plugin_name = 'Simple packer for gaeproxy'

def init_plugin(config):
    return gaeproxy.init(Handler, config)
