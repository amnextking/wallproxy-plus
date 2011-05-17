# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__version__ = '0.0.1'

import re
from util import urlinfo, urlfetch

def _sumRule(keyword, hash, share):
    k = map(len, keyword)
    hk = map(len, hash)
    hv = [sum([len(v) for v in t.itervalues()]) for t in hash]
    s = map(len, share)
    num = 'k%d|%d+h%d:%d|%d:%d+s%d|%d=%d' % (k[0], k[1],
            hk[0], hv[0], hk[1], hv[1], s[0], s[1], sum(k+hv+s))
    return num

def _parseRule(rule):
    keyword = set(), set()
    hash = {}, {}
    share = set(), set()
    for line in rule.splitlines()[1:]:
        # Ignore the first line ([AutoProxy x.x]), empty lines and comments
        line = line.strip().lower()
        if not line or line[0] in ('[','!','#'):
            continue
        rule_type = 1
        if line.startswith('@@'): # Exceptions
            line = line[2:]
            rule_type = 0
        if line[0]=='/' and line[-1]=='/': # Regular expressions
            line = line[1:-1]
        else:
            # Strictly mapping to keyword blocking
            line = re.sub(r'^(https?:)', r'|\1', line)
            if line[0]!='|' and '*' not in line: # Maybe keyword
                i1 = line.find('.'); i2 = line.find('/'); i3 = line.find('?')
                if i1==-1 or (i2!=-1 and i2<i1) or (i2==-1 and i3!=-1):
                    keyword[rule_type].add(line)
                    continue
            # Remove multiple wildcards
            line = re.sub(r'\*+', '*', line)
            # Remove anchors following separator placeholder
            line = re.sub(r'\^\|$', '^', line, 1)
            # Escape special symbols
            line = re.sub(r'(\W)', r'\\\1', line)
            # Replace wildcards by .*
            line = re.sub(r'\\\*', '.*', line)
            # Process separator placeholders
            line = re.sub(r'\\\^', r'(?:[^\w\-.%\u0080-\uFFFF]|$)', line)
            # Process extended anchor at expression start
            line = re.sub(r'^\\\|\\\|', r'^[\w\-]+:\/+(?!\/)(?:[^\/]+\.)?', line, 1)
            # Process anchor at expression start
            line = re.sub(r'^\\\|', '^', line, 1)
            # Process anchor at expression end
            line = re.sub(r'\\\|$', '$', line, 1)
            # Remove leading wildcards
            line = re.sub(r'^(?:\.\*)', '', line, 1)
            # Remove trailing wildcards
            line = re.sub(r'(?:\.\*)$', '', line, 1)
        if not line: continue # Invalid
        # Regular expressions
        idot = line.find('\\.')
        if idot == -1: hash_key = None
        else:
            # Find domain field
            istart = line.find(':') + 1
            if istart > idot: istart = 0
            iend = line.find('\\/', idot+2)
            if iend == -1: iend = line.find('.*', idot+2)
            tmp = line[istart:iend if iend!=-1 else None].replace('\\-', '-')
            # Remove uncertain field
            tmp = re.sub(r'(?:\(.*?\)\?)|(?:\(.*?\|.*?\))', '()', tmp)
            tmp = re.sub(r'(?:[\w-]+\.?)?(?:\*|\?|\|)(?:[\w-]+)?', '.*', tmp)
            tmp = re.findall(r'[\w-]{2,}', tmp)
            # Try get a hash word
            try:
                hash_key = tmp.pop()
                if tmp: hash_key = max(tmp, key=lambda x:len(x))
            except IndexError:
                hash_key = None
        if hash_key:
            if hash_key in hash[rule_type]:
                hash[rule_type][hash_key].add(line)
            else:
                hash[rule_type][hash_key] = set([line])
        else:
            share[rule_type].add(line)
    return (keyword,hash,share), _sumRule(keyword, hash, share)

def _fetchRule(url, proxy):
    url = urlinfo.URL(url)
    try:
        if url.scheme == 'file':
            import os, wpconfig
            url.path = os.path.join(wpconfig.main_dir, url.path)
            fp = open(url.path, 'rb')
            date = None
        else:
            try:
                fp = urlfetch.fetch(url, proxy=proxy)
            except:
                import time
                time.sleep(10)
                fp = urlfetch.fetch(url, proxy=proxy)
            if fp.status != 200:
                fp.close()
                return None
            date = fp.msg.getheader('last-modified')
        rule = fp.read()
        fp.close()
    except:
        return None
    try:
        tmp = rule.decode('base64')
        tmp[5:15].decode('ascii')
        rule = tmp
    except:
        pass
    rule, num = _parseRule(rule)
    return rule, '%s %s' % (num, date) if date else num

def initRule(rulelist):
    keyword = [set(), set()]
    hash = [{}, {}]
    share = [set(), set()]
    info = []
    if isinstance(rulelist, basestring):
        rulelist = (rulelist,)
    for rule in rulelist:
        if not rule: continue
        if isinstance(rule, basestring):
            url, proxy = rule, None
        elif len(rule) == 1:
            url, proxy = rule[0], None
        else:
            url, proxy = rule[0], rule[1]
        res = _fetchRule(url, proxy)
        if not res:
            info.append((url, 'failed'))
            continue
        info.append((url, res[1]))
        kw, hh, sh = res[0]
        for i in xrange(2):
            keyword[i] |= kw[i]
            for k,v in hh[i].iteritems():
                if k in hash[i]: hash[i][k] |= v
                else: hash[i][k] = v
            share[i] |= sh[i]
    info.append(('Total', _sumRule(keyword, hash, share)))
    return (keyword,hash,share), info

class jsRegExp:
    def __init__(self, r):
        self.r = r
    def __json__(self):
        return '/%s/' % self.r

def dump2js(o):
    def iterdump(o):
        if isinstance(o, (list, tuple, set)):
            yield '['
            i = len(o)
            for v in o:
                for v in iterdump(v): yield v
                i -= 1
                if i > 0: yield ', '
            yield ']'
        elif isinstance(o, dict):
            yield '{'
            i = len(o)
            for k,v in o.iteritems():
                for k in iterdump(k): yield k
                yield ': '
                for v in iterdump(v): yield v
                i -= 1
                if i > 0: yield ', '
            yield '}'
        elif isinstance(o, basestring):
            yield '"%s"' % o.encode('string-escape')
        elif isinstance(o, (int, long, float)):
            yield str(o)
        elif o is True: yield 'true'
        elif o is False: yield 'false'
        elif o is None: yield 'null'
        else:
            yield o.__json__()
    return ''.join(iterdump(o))

def initRules(ruledict, callback, prefix1, prefix2):
    infos = []
    for key,rulelist in ruledict.iteritems():
        rule, info = initRule(rulelist)
        kw, hh, sh = rule
        for i in xrange(2):
            for k,v in hh[i].iteritems():
                hh[i][k] = [callback(r) for r in v]
            sh[i] = [callback(r) for r in sh[i]]
        ruledict[key] = kw + hh + sh
        for i,v in enumerate(info):
            info[i] = '%s%s: %s' % (prefix2, v[0], v[1])
        info = '\n'.join(info)
        infos.append('%sRuleinfo for %s:\n%s' % (prefix1, key, info))
    return '\n'.join(infos)

def generatePAC(ruledict, pacFile):
    rulesBegin = '// AUTO-GENERATED RULES, DO NOT MODIFY!'
    rulesEnd = '// END OF AUTO-GENERATED RULES'
    defaultPacTemplate = '''//Proxy Auto Configuration

function FindProxyForURL(url, host) {
    for (var p in RULES)
        if (inAutoProxy(p, url, host)) return p;
    return 'DIRECT';
}

function dnsDomainIs(host, domain) {
    if (host == domain) return true;
    if (domain.charAt(0) != '.') domain = '.' + domain;
    return (host.length >= domain.length &&
            host.substring(host.length - domain.length) == domain);
}

%(rulesBegin)s
%(rulesCode)s
%(rulesEnd)s

function inAutoProxy(r,u,h){u=u.toLowerCase();r=RULES[r];var s=u.split(":",1),k,i;if(s=="http"){k=r[0];i=k.length;while(--i>=0)if(u.indexOf(k[i])!=-1)return false}h=h.split(".");var j,t;k=r[2];j=h.length;while(--j>=0){i=h[j];if(i in k&&k[i].constructor==Array){t=k[i];i=t.length;while(--i>=0)if(t[i].test(u))return false}}k=r[4];i=k.length;while(--i>=0)if(k[i].test(u))return false;if(s=="http"){k=r[1];i=k.length;while(--i>=0)if(u.indexOf(k[i])!=-1)return true}k=r[3];j=h.length;while(--j>=0){i=h[j]; if(i in k&&k[i].constructor==Array){t=k[i];i=t.length;while(--i>=0)if(t[i].test(u))return true}}k=r[5];i=k.length;while(--i>=0)if(k[i].test(u))return true;return false};'''
    try:
        fp = open(pacFile, 'r')
        template = fp.read().replace('%','%%')
        fp.close()
    except IOError:
        template = defaultPacTemplate
    else:
        args = re.escape(rulesBegin), re.escape(rulesEnd)
        pattern = r'(?ms)^(\s*%s\s*)^.*$(\s*%s\s*)$' % args
        template, n = re.subn(pattern, r'\1%(rulesCode)s\2', template)
        if n==0: template = defaultPacTemplate
    args = {'rulesBegin': rulesBegin, 'rulesEnd': rulesEnd}
    info = initRules(ruledict, jsRegExp, '// ', '// ')
    args['rulesCode'] = '%s\nvar RULES = %s;' % (info, dump2js(ruledict))
    print ' Writing PAC to file...'
    fp = open(pacFile, 'w')
    fp.write(template % args)
    fp.close()
    print ' Done!'

class Handler:
    def __init__(self, ruledict):
        print initRules(ruledict, re.compile, ' ', '  ')
        self.ruledict = ruledict

    def __call__(self, rule, url):
        rule = self.ruledict[rule]
        scheme = url.scheme
        tokens = url.hostname.split('.')
        url = url.geturl().lower()
        if scheme == 'http':
            for k in rule[0]:
                if k in url:
                    return False
        r = rule[2]
        for k in tokens:
            if k in r:
                for k in r[k]:
                    if k.search(url):
                        return False
        for k in rule[4]:
            if k.search(url):
                return False
        if scheme == 'http':
            for k in rule[1]:
                if k in url:
                    return True
        r = rule[3]
        for k in tokens:
            if k in r:
                for k in r[k]:
                    if k.search(url):
                        return True
        for k in rule[5]:
            if k.search(url):
                return True
        return False
    test = __call__


init_time = 100
plugin_name = 'AutoProxy'

def init_plugin(config):
    if isinstance(config, dict):
        return Handler(config)
    import os, wpconfig
    pacFile = os.path.join(wpconfig.main_dir, config[1])
    generatePAC(config[0], pacFile)