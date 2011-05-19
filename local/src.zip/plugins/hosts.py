# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__patcher__ = 'ZHRtYWppYUAxNjMuY29t'.decode('base64')
__version__ = '0.0.4'

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
    tag = dict((m[0],i) for i,m in enumerate(hosts[1]))
    old_items = set(hosts[0].items()), set(hosts[1])
    for line in hosts_.splitlines():
        line = line.strip().lower()
        if not line or line.startswith('#'): continue
        line = line.split()
        if len(line) != 2: continue
        ip, host = line
        if host.startswith('.'):
            if host in tag:
                hosts[1][tag[host]] = host, ip
            else:
                tag[host] = len(hosts[1])
                hosts[1].append((host, ip))
        else:
            hosts[0][host] = ip
    new_items = set(hosts[0].items()), set(hosts[1])
    c_items = new_items[0]-old_items[0], new_items[1]-old_items[1]
    print ' updated %d,%d dns mapping' % (len(c_items[0]), len(c_items[1]))
    return Handler()
