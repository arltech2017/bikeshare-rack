#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

import machine
import time

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
    if not code == -1: 
        if accept_input:
            accept_input = False 
            if code == "#":
                result = stored_code
                stored_code = ""
                print(result)
            else:
                stored_code += str(code) 
    else:
        accept_input = True
 

while True:
    handle_code(get_pressed())
    time.sleep(0.1)
