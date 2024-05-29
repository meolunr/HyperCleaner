import os

from hcglobal import MISC_DIR, log

_DATA_TMP_DIR = '/data/local/tmp'
_MODULE_DIR = '/data/adb/modules/hypercleaner'


def execute(command: str):
    os.system(f'adb shell su -c {command}')


def shell(command: str):
    return os.popen(f'adb shell su -c {command}')


def push(src: str, dst: str):
    log(f'推送设备文件: {dst}')
    tmp_file = f'{_DATA_TMP_DIR}/{os.path.basename(src)}'
    os.popen(f'adb push {src} {_DATA_TMP_DIR}')
    # Use cp and rm commands to avoid moving file permissions simultaneously
    execute(f'cp -rf {tmp_file} {dst}')
    execute(f'rm -rf {tmp_file}')


def pull(src: str, dst: str):
    log(f'拉取设备文件: {src}')
    os.system(f'adb pull {src} {dst}')


def push_test_module():
    log(f'推送 HC 测试模块到设备内置存储，请手动安装')
    os.popen(f'adb push {MISC_DIR}/module_template/HCTestModule.zip /sdcard')


def module_overlay(file: str):
    log(f'HCTest 文件覆盖: {file}')
    dir_name = f'{_MODULE_DIR}/{os.path.dirname(file)}'
    execute(f'mkdir -p {dir_name}')
    push(file, dir_name)


def module_rm(file: str):
    log(f'HCTest 文件删除: {file}')
    dir_name = os.path.dirname(file)
    execute(f'mkdir -p {_MODULE_DIR}/{dir_name}')
    execute(f'mknod {_MODULE_DIR}/{file} c 0 0')
