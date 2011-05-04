__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__version__ = '0.0.2'

from util import proxylib

class Handler:
    def __call__(self, host):
        newhost = proxylib.map_hosts(host)
        return newhost!=host
    test = __call__

init_time = 0
plugin_name = 'local dns mapping'

def init_plugin(hosts_):
    import re
    re_split = re.compile(r'\s+').split
    hosts = proxylib.hosts
    old_items = set(hosts.items())
    for line in hosts_.splitlines():
        line = line.strip().lower()
        if not line or line.startswith('#'): continue
        line = re_split(line, 1)
        if len(line) != 2: continue
        hosts[line[1]] = line[0]
    new_items = set(hosts.items())
    print ' updated %d dns mapping' % (len(new_items - old_items))
    return Handler()
