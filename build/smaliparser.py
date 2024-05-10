import re

from .smali import MethodSpecifier
from .smali import SmaliFile


class SmaliParser(object):

    def __init__(self, file: str):
        self.smali_file = SmaliFile(file)
        with open(file, 'r', encoding='utf-8') as file:
            self._parse_method(file.read())

    def _parse_method(self, content: str):
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

            self.smali_file.add_method(specifier, item[0])
