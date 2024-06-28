import os.path
import subprocess

from hcglobal import LIB_DIR


def decode(file: str, output: str):
    subprocess.run(f'java -jar {LIB_DIR}/APKEditor.jar d -i {file} -o {output}')


def build(dir_path: str):
    apk_name = os.path.basename(dir_path)[:-4]
    subprocess.run(f'java -jar {LIB_DIR}/APKEditor.jar b -i {dir_path} -o {dir_path}/dist/{apk_name}')
