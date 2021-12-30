import os
import shutil
import sys

LIB_DIR = os.path.join(sys.path[0], 'lib')


class ApkTool(object):

    @staticmethod
    def install_framework(file: str):
        os.system('java -jar %s/apktool.jar if %s' % (LIB_DIR, file))

    @staticmethod
    def uninstall_framework():
        apktool_framework_path = os.path.join(os.getenv('LOCALAPPDATA'), 'apktool/framework')
        shutil.rmtree(apktool_framework_path)
        os.makedirs(apktool_framework_path)

    @staticmethod
    def decode(file: str, need_res: bool):
        folder = os.path.splitext(file)[0]
        resource_param = '-r' if not need_res else ''
        os.system('java -jar {lib_dir}/apktool.jar d {file} -o {folder} {resource_param}'
                  .format(lib_dir=LIB_DIR, file=file, folder=folder, resource_param=resource_param))
