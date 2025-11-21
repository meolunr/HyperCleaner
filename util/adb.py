import os
import subprocess

from hcglobal import MISC_DIR, log

_DATA_TMP_DIR = '/data/local/tmp'
_MODULE_DIR = '/data/adb/modules/colorcleaner'


def execute(command: str):
    return subprocess.run(f'''adb shell "su -c '{command}'"''').returncode


def getoutput(command: str):
    popen = subprocess.Popen(f'''adb shell "su -c '{command}'"''', stdout=subprocess.PIPE, universal_newlines=True)
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
    subprocess.run(f'adb push {MISC_DIR}/module_template/CCTestModule.zip /sdcard', stdout=subprocess.DEVNULL)
    execute('ksud module install /sdcard/CCTestModule.zip')
    execute('rm -f /sdcard/CCTestModule.zip')
    log(f'已安装 CC 测试模块，重启设备后生效')


def module_overlay(phone_file: str):
    log(f'HCTest 文件覆盖: {phone_file}')
    dir_name = f'{_MODULE_DIR}{os.path.dirname(phone_file)}'
    execute(f'mkdir -p {dir_name}')
    if phone_file.startswith('/system/'):
        push(f'system{phone_file}', dir_name)
    else:
        push(phone_file[1:], dir_name)

    post_fs_data = f'{_MODULE_DIR}/post-fs-data.sh'
    mount = f'mount -o bind $MODDIR{phone_file} {phone_file}'
    if f'{mount}\n' not in set(getoutput(f'cat {post_fs_data}')):
        execute(f"echo '{mount.replace('$', r'\$')}' | su -c 'tee -a {post_fs_data} > /dev/null'")


def module_rm(phone_path: str):
    log(f'CCTest 文件删除: {phone_path}')
    if phone_path.startswith('/system/'):
        module_rm_path = phone_path
    else:
        module_rm_path = f'/system{phone_path}'

    if phone_path.startswith('/my_'):
        if is_dir(phone_path):
            execute(f'mkdir -p {_MODULE_DIR}{module_rm_path}')
            execute(f'touch {_MODULE_DIR}{module_rm_path}/.replace')
        else:
            execute(f'mkdir -p {_MODULE_DIR}{os.path.dirname(module_rm_path)}')
            execute(f'touch {_MODULE_DIR}{module_rm_path}')
    else:
        execute(f'mkdir -p {_MODULE_DIR}{os.path.dirname(module_rm_path)}')
        execute(f'mknod {_MODULE_DIR}{module_rm_path} c 0 0')


def is_dir(phone_path: str):
    return execute(f'test -d {phone_path}') == 0


def get_apk_path(package: str):
    return getoutput(f'pm path {package}').read()[8:-1]
