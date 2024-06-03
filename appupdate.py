import os
import re
import shutil
import string

import config
from hcglobal import MISC_DIR, log
from util import adb


def get_app_in_system():
    path_map = {}
    pattern_package = re.compile(r' {2}Package \[(.+)]')
    pattern_path = re.compile(r' {4}codePath=(.+)')

    section = False
    package = ''
    for line in adb.getoutput('dumpsys package packages'):
        if line.startswith('Hidden system packages:'):
            section = True
        elif section:
            match = re.search(pattern_package, line)
            if match:
                package = match.group(1)
            match = re.search(pattern_path, line)
            if match:
                path_map[package] = match.group(1)

    return path_map


def get_app_in_data():
    path_map = {}

    for line in adb.getoutput('pm list packages -f -s'):
        line = line[8:].strip()
        if not line.startswith('/data/app/'):
            continue
        splits = line.rsplit('=', 1)
        path_map[splits[1]] = splits[0]

    return path_map


# TODO: /data/ksu/module updated app
def run_on_full_ota():
    path_map_system = get_app_in_system()
    path_map_data = get_app_in_data()

    for package, path_in_data in path_map_data.items():
        path_in_system = path_map_system[package]
        if path_in_system.startswith('/system/'):
            path_in_system = f'/system{path_in_system}'
        log(f'更新系统应用: {path_in_system}')

        path_in_system = path_in_system[1:]
        adb.pull(path_in_data, f'{path_in_system}/{os.path.basename(path_in_system)}.apk')
        oat = f'{path_in_system}/oat'
        if os.path.exists(oat):
            shutil.rmtree(oat)


# TODO: /data/ksu/module updated app
def run_on_ksu_module():
    path_map_system = get_app_in_system()
    path_map_data = get_app_in_data()
    remove_oat = []

    for package, path_in_data in path_map_data.items():
        if package not in config.MODIFY_PACKAGE:
            continue
        path_in_system = path_map_system[package]
        log(f'更新系统应用: {path_in_system}')

        if path_in_system.startswith('/system/'):
            remove_oat.append(f'{path_in_system}/oat')
        else:
            remove_oat.append(f'/system{path_in_system}/oat')

        path_in_system = path_in_system[1:]
        os.makedirs(path_in_system)
        adb.pull(path_in_data, f'{path_in_system}/{os.path.basename(path_in_system)}.apk')

    with open(f'{MISC_DIR}/module_template/AppUpdate/customize.sh', 'r', encoding='utf-8') as fi:
        content = string.Template(fi.read()).safe_substitute(var_remove_oat='\n'.join(remove_oat))
        with open('customize.sh', 'w', encoding='utf-8', newline='') as fo:
            fo.write(content)
