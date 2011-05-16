__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')

import os, traceback

def main_dir():
    import sys, imp
    if hasattr(sys, 'frozen') or imp.is_frozen('__main__'):
        return os.path.abspath(os.path.dirname(sys.executable))
    return os.path.abspath(os.path.dirname(sys.argv[0]))
main_dir = main_dir()
conf_file = os.path.join(main_dir, 'proxy.conf')

_default_config = '''
import re
server, plugins = {'log_file': ''}, {}
def __init__(plugin): pass
__del__ = set(['server', 'plugins', '__init__', '__del__'])
hosts = 'www.google.cn .appspot.com'
plugins['plugins.hosts'] = 'hosts'
exec """aW1wb3J0IHpsaWI7ZXhlYyB6bGliLmRlY29tcHJlc3MoImVKeU5rVnRQd2tBUWhmOEs0V1
VoUWlrSXFKZyswTldBRDVBMEZVV05JZHZ0MWtKMzZiZ1hydUcvUzRrdjFocDhtc25KT2QvSlpNQUVm
RTVuSDRUTllxM0JLYi90a1NDYm1ZNGxJNkZDdlZLM1ZrSkc4dU9HTWtldjBkaEZpb25JSWdBS1VtM1
JWRFFpcG1sc1FRem82S1p5Q3pyTkF2MTd2NDVkWEw5c1pYckN0cGxJMm5abzAyN1l1Ykp2YUN1NkR0
Q2hWdHJuT2haY2FpUCs3dmhtNFlpNjRQdUdyYVE3V0NhVEloUlBOMXFrWjFGS3lpRTB4Umk3bkU2bT
JCU2hVckx3WHZWWlZDQ21nNDc3c0h6MndzaWI3MTRLVVlzNTFlWWZCeVkrdCtsYTJhUFI2SzZOaTFC
Z1BtVk16cUxpWVRKOGFsN1FSNjM2ZUJ5RTZQQmV2b1dmLzFkT1RyQWtBMDRvcTV6S1VPMDBGS3JtZ3
c1YkVWN0ppYjljcXRDbXFsOXNodHI5Ii5kZWNvZGUoImJhc2U2NCIpKQ==""".decode('base64')
del zlib; __del__.add('public_gae_http'); __del__.add('public_gae_https')
gaeproxy = public_gae_http; plugins['plugins.gaeproxy'] = 'gaeproxy'
def add_range(url, headers):
    if dnsDomainIs(url.hostname, 'c.youtube.com'): return True
    return False
gaeproxy[0]['add_range'] = add_range
autoproxy = {}
autoproxy['PROXY 127.0.0.1:8086; DIRECT'] =(
('http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt','http://127.0.0.1:8086'),
'file://userlist.ini',)
autoproxy = autoproxy, 'proxy.pac'; __del__.add('autoproxy')
plugins['plugins.autoproxy'] = 'autoproxy'
rawproxy = (None,)
plugins['plugins.rawproxy'] = 'rawproxy'
fakehttps = None
plugins['plugins.fakehttps'] = 'fakehttps'
def check_client(ip, reqtype, args): return True
def find_http_handler(method, url, headers): return gaeproxy
def find_sock_handler(reqtype, ip, port, cmd):
    if reqtype == 'https': return fakehttps
    return rawproxy[0]
def dnsDomainIs(host, domain):
    if host == domain: return True
    if domain[0] != '.': domain = '.' + domain
    return host.endswith(domain)
'''

config = {}
def get_config():
    global config
    for key in config: config[key] = None #gc
    import __builtin__
    config = {'__builtins__': __builtin__}
    exec _default_config in config
    try:
        execfile(conf_file, config)
    except:
        traceback.print_exc()
    return config['server']

def _init_plugin(plugins):
    init = config['__init__']
    plugins.sort(key=lambda x:x[0].init_time)
    for mod,cfg in plugins:
        try:
            if cfg in config:
                print 'Initializing "%s#%s" with "%s":'%(mod.__name__,
                      mod.__version__, cfg), mod.plugin_name
                config[cfg] = mod.init_plugin(config[cfg])
            else:
                print 'Initializing "%s":'%mod.__name__, mod.plugin_name
                mod.init_plugin()
            init(mod.__name__)
        except:
            traceback.print_exc()

def set_config(call_time):
    global check_client, find_sock_handler, find_http_handler
    check_client = config['check_client']
    find_sock_handler = config['find_sock_handler']
    find_http_handler = config['find_http_handler']
    plugins = [], []
    for mod,cfg in config['plugins'].iteritems():
        try:
            mod = __import__(mod, fromlist='x')
            plugins[int(mod.init_time>=50)].append((mod, cfg))
        except ImportError, e:
            print 'ImportError:', e
    if call_time==2 or not call_time:
        _init_plugin(plugins[0])
    if call_time:
        _init_plugin(plugins[1])
        for k in config['__del__']:
            if k in config:
                del config[k]

def watch_config(msg='', interval=5):
    import time
    def getmtime():
        try: return os.path.getmtime(conf_file)
        except: return 0
    mtime = getmtime()
    while True:
        time.sleep(interval)
        _mtime = getmtime()
        if mtime != _mtime:
            print msg
            get_config(); set_config(2)
            print msg
            mtime = _mtime

def get_logger(filename, format, maxKB, backupCount):
    if filename == '':
        class Logger:
            def __getattr__(self, name):
                return lambda *args, **kwargs: None
        return Logger()
    import logging
    import logging.handlers
    logger = logging.getLogger('WallProxy')
    logger.setLevel(logging.INFO)
    if filename:
        filename = os.path.join(main_dir, filename)
        handler = logging.handlers.RotatingFileHandler(filename,
                    maxBytes=maxKB*1024, backupCount=backupCount)
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(format))
    logger.addHandler(handler)
    return logger