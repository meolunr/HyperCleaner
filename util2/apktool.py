import os
import sys

LIB_DIR = os.path.join(sys.path[0], 'lib')


def decode(file: str, output: str, no_res=True):
    no_res = '-r' if no_res else ''
    print(f'java -jar {LIB_DIR}/apktool.jar d {no_res} {file} -o {output}')


def build(dir_path: str, output: str, copy_original=True):
    original_param = '-c' if copy_original else ''
    print(f'java -jar {LIB_DIR}/apktool.jar b {original_param} {dir_path} -o {output}')
