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
    keypad = [['1', '2', '3'],
              ['4', '5', '6'],
              ['7', '8', '9'],
              ['*', '0', '#']]

    return keypad[row][col]

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

class Keypad():
    def __init__(self, col_pins, row_pins):
        self.cols = [machine.Pin(i, machine.Pin.OUT) for i in col_pins]
        self.rows = [machine.Pin(i, machine.Pin.IN) for i row_pins]
        self.stored_code = ""
        self.accept_input = True

    def get_pressed(self):
        for i, col in enumerate(self.cols):
            col.value(1)
            for j, row in enumerate(self.rows):
                if row.value() == 1:
                    col.value(0)
                    return get_code(i, j)
            col.value(0)
        return -1

    def get_code(self, col, row):
        vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, "*", 0, "#"]
        index = cols + (row * 3)
        return vals[index]

counter = 0
secret = "ITSAKEY"

pool = [None] * 10
invallimit = 2

class Key():
    def __init__(self, key, n):
        self.n = n
        self.key = key
        self.invaltime = None


#Iterates through the pool and for every None value, replaces it with a new key and increments the counter
def refresh_pool():
    global counter

    for i in range(len(pool)):
        if not pool[i]:
            key = truncate(hmac.new(secret.encode(), str(counter).encode(), _sha256.sha256))
            pool[i] = Key(key, counter)
            counter += 1
    print("done")

def format(i, args):
    argstr = '{:' + args + "}"
    return argstr.format(i)

#Takes a hash object, such as Sha256, and returns the first two bytes of its hex value, formated to be a three digit string
def truncate(hashobj):
    digest = hashobj.hexdigest()
    return format(int(digest[:2], 16), '03d')

#Takes a string and returns whether the string is in the pool as a key. If the code is found, remove it from the pool and mark any previous codes as invalid.
#Whether or not the code is found, remove any code that has been invalid for too long and then refresh the pool with new codes.
def accept_code(code):
    found = False

    for i in range(len(pool)):
        if pool[i] and pool[i].key == code:
            remove_code(code)
            invalidate_codes(pool[i].n)
            found = True

    remove_inval_codes()
    refresh_pool()
    return found

#Accepts a key number, presumably of a code that was just used, and marks any key with a lower number as invalid by setting its invalidated time
def invalidate_codes(n):
    for i in range(len(pool)):
        if pool[i] and pool[i].invaltime == None and pool[i].n < n:
            pool[i].invaltime = time.time()

#Removes any code that has been invalid for too long (that is, longer than global invallimit)
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

#Removes a key from the pool and shifts the other keys to the left to fill its gap and maintain an ordered list
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
