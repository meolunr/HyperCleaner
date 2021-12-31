import os

from build.apktool import ApkTool
from build.smali_parser import SmaliParser


class ApkFile(object):

    def __init__(self, file: str):
        self.__path = os.path.abspath(file)
        self.__output_dir = None

    def decode(self, need_res=False):
        self.__output_dir = os.path.splitext(self.__path)[0]
        # ApkTool.decode(self.__path, self.__output_dir, need_res)

    def build(self):
        output_file = os.path.join(self.__output_dir, 'dist', os.path.basename(self.__path))
        ApkTool.build(self.__output_dir)
        ApkTool.sign(output_file)
        return output_file

    def open_smali(self, file: str):
        for dir_name in os.listdir(self.__output_dir):
            if dir_name.startswith('smali'):
                assumed_path = os.path.join(self.__output_dir, dir_name, file)
                if os.path.exists(assumed_path):
                    SmaliParser(assumed_path)
