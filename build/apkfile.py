import os

from build.apktool import ApkTool


class ApkFile(object):

    def __init__(self, file: str):
        self.__path = os.path.abspath(file)
        self.__output_dir = None

    def decode(self, need_res=False):
        self.__output_dir = os.path.splitext(self.__path)[0]
        ApkTool.decode(self.__path, self.__output_dir, need_res)

    def build(self):
        output_file = os.path.join(self.__output_dir, 'dist', os.path.basename(self.__path))
        ApkTool.build(self.__output_dir)
        ApkTool.sign(output_file)
        return output_file
