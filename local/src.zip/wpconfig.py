# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__patcher__ = 'ZHRtYWppYUAxNjMuY29t'.decode('base64')

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
def use_gae_https(gaeproxy):
    httpsproxy = []
    for s in gaeproxy:
        if isinstance(s, basestring): s = {'url': s}
        httpsproxy.append(s.copy())
        httpsproxy[-1]['url'] = httpsproxy[-1]['url'].replace('http:', 'https:')
    return httpsproxy
exec """eJyFz0tPg0AUBeCfMwtboLX4IHFRRlNc0IRgtdUYMwwzToHpXOehUNP/Lutiwvaek+/kfh
IGWrXd3dsvcrpBERLWQuT7R26Y5B4BMKCsR5X0ObNUeCAATVDNur5LFkEZ0KsyvA5u6ZzfFH1CdQdW
9eHyIZ/iGE8v5/1VkvbDCs1IaVAUniZna1WjrZMja5jTGPLcsW8drw71Bg2YRrVWqhHGaJ3ATK5x3N
DNFrsho0iVvdoRppDbVRg/Hl6ykmf74+4fptpT60afqvMmoD8mSNP0foGHDLgvLcgII5I6eZ5d0Cdr
lnhdlOj0/gdfH6DY""".decode('base64').decode('zlib')
__del__.add('use_gae_https'); plugins['plugins.gaeproxy'] = 'gaeproxy'
server_type = 'gaeproxy'; __del__.add('server_type')
def add_range(url, headers):
    if dnsDomainIs(url.hostname, 'c.youtube.com'): return True
    return False
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
def find_http_handler(method, url, headers):
    if method not in ('GET', 'POST', 'HEAD', 'PUT', 'DELETE'): return rawproxy[0]
    return gaeproxy
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
    config = {
        '__builtins__': __builtin__, '__file__': conf_file,
        '__name__': __name__+'.conf',
    }
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