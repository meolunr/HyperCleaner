import subprocess

from hcglobal import LIB_DIR


def decode(file: str, output: str, no_res: bool):
    no_res = '-r' if no_res else ''
    subprocess.run(f'java -jar {LIB_DIR}/apktool.jar d {no_res} {file} -o {output}')


def build(dir_path: str, copy_original: bool):
    original_param = '-c' if copy_original else ''
    subprocess.run(f'java -jar {LIB_DIR}/apktool.jar b {original_param} {dir_path}')


def zipalign(src: str, dst: str):
    subprocess.run(f'{LIB_DIR}/zipalign.exe -f -p 4 {src} {dst}')
