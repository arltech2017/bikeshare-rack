#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

#import machine
import time
import hmac
import _sha256 as sha256


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
        self.keys = [None] * 12
        for i in range(len(self.keys)):
            self.keys[i] = key + str(hotp.at(key + str(i)))
        self.invaltime = None
        print("key done")

    def __getitem__(self, i):
        return self.keys[i]

    def __contains__(self, code):
        return code in self.keys

    def __str__(self):
        s = '['
        for i in range(len(self.keys)):
            if self.invaltime:
                s+='I'
            s += self.keys[i]
            if i+1 < len(self.keys):
                s += ', '
        s += ']'
        return s


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

    def remove_key(self, key):
        """
        Removes a key from the pool and shifts the other keys to the left to fill
        its gap and maintain an ordered list
        """
        found = False
        for i in range(len(self.pool)):
            if self.pool[i] and self.pool[i].keys is key.keys:
                found = True
            if found:
                if i + 1 >= len(self.pool):
                    self.pool[i] = None
                else:
                    self.pool[i] = self.pool[i + 1]

    def invalidate_codes(self, n):
        for i in range(len(self.pool)):
            key = self.pool[i]
            if key and key.invaltime is None and key.n < n:
                key.invaltime = time.time()


    def accept_code(self, code):
        """
        Takes a string and returns whether the string is in the pool as a key. If
        the code is found, remove it from the pool and mark any previous codes as
        invalid.
        Whether or not the code is found, remove any code that has been invalid for
        too long and then refresh the pool with new codes.
        """

        global counter #Not needed here, but a reminder that counter will need to be updated after this method

        for i in range(len(self.pool)):
            key = self.pool[i]
            if key:
                for j in range(len(key.keys)):
                    if code == key.keys[j]:
                        self.remove_key(key)
                        self.remove_inval_codes()
                        self.invalidate_codes(key.n)
                        counter = self.repopulate(counter) #update counter here
                        return j

        return None

    def remove_inval_codes(self):
        """
        Removes any code that has been invalid for too long (that is, longer than
        global invallimit)
        Uses while() instead of for() because once a code is removed, everything shifts over an
        index, so you want to check that index again.
        """

        i = 0
        while i < len(pool):
            found = False
            key = self.pool[i]
            if key and key.invaltime:
                diff = time.time() - key.invaltime
                if diff >= self.inval_time_limit:
                    self.remove_key(key)
                    found = True
            if not found:
                i += 1

    def __len__(self):
        return len(self.pool)

    def __getitem__(self, index):
        return self.pool[index]

    def __str__(self):
        s = "["
        for i in range(len(self.pool)):
            s += str(self.pool[i])
            if not i+1 == len(self.pool):
                s += ", "
        s += "]"
        return s


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

class Relay():
    def __init__(self, pins):
        self.pins = [machine.Pin(i, machine.Pin.OUT) for i in pins]
        for pin in self.pins:
            pin.value(1)

    def unlock_bike(self, bike_num):
        self.pins[bike_num].value(0)
        time.sleep(5)
        self.pins[bike_num].value(1)

#pin2 = machine.Pin(2, machine.Pin.OUT)
#pin2.value(1)
#kp = Keypad((21, 22, 23), (16, 17, 18, 19))
hotp = HOTP("ITSAKEY", sha256.sha256)
pool = Pool(15, hotp, 3600) #set invalid time to an hour (3600 seconds)
counter = 10 #Set counter to 10 initially because calling Pool() initializes the first 10 keys
#relay = Relay((4, 0, 15, 10, 9, 13, 12, 14, 27, 26, 25, 33, 32))

#pin2.value(0)
print(pool)

"""
while True:
    result = pool.accept_code(kp.get_input_message())
    print(result)
    if result is not None:
        relay.unlock_bike(result)
        """
