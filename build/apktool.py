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
    def decode(file: str, output_dir: str, need_res: bool):
        resource_param = '-r' if not need_res else ''
        os.system('java -jar {lib_dir}/apktool.jar d {file} -o {output_dir} {resource_param}'
                  .format(lib_dir=LIB_DIR, file=file, output_dir=output_dir, resource_param=resource_param))

    @staticmethod
    def build(output_dir: str):
        os.system('java -jar %s/apktool.jar b %s' % (LIB_DIR, output_dir))

    @staticmethod
    def sign(file: str):
        old_file = file + '.old'
        os.rename(file, old_file)

        java_path = os.path.join(os.getenv('JAVA_HOME'), 'bin', 'java.exe')
        security_dir = os.path.join(LIB_DIR, 'security')
        os.system('{java} -jar {lib_dir}/signapk.jar {security_dir}/platform.x509.pem {security_dir}/platform.pk8 {src} {dst}'
                  .format(java=java_path, lib_dir=LIB_DIR, security_dir=security_dir, src=old_file, dst=file))

        os.remove(old_file)
