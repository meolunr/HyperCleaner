import os
import shutil
from glob import glob
from zipfile import ZipFile

from util import apktool, apkeditor
from .axml import ManifestXml
from .smali import SmaliFile
from .xml import XmlFile


class ApkFile:
    def __init__(self, file: str):
        self.file = file
        self.output = f'{self.file}.out'
        self._use_apk_editor = False
        self._manifest_attributes = None

    def decode(self, no_res=True):
        self._use_apk_editor = not no_res
        if self._use_apk_editor:
            apkeditor.decode(self.file, self.output)
        else:
            apktool.decode(self.file, self.output, no_res)

    def build(self, copy_original=True):
        if self._use_apk_editor:
            apkeditor.build(self.output, self.file)
        else:
            apktool.build(self.output, copy_original)
            apktool.zipalign(f'{self.output}/dist/{os.path.basename(self.file)}', self.file)
        shutil.rmtree(self.output)

    def refactor(self):
        old_file = f'{self.file}.old'
        os.rename(self.file, old_file)
        apkeditor.refactor(old_file, self.file)
        os.remove(old_file)

    def open_smali(self, file: str):
        if self._use_apk_editor:
            dirs = set(map(lambda x: f'smali/{x}', os.listdir(f'{self.output}/smali')))
        else:
            dirs = set(filter(lambda x: x.startswith('smali'), os.listdir(self.output)))
        for dir_name in dirs:
            assumed_path = f'{self.output}/{dir_name}/{file}'
            if os.path.exists(assumed_path):
                return SmaliFile(assumed_path)

    def find_smali(self, *keywords: str):
        results = set()
        # See: https://docs.python.org/3/using/windows.html#removing-the-max-path-limitation
        for file in glob(f'{self.output}/smali*/**/*.smali', recursive=True):
            keyword_set = set(keywords)
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    for keyword in keywords:
                        if keyword in line:
                            keyword_set.discard(keyword)
            if len(keyword_set) == 0:
                results.add(SmaliFile(file))
        return results

    def open_xml(self, file: str):
        return XmlFile(f'{self.output}/resources/package_1/res/{file}')

    def version_code(self):
        if not self._manifest_attributes:
            self._parse_manifest()
        return self._manifest_attributes['android:versionCode']

    def extract_native_libs(self) -> bool | None:
        if not self._manifest_attributes:
            self._parse_manifest()
        attribute_map: dict = self._manifest_attributes['application']
        return attribute_map.get('android:extractNativeLibs', None)

    def _parse_manifest(self):
        with ZipFile(self.file, 'r') as zip_file:
            f = zip_file.open('AndroidManifest.xml', 'r')
            self._manifest_attributes = ManifestXml(f.read()).attributes
