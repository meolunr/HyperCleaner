import re

from .method_specifier import MethodSpecifier
from .smali_file import SmaliFile


class SmaliParser(object):

    def __init__(self, path: str):
        self.__smali_file = SmaliFile(path)
        with open(path, mode='r') as file:
            self.__parse_method(file.read())

    def __parse_method(self, content: str):
        pattern = re.compile(r'((\.method.+?)\n.+?\.end method)', re.DOTALL)
        method_pattern = re.compile(r'\.method (public|protected|private)(?: static)? (\w+?)\((\S*?)\)(\S+?)')

        for item in pattern.findall(content):
            method_defines = method_pattern.findall(item[1])
            if len(method_defines) == 0:
                continue
            method_defines = method_defines[0]

            specifier = MethodSpecifier()
            specifier.access = MethodSpecifier.Access(method_defines[0])
            specifier.is_static = ' static ' in item[1]
            specifier.name = method_defines[1]
            specifier.parameters = method_defines[2]
            specifier.return_type = method_defines[3]

            self.__smali_file.add_method(specifier, item[0])

    def make(self):
        return self.__smali_file
