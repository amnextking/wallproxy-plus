# Copyright (C) 2010-2011 | GNU GPLv3
__author__ = '%s & %s' % ('d3d3LmVodXN0QGdtYWlsLmNvbQ=='.decode('base64'),
             'YnJvbnplMW1hbkBnbWFpbC5jb20='.decode('base64'))

import hashlib, itertools

__all__ = ['Crypto']

class XOR:
    '''XOR with pure Python in case no PyCrypto'''
    def __init__(self, key):
        self.key = key

    def encrypt(self, data):
        xorsize = 1024
        key = itertools.cycle(map(ord, self.key))
        dr = xrange(0, len(data), xorsize)
        ss = [None] * len(dr)
        for i,j in enumerate(dr):
            dd = [ord(d)^k for d,k in itertools.izip(data[j:j+xorsize], key)]
            ss[i] = ''.join(map(chr, dd))
        return ''.join(ss)
    decrypt = encrypt


class NUL:
    def encrypt(self, data):
        return data
    decrypt = encrypt


class Crypto:

    _BlockSize = {'AES':16, 'ARC2':8, 'ARC4':1, 'Blowfish':8, 'CAST':8,
                  'DES':8, 'DES3':8, 'IDEA':8, 'RC5':8, 'XOR':1}
    _Modes = ['ECB', 'CBC', 'CFB', 'OFB', 'PGP'] #CTR needs 4 args
    _KeySize = {'AES':[16,24,32], 'CAST':xrange(5,17),
                'DES':[8], 'DES3':[16,24], 'IDEA':[16]}

    def __init__(self, mode='AES-CBC-32'):
        mode = mode.split('-')
        mode += [''] * (3 - len(mode))
        #check cipher
        self.cipher = mode[0] if mode[0] else 'AES'
        if self.cipher not in self._BlockSize:
            raise ValueError('Invalid cipher: '+self.cipher)
        #check ciphermode
        if self._BlockSize[self.cipher] == 1:
            self.ciphermode = ''
        else:
            self.ciphermode = mode[1] if mode[1] in self._Modes else 'CBC'
        #check keysize
        try:
            self.keysize = int(mode[2])
        except ValueError:
            self.keysize = 32
        if self.keysize != 0:
            if self.cipher in self._KeySize:
                keysize = self._KeySize[self.cipher]
                if self.keysize not in keysize:
                    self.keysize = keysize[-1]
        #avoid Memmory Error
        if self.cipher=='RC5' and self.keysize in (1, 57): self.keysize=32
        #try to import Crypto.Cipher.xxxx
        try:
            cipherlib = __import__('Crypto.Cipher.'+self.cipher, fromlist='x')
            self._newobj = cipherlib.new
            if self._BlockSize[self.cipher] != 1:
                self._ciphermode = getattr(cipherlib, 'MODE_'+self.ciphermode)
        except ImportError:
            if self.cipher == 'XOR': self._newobj = XOR
            else: raise

    def paddata(self, data):
        blocksize = self._BlockSize[self.cipher]
        if blocksize != 1:
            padlen = (blocksize - len(data) - 1) % blocksize
            data = '%s%s%s' % (chr(padlen), ' '*padlen, data)
        return data

    def unpaddata(self, data):
        if self._BlockSize[self.cipher] != 1:
            padlen = ord(data[0])
            data = data[padlen+1:]
        return data

    def getcrypto(self, key):
        if self.keysize==0 and key=='':
            return NUL()
        khash = hashlib.sha512(key).digest()
        if self.keysize != 0:
            key = khash[:self.keysize]
        blocksize = self._BlockSize[self.cipher]
        if blocksize == 1:
            return self._newobj(key)
        return self._newobj(key, self._ciphermode, khash[-blocksize:])

    def encrypt(self, data, key):
        crypto = self.getcrypto(key)
        data = self.paddata(data)
        return crypto.encrypt(data)

    def decrypt(self, data, key):
        crypto = self.getcrypto(key)
        data = crypto.decrypt(data)
        return self.unpaddata(data)

    def getmode(self):
        return '%s-%s-%d' % (self.cipher, self.ciphermode, self.keysize)

    def __str__(self):
        return '%s("%s")' % (self.__class__, self.getmode())

    def getsize(self, size):
        blocksize = self._BlockSize[self.cipher]
        return (size + blocksize - 1) // blocksize * blocksize

class Crypto2(Crypto):
    def paddata(self, data):
        blocksize = self._BlockSize[self.cipher]
        if blocksize != 1:
            padlen = (blocksize - len(data) - 1) % blocksize
            data = '%s%s%s' % (data, ' '*padlen, chr(padlen))
        return data

    def unpaddata(self, data):
        if self._BlockSize[self.cipher] != 1:
            padlen = ord(data[-1])
            data = data[:-(padlen+1)]
        return data