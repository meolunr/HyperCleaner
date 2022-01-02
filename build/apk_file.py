import os

from build import SmaliParser
from util import ApkUtils


class ApkFile(object):
    def __init__(self, file: str):
        self.__path = os.path.abspath(file)
        self.__output_dir = None

    def decode(self, need_res: bool = False):
        self.__output_dir = os.path.splitext(self.__path)[0]
        ApkUtils.decode(self.__path, self.__output_dir, need_res)

    def build(self):
        output_file = os.path.join(self.__output_dir, 'dist', os.path.basename(self.__path))
        ApkUtils.build(self.__output_dir)
        ApkUtils.sign(output_file)
        return output_file

    def open_smali(self, file: str):
        for dir_name in os.listdir(self.__output_dir):
            if dir_name.startswith('smali'):
                assumed_path = os.path.join(self.__output_dir, dir_name, file)
                if os.path.exists(assumed_path):
                    return SmaliParser(assumed_path).make()
