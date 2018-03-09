import hmac
import hashlib

counter = 0
key = "ITSAKEY"

pool = [None] * 10

def refresh_pool():
    for i in range(10):
        pool[i] = truncate(hmac.new(key.encode(), str(counter + i).encode(), "sha256"))

def truncate(hmac):
    digest = hmac.hexdigest()
    return format(int(digest[:2], 16), "03d")

def accept_code(code):
    if code in pool:
        return True
    return False

refresh_pool()
print(pool)

print(accept_code("167"))
