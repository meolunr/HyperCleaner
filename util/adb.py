import os

from hcglobal import OVERLAY_DIR

_DATA_TMP = '/data/local/tmp/'


def execute(command: str):
    os.system(f'adb shell su -c {command}')


def push(src: str, dst: str):
    tmp_file = f'{_DATA_TMP}/{os.path.basename(src)}'
    os.system(f'adb push {src} {_DATA_TMP}')
    execute(f'cp -rf {tmp_file} {dst}')
    execute(f'rm -rf {tmp_file}')


def install_test_module():
    module_dir = '/data/adb/modules/hypercleaner'
    execute(f'mkdir -p {module_dir}')
    push(f'{OVERLAY_DIR}/module.prop', module_dir)
