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


class Key():
    def __init__(self, key, n):
        self.n = n
        self.key = key
        self.invaltime = None


class HOTP():
    def __init__(self, secret, hash_func):
        self.secret = secret
        self.hash_func = hash_func

    def at(self, counter):
        return self.truncate(
            hmac.new(
                self.secret.encode(),
                str(counter).encode(),
                self.hash_func
            ).hexdigest())

    def truncate(self, hash_obj):
        #digest = hash_obj.hexdigest()
        return format(int(hash_obj, 16) % 10, '03d')


def format(i, args):
    argstr = '{:' + args + '}'
    return argstr.format(i)


class Pool():
    def __init__(self, size, encryption, inval_time_limit):
        """Accepts three arguments:
            -the size of the pool
            -the class used to encrypt the counter, should be HOTP() 
            -the length of time after which an invalid code will be removed

        Initially fills up the pool
        """
        self.pool = [None] * size
        self.encryption = encryption 
        self.inval_time_limit = inval_time_limit
        self.repopulate(0)

    def repopulate(self, counter):
        """
        Iterates through the pool and for every None value, replaces it with a new
        key and increments the counter
        Since counter is being passed to it, returns the updated counter. The code
        calling this function should set its counter to the return value of this
        function
        """
        for i in range(len(self.pool)):
            if not self.pool[i]:
                key = self.encryption.at(counter) 
                self.pool[i] = Key(key, counter)
                counter += 1
        print("Done repopulating pool")
        return counter

    def remove_code(self, code):
        """
        Removes a key from the pool and shifts the other keys to the left to fill
        its gap and maintain an ordered list
        """
        found = False
        for i in range(len(self.pool)):
            if self.pool[i] and code == self.pool[i].key:
                found = True
            if found:
                if i + 1 >= len(self.pool):
                    self.pool[i] = None
                else:
                    self.pool[i] = self.pool[i + 1]



def accept_code(pool, code):
    """
    Takes a string and returns whether the string is in the pool as a key. If
    the code is found, remove it from the pool and mark any previous codes as
    invalid.
    Whether or not the code is found, remove any code that has been invalid for
    too long and then refresh the pool with new codes.
    """

    global counter #Not needed here, but a reminder that counter will need to be updated after this method

    found = False

    for i in range(len(pool)):
        if pool[i] and pool[i].key == code:
            pool.remove_code(code)
            invalidate_codes(pool[i].n)
            found = True

    remove_inval_codes()
    counter = pool.repopulate() #update counter here
    return found


def invalidate_codes(pool, n):
    """
    Accepts a key number, presumably of a code that was just used, and marks
    any key with a lower number as invalid by setting its invalidated time
    """
    for i in range(len(pool)):
        if pool[i] and pool[i].invaltime is None and pool[i].n < n:
            pool[i].invaltime = time.time()


def remove_inval_codes(pool):
    """
    Removes any code that has been invalid for too long (that is, longer than
    global invallimit)
    """
    i = 0
    while i < len(pool):
        if pool[i] and pool[i].invaltime:
            diff = time.time() - pool[i].invaltime
            if diff >= pool.inval_time_limit:
                pool.remove_code(pool[i].key)
            else:
                i += 1
        else:
            i += 1

kp = Keypad((21, 22, 23), (16, 17, 18, 19))
hotp = HOTP("ITSAKEY", _sha256.sha256)
pool = Pool(10, hotp, 3600)
counter = 10 #Set counter to 10 initially because calling Pool() initializes the first 10 keys

while True:
    accept_code(kp.get_input_message())
    time.sleep(0.1)
