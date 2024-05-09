import os
import sys

LIB_DIR = os.path.join(sys.path[0], 'lib')
BIN_DIR = os.path.join(sys.path[0], 'bin')


def decode(file: str, output: str, no_res=True):
    no_res = '-r' if no_res else ''
    print(f'java -jar {LIB_DIR}/apktool.jar d {no_res} {file} -o {output}')


def build(dir_path: str, output: str, copy_original=True):
    original_param = '-c' if copy_original else ''
    print(f'java -jar {LIB_DIR}/apktool.jar b {original_param} {dir_path} -o {output}')


def zipalign(file: str):
    old_file = f'{file}.old'
    os.rename(file, old_file)
    print(f'{BIN_DIR}/zipalign.exe -p 4 {old_file} {file}')
    os.remove(old_file)
