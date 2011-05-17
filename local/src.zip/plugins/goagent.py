# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'ZHRtYWppYUAxNjMuY29t'.decode('base64')
__version__ = '0.0.1'

from util import crypto as _crypto
import forold

class Handler(forold.Handler):
    crypto = _crypto.Crypto('XOR--0'); key = ''

    def dump_data(self, dic):
        return '&'.join('%s=%s' % (k, str(v).encode('hex')) for k, v in dic.iteritems())

    def load_data(self, qs):
        return dict((k, v.decode('hex')) for k, v in (x.split('=') for x in qs.split('&')))

    def __init__(self, config):
        config.pop('crypto', None)
        self.password = config.pop('key', '')
        forold.Handler.__init__(self, config)

    def _process_request(self, req):
        request, rawrange = forold.Handler._process_request(self, req)
        del request['range']
        request['password'] = self.password
        return request, rawrange

init_time = 3
plugin_name = 'Plugin for GoAgent'

def init_plugin(config):
    return forold.gaeproxy.init(Handler, config)