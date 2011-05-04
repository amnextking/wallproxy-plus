__author__ = 'd3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64')
__version__ = '0.0.2'

import os
from wpconfig import main_dir as cert_dir
cert_dir = os.path.join(cert_dir, 'cert')
try:
    from OpenSSL import crypto
except ImportError:
    crypto = None
try:
    import ssl
except ImportError:
    ssl = None

def _createKeyPair(type=None, bits=1024):
    if type is None:
        type = crypto.TYPE_RSA
    pkey = crypto.PKey()
    pkey.generate_key(type, bits)
    return pkey

def _createCertRequest(pkey, subj, digest='sha1'):
    req = crypto.X509Req()
    subject = req.get_subject()
    for k,v in subj.iteritems():
        setattr(subject, k, v)
    req.set_pubkey(pkey)
    req.sign(pkey, digest)
    return req

def _createCertificate(req, issuerKey, issuerCert, serial,
                       notBefore, notAfter, digest='sha1'):
    cert = crypto.X509()
    cert.set_serial_number(serial)
    cert.gmtime_adj_notBefore(notBefore)
    cert.gmtime_adj_notAfter(notAfter)
    cert.set_issuer(issuerCert.get_subject())
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(issuerKey, digest)
    return cert

def _makeCA(dump=True):
    pkey = _createKeyPair(bits=2048)
    subj = {'countryName': 'CN', 'organizationalUnitName': 'WallProxy Root',
            'stateOrProvinceName': 'Internet', 'localityName': 'Cernet',
            'organizationName': 'WallProxy', 'commonName': 'WallProxy CA'}
    req = _createCertRequest(pkey, subj)
    cert = _createCertificate(req, pkey, req, 0, 0, 60*60*24*7305) #20 years
    if dump:
        pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    return pkey, cert

def _makeCert(host, cakey, cacrt, serial, dump=True):
    pkey = _createKeyPair()
    subj = {'countryName': 'CN', 'organizationalUnitName': 'WallProxy Branch',
            'stateOrProvinceName':'Internet', 'localityName': 'Cernet',
            'organizationName': host, 'commonName': host}
    req = _createCertRequest(pkey, subj)
    cert = _createCertificate(req, cakey, cacrt, serial, 0, 60*60*24*7305)
    if dump:
        pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    return pkey, cert

def read_file(filename):
    try:
        f = open(filename, 'rb')
        c = f.read()
        f.close()
        return c
    except IOError:
        return None

def write_file(filename, content):
    try:
        f = open(filename, 'wb')
        f.write(str(content))
        f.close()
    except IOError:
        pass

_g_serial = _g_CA = None

def checkCA():
    if not crypto: return
    global _g_serial, _g_CA
    #Check cert directory
    if not os.path.isdir(cert_dir):
        if os.path.isfile(cert_dir):
            os.remove(cert_dir)
        os.mkdir(cert_dir)
    #Check CA file
    cakeyFile = os.path.join(cert_dir, '_ca.key')
    cacrtFile = os.path.join(cert_dir, '_ca.crt')
    serialFile = os.path.join(cert_dir, '_serial')
    cakey = read_file(cakeyFile)
    cacrt = read_file(cacrtFile)
    _g_serial = read_file(serialFile)
    try:
        cakey = crypto.load_privatekey(crypto.FILETYPE_PEM, cakey)
        cacrt = crypto.load_certificate(crypto.FILETYPE_PEM, cacrt)
        _g_CA = cakey, cacrt
        _g_serial = int(_g_serial)
    except:
        _g_CA = cakey, cacrt = _makeCA(False)
        _g_serial = 0
        #Remove old certifications, because ca and cert must be in pair
        for name in os.listdir(cert_dir):
            path = os.path.join(cert_dir, name)
            if os.path.isfile(path):
                os.remove(path)
        cakey = crypto.dump_privatekey(crypto.FILETYPE_PEM, cakey)
        cacrt = crypto.dump_certificate(crypto.FILETYPE_PEM, cacrt)
        write_file(cakeyFile, cakey)
        write_file(cacrtFile, cacrt)
        write_file(serialFile, _g_serial)

def getCertificate(host):
    keyFile = os.path.join(cert_dir, '%s.key' % host)
    crtFile = os.path.join(cert_dir, '%s.crt' % host)
    if not os.path.isfile(keyFile) or not os.path.isfile(crtFile):
        if not crypto:
            keyFile = os.path.join(cert_dir, '_ca.key')
            crtFile = os.path.join(cert_dir, '_ca.crt')
            return (keyFile, crtFile)
        global _g_serial
        _g_serial += 1
        key, crt = _makeCert(host, _g_CA[0], _g_CA[1], _g_serial)
        write_file(keyFile, key)
        write_file(crtFile, crt)
        write_file(os.path.join(cert_dir,'_serial'), _g_serial)
    return keyFile, crtFile

class Handler:
    def handle(self, handler, req):
        if not ssl:
            return req.send_error(501, 'ssl needs Python2.6 or later')
        host = req.path.rsplit(':', 1)[0]
        keyFile, crtFile = getCertificate(host)
        req.connection.sendall('HTTP/1.1 200 OK\r\n\r\n')
        try:
            ssl_sock = ssl.wrap_socket(req.connection, keyFile, crtFile, True)
        except ssl.SSLError, e:
            return req.log_error('"%s" SSLError:%s', req.requestline, e)
        addr = req.client_address[0],req.client_address[1],'https://'+req.path
        try: req.__class__(ssl_sock, addr, req.server)
        except: pass


init_time = 0
plugin_name = 'https to http'

def init_plugin(ignore):
    print ' SSL module support:', 'YES' if ssl else 'NO'
    print ' OpenSSL module support:', 'YES' if crypto else 'NO'
    checkCA()
    return Handler()