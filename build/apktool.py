import os
import shutil
import sys


class ApkTool(object):

    def __init__(self):
        self.lib_dir = os.path.join(sys.path[0], 'lib')

    def install_framework(self, file: str):
        os.system('java -jar %s/apktool.jar if %s' % (self.lib_dir, file))

    def uninstall_framework(self):
        apktool_framework_path = os.path.join(os.getenv('LOCALAPPDATA'), 'apktool/framework')
        shutil.rmtree(apktool_framework_path)
        os.makedirs(apktool_framework_path)
