import os
from glob import glob

from smaliparser import SmaliParser
from util import apktool


class ApkFile(object):
    def __init__(self, file: str):
        self.file = file
        self.output = f'{self.file}.out'

    def decode(self, no_res=True):
        apktool.decode(self.file, self.output, no_res)

    def build(self, copy_original=True):
        apktool.build(self.output, copy_original)
        apktool.zipalign(f'{self.output}/dist/{os.path.basename(self.file)}', self.file)

    def open_smali(self, file: str):
        for dir_name in os.listdir(self.output):
            if dir_name.startswith('smali'):
                assumed_path = os.path.join(self.output, dir_name, file)
                if os.path.exists(assumed_path):
                    return SmaliParser(assumed_path).smali_file

    def find_smali(self, *keywords: str):
        for file in glob(f'{self.output}/smali*/**/*.smali', recursive=True):
            keyword_set = set(keywords)
            for line in open(file, 'r'):
                for keyword in keywords:
                    if keyword in line:
                        keyword_set.discard(keyword)
            if len(keyword_set) == 0:
                return SmaliParser(file).smali_file
