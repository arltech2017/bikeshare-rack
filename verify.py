#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

from google.oauth2 import id_token
from google.auth.transport import requests

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



hotp = HOTP("ITSAKEY", sha256.sha256)

c = Counter("index.txt")
key = hotp.at(c())

def validate_user(user):
    if user['hd'] != 'apsva.us':
        return False
    return True

def get_bike_index():
    return 2

print("Content-type: text/plain\n")
#print('hi')
token = input()
#token = input()
user = id_token.verify_oauth2_token(token, requests.Request())
if validate_user(user):
    bike_index = get_bike_index()
    print(key + hotp.at(str(key + str(bike_index))))
else:
    print("invalid user, what did you do?")
