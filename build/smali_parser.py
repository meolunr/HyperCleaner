import re

from build.smali_file import SmaliFile


class SmaliParser(object):

    def __init__(self, path: str):
        self.__smali_file = SmaliFile(path)
        with open(path, mode='r') as file:
            self.__parse_method(file.read())

    def __parse_method(self, content: str):
        pattern = re.compile(r'((\.method.+?)\n.+?\.end method)', re.DOTALL)
        method_pattern = re.compile(r'\.method (public|private|protected)(?: static)? (\w+?)\((\S+?)\)(\S+?)')

        for item in pattern.findall(content):
            method_specifiers = method_pattern.findall(item[1])
            if len(method_specifiers) == 0:
                continue
            method_specifiers = method_specifiers[0]

            method = SmaliFile.Method()
            method.access_specifier = method_specifiers[0]
            method.is_static = ' static ' in item[1]
            method.name = method_specifiers[1]
            method.parameters = method_specifiers[2]
            method.return_type = method_specifiers[3]

            self.__smali_file.add_method(method, item[0])

    def make(self):
        return self.__smali_file
