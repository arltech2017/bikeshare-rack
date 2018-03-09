import hmac
import hashlib

counter = 0
key = "ITSAKEY"

pool = [None] * 10

def refresh_pool():
    for i in range(len(pool)):
        pool[i] = truncate(hmac.new(key.encode(), str(counter + i).encode(), "sha256"))

def truncate(hmac):
    digest = hmac.hexdigest()
    return format(int(digest[:2], 16), "03d")

def accept_code(code):
    if code in pool:
        remove_code(code)
        counter += 1
        return True
    return False

def remove_code(code):
    found = False
    for i in range(len(pool)):
        if code == pool[i]:
            found = True
        if found:
            if i+1 >= len(pool):
                pool[i] = None
            else:
                pool[i] = pool[i+1]

refresh_pool()
print(pool)
print(accept_code("167"))
print(pool)
