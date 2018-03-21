#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

import machine
import time
import hmac
import _sha256

class Keypad():
    buttons = (('1', '2', '3'),
               ('4', '5', '6'),
               ('7', '8', '9'),
               ('*', '0', '#'))

    def __init__(self, col_pins, row_pins):
        self.cols = [machine.Pin(i, machine.Pin.OUT) for i in col_pins]
        self.rows = [machine.Pin(i, machine.Pin.IN) for i in row_pins]

    @property
    def pressed(self):
        for i, col in enumerate(self.cols):
            col.value(1)
            for j, row in enumerate(self.rows):
                if row.value() == 1:
                    col.value(0)
                    return self.buttons[j][i]
            col.value(0)
        return None

    def get_next_pressed(self):
        val = self.pressed 
        while not val:
            val = self.pressed
        val2 = val 
        while val:
            val = self.pressed
            if val:
                val2 = val
        return val2 
        
    def get_input_message(self):
        message = ""
        button = self.get_next_pressed()
        while not button == '#':
            message += button
            button = self.get_next_pressed()
        return message

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
#while True:
    #handle_code(get_pressed())
    #time.sleep(0.1)
