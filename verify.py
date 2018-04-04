#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

__appname__     = "verify"
__author__      = "Marco Sirabella"
__copyright__   = ""
__credits__     = ["Marco Sirabella"]  # Authors and bug reporters
__license__     = "GPL"
__version__     = "1.0"
__maintainers__ = "Marco Sirabella"
__email__       = "marco@sirabella.org"
__status__      = "Prototype"  # "Prototype", "Development" or "Production"
__module__      = ""


import hmac
import hashlib as sha256


class HOTP():
    codelen = 3

    def __init__(self, secret, hash_func=sha256.sha256):
        self.secret = secret
        self.hash_func = hash_func

    def at(self, counter):
        return self.truncate(
            hmac.new(
                self.secret.encode(),
                str(counter).encode(),
                self.hash_func
            ).hexdigest())

    def truncate(self, hashstr):
        return format(int(hashstr, 16) % (10 ** self.codelen),
                      '0{}d'.format(self.codelen))



class Counter():
    def __init__(self, filename, start=None):
        self.filename = filename
        with open(self.filename, 'r') as file:
            if file.read() == '':
                start = -1
        if start is not None:
            self._set(start)

    def _set(self, num):
        with open(self.filename, 'w') as file:
            file.write(str(num))

    def __call__(self):
        with open(self.filename, 'r') as file:
            num = int(file.read())
        num += 1
        self._set(num)
        return num


hotp = HOTP("ITSAKEY", sha256.sha256)

c = Counter("index.txt")
key = hotp.at(c())

print("Content-type: plain/text\n")
print(key + hotp.at(str(key + "11")))
