from build.apktool import ApkTool


class ApkFile(object):

    def __init__(self, path: str):
        self.path = path

    def decode(self, need_res=False):
        ApkTool.decode(self.path, need_res)
