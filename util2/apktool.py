import os
import sys

_LIB_DIR = os.path.join(sys.path[0], 'lib')
_BIN_DIR = os.path.join(sys.path[0], 'bin')


def decode(file: str, output: str, no_res: bool):
    no_res = '-r' if no_res else ''
    os.system(f'java -jar {_LIB_DIR}/apktool.jar d {no_res} {file} -o {output}')


def build(dir_path: str, copy_original: bool):
    original_param = '-c' if copy_original else ''
    os.system(f'java -jar {_LIB_DIR}/apktool.jar b {original_param} {dir_path}')


def zipalign(src: str, dst: str):
    os.system(f'{_BIN_DIR}/zipalign.exe -f -p 4 {src} {dst}')
