import os.path
import re

import config
from hcglobal import log
from util import adb


def get_app_path_in_system():
    path_map = {}
    pattern_package = re.compile(r' {2}Package \[(.+)]')
    pattern_path = re.compile(r' {4}codePath=(.+)')

    section = False
    package = ''
    for line in adb.shell('dumpsys package packages'):
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


def get_app_path_in_data():
    path_map = {}

    for line in adb.shell('pm list packages -f -s'):
        line = line[8:].strip()
        if not line.startswith('/data/app/'):
            continue
        splits = line.rsplit('=', 1)
        path_map[splits[1]] = splits[0]

    return path_map


def pull_updated_app(full_ota: bool):
    path_map = get_app_path_in_system()
    for package, path_in_data in get_app_path_in_data().items():
        if not full_ota and package not in config.MODIFY_PACKAGE:
            continue

        path_in_system = path_map[package]
        if full_ota and path_in_system.startswith('/system/'):
            path_in_system = f'/system{path_in_system}'
        log(f'更新系统应用: {path_in_system}')

        # TODO: full_ota, delete oat or add replace variable
        # TODO: /data/ksu/module updated app

        path_in_system = path_in_system[1:]
        os.makedirs(path_in_system)
        adb.pull(path_in_data, f'{path_in_system}/{os.path.basename(path_in_system)}.apk')
