import os
from glob import glob

from util2 import apktool


class ApkFile(object):
    def __init__(self, file: str):
        self.file = file

    def decode(self, no_res=True):
        apktool.decode(self.file, f'{self.file}.out', no_res)

    def build(self, copy_original=True):
        apktool.build(f'{self.file}.out', copy_original)
        apktool.zipalign(f'{self.file}.out/dist/{os.path.basename(self.file)}', self.file)

    def open_smali(self, file: str):
        for dir_name in os.listdir(self._output):
            if dir_name.startswith('smali'):
                assumed_path = os.path.join(self._output, dir_name, file)
                if os.path.exists(assumed_path):
                    pass
                    # return SmaliParser(assumed_path).make()

    def find_smali(self, *keywords: str):
        for file in glob(f'{self.file}.out/smali*/**/*.smali', recursive=True):
            keyword_set = set(keywords)
            for line in open(file, mode='r'):
                for keyword in keywords:
                    if keyword in line:
                        keyword_set.discard(keyword)
            if len(keyword_set) == 0:
                pass
                # return SmaliParser(file).make()
