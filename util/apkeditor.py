import subprocess

from hcglobal import LIB_DIR


def decode(file: str, output: str, resource_type: str = 'xml'):
    subprocess.run(f'java -jar {LIB_DIR}/APKEditor.jar d -t {resource_type} -i {file} -o {output}', stderr=subprocess.STDOUT)


def build(dir_path: str, output: str):
    subprocess.run(f'java -jar {LIB_DIR}/APKEditor.jar b -f -i {dir_path} -o {output}', stderr=subprocess.STDOUT)


def refactor(file: str, output: str):
    subprocess.run(f'java -jar {LIB_DIR}/APKEditor.jar x -i {file} -o {output}', stderr=subprocess.STDOUT)
