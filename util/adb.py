import os

from hcglobal import OVERLAY_DIR

_DATA_TMP_DIR = '/data/local/tmp/'
_MODULE_DIR = '/data/adb/modules/hypercleaner'


def execute(command: str):
    os.system(f'adb shell su -c {command}')


def push(src: str, dst: str):
    tmp_file = f'{_DATA_TMP_DIR}/{os.path.basename(src)}'
    os.system(f'adb push {src} {_DATA_TMP_DIR}')
    # Use cp and rm commands to avoid moving file permissions simultaneously
    execute(f'cp -rf {tmp_file} {dst}')
    execute(f'rm -rf {tmp_file}')


def install_test_module():
    execute(f'mkdir -p {_MODULE_DIR}')
    push(f'{OVERLAY_DIR}/module.prop', _MODULE_DIR)


def rm(file: str):
    dir_name = os.path.dirname(file)
    execute(f'mkdir -p {_MODULE_DIR}{dir_name}')
    execute(f'mknod {_MODULE_DIR}{file} c 0 0')
