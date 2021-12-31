from enum import Enum


class SmaliFile(object):
    class AccessSpecifier(Enum):
        public = 0
        protected = 1

    def __init__(self, file: str):
        self.__path = file
        self.__methods = []
        self.__method_body = {}

    def add_method(self, method_name, method_body):
        print('-------- ' + method_name + ' --------')
        print(method_body)
