import subprocess

from hcglobal import LIB_DIR


def decode(file: str, output: str):
    subprocess.run(f'java -jar {LIB_DIR}/APKEditor.jar d -i {file} -o {output}', stderr=subprocess.STDOUT)


def build(dir_path: str, output: str):
    subprocess.run(f'java -jar {LIB_DIR}/APKEditor.jar b -f -i {dir_path} -o {output}', stderr=subprocess.STDOUT)
