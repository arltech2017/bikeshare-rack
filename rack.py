import hmac
import time

class Key():
    def __init__(self, key, n):
        self.n = n 
        self.key = key
        self.invaltime = None

    def __str__(self):
        return self.key

def print_pool(l):
    print("[", end='')
    for i in range(len(l)):
        print(str(l[i]), end='')
        if i < len(l) - 1:
            print(', ', end='')
    print(']')

def print_time(l):
    print("[", end='')
    for i in range(len(l)):
        if l[i]:
            print(l[i].invaltime, end='')
        else:
            print("None", end='')

        if i < len(l) - 1:
            print(', ', end='')
    print(']')

counter = 0
secret = "ITSAKEY"

pool = [None] * 10
invallimit = 2 

def refresh_pool():
    global counter
    for i in range(len(pool)):
        if not pool[i]:
            key = truncate(hmac.new(secret.encode(), str(counter).encode(), "sha256"))
            pool[i] = Key(key, counter)
            counter += 1

def truncate(hmac):
    digest = hmac.hexdigest()
    return format(int(digest[:2], 16), "03d")

def accept_code(code):
    for i in range(len(pool)):
        if pool[i] and pool[i].key == code:
            remove_code(code)
            invalidate_codes(pool[i].n)
            remove_inval_codes()
            refresh_pool()
            #counter += 1
            return True
    remove_inval_codes()
    refresh_pool()
    return False

def invalidate_codes(n):
    for i in range(len(pool)):
        if pool[i] and pool[i].invaltime == None and pool[i].n < n:
            pool[i].invaltime = time.time()
    
def remove_inval_codes():
    i = 0
    while i < len(pool):
        if pool[i] and not pool[i].invaltime == None:
            diff = time.time() - pool[i].invaltime
            if diff >= invallimit:
                remove_code(pool[i].key)
            else:
                i += 1
        else:
            i += 1


def remove_code(code):
    found = False
    for i in range(len(pool)):
        if pool[i] and code == pool[i].key:
            found = True
        if found:
            if i+1 >= len(pool):
                pool[i] = None
            else:
                pool[i] = pool[i+1]

refresh_pool()
print_pool(pool)

print_time(pool)
print(accept_code("167"))
print_pool(pool)
print_time(pool)
time.sleep(3)
print(accept_code("145"))
print_pool(pool)
print_time(pool)

