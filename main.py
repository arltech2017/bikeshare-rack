#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

import machine
import time
import hmac 
import _sha256 

cols = [machine.Pin(i, machine.Pin.OUT) for i in [21, 22, 23]]
rows = [machine.Pin(i, machine.Pin.IN) for i in [16 ,17, 18, 19]]

accept_input = True
stored_code = ""

def toggle(pin):
    value = pin.value()
    value ^= 1
    pin.value(value)

def get_pressed():
    for i, col in enumerate(cols):
        col.value(1)
        for j, row in enumerate(rows):
            if row.value() == 1:
                col.value(0)
                return get_code(i, j)
        col.value(0)
    return -1 

def get_code(col, row):
    if row < 3:
        return (col + 1) + (row * 3)
    else:
        if col == 0:
            return "*"
        elif col == 1:
            return 0
        else:
            return "#"

def handle_code(code):
    global accept_input
    global stored_code
    if not code == -1: 
        if accept_input:
            accept_input = False 
            if code == "#":
                result = stored_code
                stored_code = ""
                print(accept_code(result))
            else:
                stored_code += str(code) 
    else:
        accept_input = True
 

counter = 0
secret = "ITSAKEY"

pool = [None] * 10
invallimit = 2

class Key():
    def __init__(self, key, n):
        self.n = n
        self.key = key
        self.invaltime = None

def refresh_pool():
    global counter
    
    for i in range(len(pool)):
        if not pool[i]:
            key = truncate(hmac.new(secret.encode(), str(counter).encode(), _sha256.sha256))
            pool[i] = Key(key, counter)
            counter += 1
    print("done")

def truncate(hmac):
    digest = hmac.hexdigest()
    return '{:03d}'.format(int(digest[:2], 16))

def accept_code(code):
    for i in range(len(pool)):
        if pool[i] and pool[i].key == code:
            remove_code(code)
            invalidate_codes(pool[i].n)
            remove_inval_codes()
            refresh_pool()
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
        if pool[i] and pool[i].invaltime:
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
while True:
    handle_code(get_pressed()) 
    time.sleep(0.1)
