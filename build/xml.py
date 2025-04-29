import xml.etree.ElementTree as eTree
from xml.etree.ElementTree import Element

_NAMESPACES = {
    'android': 'http://schemas.android.com/apk/res/android',
    'app': 'http://schemas.android.com/apk/res-auto'
}


class XmlFile:
    def __init__(self, file: str):
        for k, v in _NAMESPACES.items():
            eTree.register_namespace(k, v)

        self.file = file
        self._tree = eTree.parse(file)

    def get_root(self) -> Element:
        return self._tree.getroot()

    def commit(self):
        self._tree.write(self.file, 'utf-8')

    @staticmethod
    def make_attr_key(key: str):
        splits = key.split(':')
        for k, v in _NAMESPACES.items():
            if k == splits[0]:
                return f'{{{v}}}{splits[1]}'
        return None
