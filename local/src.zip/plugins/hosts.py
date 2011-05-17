# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__patcher__ = 'ZHRtYWppYUAxNjMuY29t'.decode('base64')
__version__ = '0.0.3'

from util import proxylib

class Handler:
    def __call__(self, host):
        newhost = proxylib.map_hosts(host)
        return newhost!=host
    test = __call__

init_time = 0
plugin_name = 'local dns mapping'

def init_plugin(hosts_):
    hosts = proxylib.hosts
    old_items = set(hosts[0].items()), set(hosts[1].items())
    for line in hosts_.splitlines():
        line = line.strip().lower()
        if not line or line.startswith('#'): continue
        line = line.split()
        if len(line) != 2: continue
        hosts[int(line[1].startswith('.'))][line[1]] = line[0]
    new_items = set(hosts[0].items()), set(hosts[1].items())
    c_items = new_items[0]-old_items[0], new_items[1]-old_items[1]
    print ' updated %d,%d dns mapping' % (len(c_items[0]), len(c_items[1]))
    return Handler()
