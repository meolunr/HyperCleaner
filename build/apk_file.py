import glob
import os

from util import ApkUtils
from .smali_parser import SmaliParser


class ApkFile(object):
    def __init__(self, file: str):
        self.__path = os.path.abspath(file)
        self.__output_dir = None

    def decode(self, need_res: bool = False):
        self.__output_dir = os.path.splitext(self.__path)[0]
        ApkUtils.decode(self.__path, self.__output_dir, need_res)

    def build(self, sign=False):
        output_file = os.path.join(self.__output_dir, 'dist', os.path.basename(self.__path))
        if sign:
            ApkUtils.build(self.__output_dir)
            ApkUtils.sign(output_file)
        else:
            ApkUtils.build(self.__output_dir, True)
        ApkUtils.zipalign(output_file)
        return output_file

    def open_smali(self, file: str):
        for dir_name in os.listdir(self.__output_dir):
            if dir_name.startswith('smali'):
                assumed_path = os.path.join(self.__output_dir, dir_name, file)
                if os.path.exists(assumed_path):
                    return SmaliParser(assumed_path).make()

    def find_smali(self, *keywords: str):
        files = glob.glob(os.path.join(self.__output_dir, r'smali*/**/*.smali'), recursive=True)
        for file in files:
            keywordSet = set(keywords)
            for line in open(file, mode='r'):
                for keyword in keywords:
                    if keyword in line:
                        keywordSet.discard(keyword)
            if len(keywordSet) == 0:
                return SmaliParser(file).make()
