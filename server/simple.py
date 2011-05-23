# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'ZHRtYWppYUAxNjMuY29t'.decode('base64')
__version__ = '0.0.1'

import gaeproxy

class MainHandler(gaeproxy.MainHandler):
    _cachename = 'wp_cache2'

    def dump_data(self, dic):
        if 'headers' in dic:
            dic['headers'] = '&'.join('%s=%s' % (k,str(v).encode('hex')) for k,v in dic['headers'].iteritems())
        return '&'.join('%s=%s' % (k,str(v).encode('hex')) for k,v in dic.iteritems())

    def load_data(self, qs):
        dic = dict((k,v.decode('hex')) for k,v in (x.split('=') for x in qs.split('&')))
        if 'headers' in dic:
            dic['headers'] = dict((k,v.decode('hex')) for k,v in (x.split('=') for x in qs.split('&')))
        return dic

def main():
    application = gaeproxy.webapp.WSGIApplication([(r'/.*', MainHandler)], debug=True)
    gaeproxy.run_wsgi_app(application)

if __name__ == '__main__':
    main()
