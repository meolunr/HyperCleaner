import os

from hcglobal import LIB_DIR


def decode(file: str, output: str, no_res: bool):
    no_res = '-r' if no_res else ''
    os.system(f'java -jar {LIB_DIR}/apktool.jar d {no_res} {file} -o {output}')


def build(dir_path: str, copy_original: bool):
    original_param = '-c' if copy_original else ''
    os.system(f'java -jar {LIB_DIR}/apktool.jar b {original_param} {dir_path}')


def zipalign(src: str, dst: str):
    os.system(f'{LIB_DIR}/zipalign.exe -f -p 4 {src} {dst}')
