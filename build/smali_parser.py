import re

from build.smali_file import SmaliFile


class SmaliParser(object):

    def __init__(self, path: str):
        self.smali_file = SmaliFile(path)

        content = open(path, mode='r').read()
        self.__parse_method(content)

    def __parse_method(self, content: str):
        pattern = re.compile(r'((\.method.+?)\n.+?\.end method)', re.DOTALL)
        for item in pattern.findall(content):
            self.smali_file.add_method(item[1], item[0])
