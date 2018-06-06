#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

__appname__     = "lib"
__author__      = "Marco Sirabella"
__copyright__   = ""
__credits__     = ["Marco Sirabella"]  # Authors and bug reporters
__license__     = "GPL"
__version__     = "1.0"
__maintainers__ = "Marco Sirabella"
__email__       = "marco@sirabella.org"
__status__      = "Prototype"  # "Prototype", "Development" or "Production"
__module__      = ""


class Counter():
    def __init__(self, filename, start=None):
        self.filename = filename
        with open(self.filename, "w+"):
            pass  # create file just in case

        with open(self.filename, 'r') as file:
            isempty = len(file.read()) == 0

        print('isempty', isempty)
        if isempty:
            if start is None:
                start = -1
            self.__set__(None, start)
        else:
            self.__get__()  # test out is integer

    def __call__(self):
        num = self.__get__(None)
        num += 1
        self.__set__(None, num)
        return num

    def __get__(self, obj, _type=None):
        with open(self.filename, 'r') as file:
            return int(file.read())

    def __set__(self, obj, value):
        assert isinstance(value, int), (value, type(value))
        with open(self.filename, 'w') as file:
            file.write(str(value))

    def __delete__(self, obj):
        raise AttributeError("can't delete attribute")
