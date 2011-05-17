# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')

from UserDict import IterableUserDict

__all__ = ['HTTPHeaders']

class HTTPHeaders(IterableUserDict):

    def __setitem__(self, key, item):
        self.data[key.title()] = item

    def add(self, key, item):
        key = key.title()
        if key in self.data:
            self.data[key] = '%s\r\n%s: %s' % (self.data[key], key, item)
        else:
            self.data[key] = item

    def __delitem__(self, key):
        try:
            del self.data[key]
        except KeyError:
            pass

    def readheaders(self, fp):
        if isinstance(fp, basestring):
            fp = fp.splitlines()
        for line in fp:
            k, s, v = line.partition(':')
            if not s: break
            self.add(k, v.strip())

    def update(self, dic=None, **kwargs):
        if not dic:
            pass
        elif isinstance(dic, HTTPHeaders):
            self.data.update(dic.data)
        elif isinstance(dic, basestring) or hasattr(dic, 'readline'):
            self.readheaders(dic)
        else:
            try:
                for k in dic.keys():
                    self[k] = dic[k]
            except AttributeError:
                for k,v in dic:
                    self.add(k, v)
        if kwargs:
            self.update(kwargs)

    def __str__(self):
        buf = [None] * len(self.data)
        for i,v in enumerate(self.data.iteritems()):
            buf[i] = '%s: %s\r\n' % v
        return ''.join(buf)

    def __getstate__(self):
        return self.data

    def __setstate__(self, state):
        self.data = state