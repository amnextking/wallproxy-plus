__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')

import os, traceback

def main_dir():
    import sys, imp
    if hasattr(sys, 'frozen') or imp.is_frozen('__main__'):
        return os.path.abspath(os.path.dirname(sys.executable))
    return os.path.abspath(os.path.dirname(sys.argv[0]))
main_dir = main_dir()

def check_client(ip, reqtype, args): return True
def find_sock_handler(reqtype, ip, port, cmd): return None
def find_http_handler(method, url, headers): return None

config = {}
def get_config():
    global config
    for key in config: config[key] = None #gc
    def dnsDomainIs(host, domain):
        if host == domain: return True
        if domain[0] != '.': domain = '.' + domain
        return host.endswith(domain)
    import __builtin__, re
    config = {'__builtins__': __builtin__, 're': re,
               'check_client': check_client,
               'find_sock_handler': find_sock_handler,
               'find_http_handler': find_http_handler,
               'dnsDomainIs': dnsDomainIs,
               'server': {}, 'plugins': {}, '__init__': lambda plugin:None,
               '__del__': set(['server','plugins','__init__','__del__'])}
    conf_file = os.path.join(main_dir, 'proxy.conf')
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
    conf_file = os.path.join(main_dir, 'proxy.conf')
    mtime = os.path.getmtime(conf_file)
    while True:
        time.sleep(interval)
        _mtime = os.path.getmtime(conf_file)
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