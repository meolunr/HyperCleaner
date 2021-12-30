import os

from build.apktool import ApkTool


class ApkFile(object):

    def __init__(self, file: str):
        self.name = file
        self.output_dir = None

    def decode(self, need_res=False):
        self.output_dir = os.path.splitext(self.name)[0]
        ApkTool.decode(self.name, self.output_dir, need_res)

    def build(self):
        output_file = os.path.join(self.output_dir, 'dist', self.name)
        ApkTool.build(self.output_dir)
        ApkTool.sign(output_file)
        return output_file
