import os
import shutil
from glob import glob
from zipfile import ZipFile

from util import apktool
from .axml import ManifestXml
from .smaliparser import SmaliParser


class ApkFile:
    def __init__(self, file: str):
        self.file = file
        self.output = f'{self.file}.out'

    def decode(self, no_res=True):
        apktool.decode(self.file, self.output, no_res)

    def build(self, copy_original=True):
        apktool.build(self.output, copy_original)
        apktool.zipalign(f'{self.output}/dist/{os.path.basename(self.file)}', self.file)
        shutil.rmtree(self.output)

    def open_smali(self, file: str):
        for dir_name in os.listdir(self.output):
            if dir_name.startswith('smali'):
                assumed_path = f'{self.output}/{dir_name}/{file}'
                if os.path.exists(assumed_path):
                    return SmaliParser(assumed_path).smali_file

    def find_smali(self, *keywords: str):
        results = []
        # See: https://docs.python.org/3/using/windows.html#removing-the-max-path-limitation
        for file in glob(f'{self.output}/smali*/**/*.smali', recursive=True):
            keyword_set = set(keywords)
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    for keyword in keywords:
                        if keyword in line:
                            keyword_set.discard(keyword)
            if len(keyword_set) == 0:
                results.append(SmaliParser(file).smali_file)
        return results

    def get_version_code(self):
        with ZipFile(self.file, 'r') as zip_file:
            f = zip_file.open('AndroidManifest.xml', 'r')
            return ManifestXml(f.read()).attributes['android:versionCode']
