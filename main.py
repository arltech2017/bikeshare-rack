#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

# TODO: Finish implementing the Counter class in the rest of the code
# TODO: Implement multitasking so that multiple bikes can be unlocked at once

import machine
import time
import hmac

# The hmac library's sha256 is broken, so use our version,
# downloaded from the micropython repo
import _sha256 as sha256


class Keypad():
    """
    An interface between the code and the matrix membrane keypad attached to
    the arduino. Able to read input from the keypad.
    """

    # The order of the keys as they show up on the keypad, used for determining
    # the key value of a specific row/column location.
    buttons = (('1', '2', '3'),
               ('4', '5', '6'),
               ('7', '8', '9'),
               ('*', '0', '#'))

    def __init__(self, col_pins, row_pins):
        """
        Accepts the esp pins for columns and rows, increasing along with the
        buttons tuples. Set column pins to output and row pins to input.
        """

        self.cols = [machine.Pin(i, machine.Pin.OUT) for i in col_pins]
        self.rows = [machine.Pin(i, machine.Pin.IN) for i in row_pins]

    @property
    def pressed(self):
        """
        Returns true if any of the keys on the keypad is pressed.  For each
        column pin, output a signal. If a row pin is receiving a signal, the
        key at the row/column intersection is being pressed, and the
        corresponding string in 'buttons' is returned. If no key is pressed,
        return None.
        """

        for i, col in enumerate(self.cols):
            col.value(1)
            for j, row in enumerate(self.rows):
                if row.value() == 1:
                    col.value(0)
                    return self.buttons[j][i]
            col.value(0)
        return None

    def get_next_pressed(self):
        """
        Returns the most recently pressed key on the keypad. The first while
        loop waits until a key is being pressed, and then the second while loop
        waits until the key is released to return.
        """

        # Make sure val is the most recently pressed key that is not None
        val = self.pressed
        while not val:
            val = self.pressed

        val2 = val

        # Sets val2 to the most recently pressed key until no key is being
        # pressed (val == None)
        while val:
            val = self.pressed  # get current pressed key

            if val:
                val2 = val  # sets val2 to the most recent key pressed

        return val2  # return most recently pressed key

    def get_input_message(self):
        """
        Stores a list of the keys pressed as a string. Keeps recording key
        presses until it finds the escape character, '#', and then return
        the message.
        """

        message = ""
        button = self.get_next_pressed()
        while not button == '#':
            message += button
            button = self.get_next_pressed()
        return message


class Key():
    """
    Represents a hashed code able to unlock a bike. 12 subcodes are stored,
    each one linked to a bike number, any of which can be used to unlock
    a specific bike.
    """

    def __init__(self, key, n):
        """
        Initializes 'keys' a list of 12 codes, one for each bike. With 'key'
        being the initial hash code, each code is 'key' + hash('key' + 'bike
        number').  'invaltime' is the timestamp that the key became invalidated
        (when the key is skipped, see invalidate_codes() in Pool), or None if
        the key is valid.  'n' is the value of the counter that this key was
        generated with. This is used to compare keys, to see which one came
        first. This is useful when invaliding and removing unused keys.
        """

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
                s += 'I'
            s += self.keys[i]
            if i+1 < len(self.keys):
                s += ', '
        s += ']'
        return s


class HOTP():
    """
    An HOTP encryption class, follows the standard guidelines. Use at() to get
    an encrypted message.
    """

    # The number of digits the returned code will be
    codelen = 3

    def __init__(self, secret, hash_func=sha256.sha256):
        """
        Pass this a secret and a hash function. The function should be sha256
        """
        self.secret = secret
        self.hash_func = hash_func

    def at(self, counter):
        """
        Pass a message ('counter') and it returns the HOTP encrypted form, with
        the hex form truncated as according to truncate()
        """
        return self.truncate(
            hmac.new(
                self.secret.encode(),
                str(counter).encode(),
                self.hash_func
            ).hexdigest())

    def truncate(self, hashstr):
        """
        Takes a hexdigest from at(), turns it into an integer, and returns the
        first number of digits specified by 'self.codelen'
        """
        return format(int(hashstr, 16) % (10 ** self.codelen),
                      '0{}d'.format(self.codelen))


def format(i, args):
    """
    Helper method to replace String's format() because it's not supported in
    micropython. Accepts an object 'i' and formats according to arguments
    'args' as normal format() would do.
    """
    argstr = '{:' + args + '}'
    return argstr.format(i)


class Pool():
    """
    A pool of key objects.  Used as backup in case someone requests a code but
    never uses it. Should someone request a code, it would be used up on the
    server side. If the code is never entered into the bike rack, it would be
    forever looking for that code, even when other codes are being distributed
    by the server. A pool of available codes is the solution.
    """
    def __init__(self, size, encryption, counter, inval_time_limit):
        """
        Accepts three arguments:
            -the size of the pool
            -the class used to encrypt the counter, should be HOTP()
            -the length of time after which an invalid code will be removed

        Initially fills up the pool
        """
        self.pool = [None] * size
        self.encryption = encryption
        self.counter = counter
        self.inval_time_limit = inval_time_limit
        self.repopulate()

    def repopulate(self):
        """
        For each None value in the pool, generate a new key according to the
        value of 'counter' and increment the counter. Return the counter so
        that the counter object can be updated.
        """
        for i in range(len(self.pool)):
            if not self.pool[i]:
                key = self.encryption.at(self.counter)
                self.pool[i] = Key(key, self.counter)
                self.counter += 1
        print("Done repopulating pool")
        return self.counter

    def remove_key(self, key):
        """
        Removes the given key from the pool if discovered, and shifts all items
        after it to the left. Successfully removing a key will leave a None
        value at the end of the list, so repopulate() will be needed.
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
        """
        Invalidates any key whose n value is less than 'n', that is, any key
        that was created before the counter reached 'n'. This should be called
        whenever a key is accepted (because any keys before the accepted key
        will never be used).  Invalidates the keys by setting their 'invaltime'
        to the current time.
        """
        for i in range(len(self.pool)):
            key = self.pool[i]
            if key and key.invaltime is None and key.n < n:
                key.invaltime = time.time()

    def accept_code(self, code):
        """
        Checks to see if 'code' is in the pool.  Iterates through the subkeys
        in each key and returns the subkey index (the bike number) if found.
        Currently when a key is found, this function removes it from the pool,
        removes invalidated codes, invalidates any codes before the accepted
        key, and then reopulates the pool, all before returning the bike index.
        This means there's a significant time gap as the microcontroller
        generates a new key, and should be fixed.
        """
        for i in range(len(self.pool)):
            key = self.pool[i]
            if key:
                for j in range(len(key.keys)):
                    if code == key.keys[j]:
                        self.remove_key(key)
                        self.remove_inval_codes()
                        self.invalidate_codes(key.n)
                        # update counter here
                        self.counter = self.repopulate()
                        return j

        return None

    def remove_inval_codes(self):
        """
        Removes any key that has been invalidated for greater than the time
        limit, as designated by 'self.inval_time_limit'
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
    """
    A class for storing the 'counter' int, which is incremented and used to
    generate the passcodes. Reads and writes to a file on the microcontroller
    to survive reboot.
    """

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
    """
    An interface for the relay, which physically unlocks the bikes on the rack.
    As of currently, no new code can be accepted while a bike is unlocked,
    meaning only one bike can be unlocked at the same time. This needs to
    change.
    """

    unlocktime = 5  # How many seconds the bikes are unlocked for

    def __init__(self, pins):
        """
        Sets up the pins connected to the relay as output, as passed by 'pins'.
        HIGH is closed, so output a signal for all pins.
        """
        self.pins = [machine.Pin(i, machine.Pin.OUT) for i in pins]
        for pin in self.pins:
            pin.value(1)

    def unlock_bike(self, bike_num):
        """
        Unlocks the bike of 'bike_num', which corresponds to 'self.pins' index
        """
        self.pins[bike_num].value(0)
        time.sleep(self.unlocktime)
        self.pins[bike_num].value(1)


# Turn ESP32 blue light on for dev testing
pin2 = machine.Pin(2, machine.Pin.OUT)
pin2.value(1)

kp = Keypad((21, 22, 23), (16, 17, 18, 19))
hotp = HOTP("ITSAKEY", sha256.sha256)
# Set counter to 10 initially because calling Pool() initializes the first 10
# keys
counter = 0

# set invalid time limit to an hour (3600 seconds)
pool = Pool(10, hotp, counter, 3600)
print(pool)
relay = Relay((4, 0, 15, 10, 9, 13, 14, 27, 26, 25, 33, 32))

# Turn ESP32 blue light off to signify setup completion
pin2.value(0)

# Main loop, continually tries to accept input from the keypad, and unlocks the
# bike if the input is accepted as a code.
while True:
    result = pool.accept_code(kp.get_input_message())
    print(result)
    if result is not None:
        relay.unlock_bike(result)
        print(pool)
