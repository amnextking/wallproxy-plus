import sys, os, re
dll = 'python%s%s.dll' % (sys.version[0], sys.version[2])
dir = os.path.dirname(sys.argv[0])
for fn in ('OpenSSL', 'Crypto', 'Crypto/Cipher'):
    open(os.path.join(dir, fn, '__init__.py'), 'wb').close()
files = [os.path.join(dir, 'OpenSSL/crypto.pyd')]
dir = os.path.join(dir, 'Crypto/Cipher')
for fn in os.listdir(dir):
    if fn.endswith('.pyd'):
        files.append(os.path.join(dir, fn))
for fn in files:
    print fn,
    try:
        fp = open(fn, 'rb')
        data = fp.read()
        fp.close()
        newdata = re.sub(r'python\d{2}\.dll', dll, data, 1)
        if newdata != data:
            try:
                os.rename(fn, fn+'.bak')
            except:
                print 'backup failed',
            fp = open(fn, 'wb')
            fp.write(newdata)
            fp.close()
            print 'done'
        else:
            print 'pass'
    except IOError, e:
        print e
