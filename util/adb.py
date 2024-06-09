import os
import subprocess

from hcglobal import MISC_DIR, log

_DATA_TMP_DIR = '/data/local/tmp'
_MODULE_DIR = '/data/adb/modules/hypercleaner'


def execute(command: str):
    subprocess.run(f'adb shell su -c {command}')


def getoutput(command: str):
    popen = subprocess.Popen(f'adb shell su -c {command}', stdout=subprocess.PIPE, universal_newlines=True)
    return popen.stdout


def push(src: str, dst: str):
    log(f'推送设备文件: {dst}')
    tmp_file = f'{_DATA_TMP_DIR}/{os.path.basename(src)}'
    subprocess.run(f'adb push {src} {_DATA_TMP_DIR}', stdout=subprocess.DEVNULL)
    # Use cp and rm commands to avoid moving file permissions simultaneously
    execute(f'cp -rf {tmp_file} {dst}')
    execute(f'rm -rf {tmp_file}')


def pull(src: str, dst: str):
    log(f'拉取设备文件: {src}')
    subprocess.run(f'adb pull {src} {dst}', stdout=subprocess.DEVNULL)


def install_test_module():
    subprocess.run(f'adb push {MISC_DIR}/module_template/HCTestModule.zip /sdcard', stdout=subprocess.DEVNULL)
    execute('ksud module install /sdcard/HCTestModule.zip')
    execute('rm -f /sdcard/HCTestModule.zip')
    log(f'已安装 HC 测试模块，重启设备后生效')


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


def get_apk_path(package: str):
    return getoutput(f'pm path {package}').read()[8:-1]
