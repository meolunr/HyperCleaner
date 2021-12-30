import os

from build.apktool import ApkTool


class ApkFile(object):

    def __init__(self, path: str):
        self.path = path
        self.output_dir = None

    def decode(self, need_res=False):
        self.output_dir = os.path.splitext(self.path)[0]
        ApkTool.decode(self.path, self.output_dir, need_res)

    def build(self):
        ApkTool.build(self.output_dir)
