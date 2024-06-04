import os
import re
import shutil
import string

import config
from hcglobal import MISC_DIR, log
from util import adb


class NewApp(object):
    def __init__(self, package, data_path, system_path):
        self.package = package
        self.data_path = data_path
        self.system_path_rom = self._combine_system_path(system_path, False)
        self.system_path_module = self._combine_system_path(system_path, True)

    @staticmethod
    def _combine_system_path(system_path, is_module):
        if (is_module and not system_path.startswith('/system/')) or (not is_module and system_path.startswith('/system/')):
            system_path = f'/system{system_path}'
        return system_path[1:]


def get_app_in_data():
    path_map = {}

    for line in adb.getoutput('pm list packages -f -s'):
        line = line[8:].strip()
        if not line.startswith('/data/app/'):
            continue
        splits = line.rsplit('=', 1)
        path_map[splits[1]] = splits[0]

    return path_map


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


def fetch_updated_app():
    apps = []
    path_map_data = get_app_in_data()
    path_map_system = get_app_in_system()

    for package, path_in_data in path_map_data.items():
        app = NewApp(package, path_in_data, path_map_system[package])
        apps.append(app)

    return apps


# TODO: /data/ksu/module updated app
def run_on_rom():
    for app in fetch_updated_app():
        log(f'更新系统应用: {app.system_path_rom}')
        adb.pull(app.data_path, f'{app.system_path_rom}/{os.path.basename(app.system_path_rom)}.apk')
        oat = f'{app.system_path_rom}/oat'
        if os.path.exists(oat):
            shutil.rmtree(oat)


# TODO: /data/ksu/module updated app
def run_on_module():
    remove_oat = []

    for app in fetch_updated_app():
        if app.package not in config.MODIFY_PACKAGE:
            continue
        log(f'更新系统应用: {app.system_path_module}')
        os.makedirs(app.system_path_rom)
        adb.pull(app.data_path, f'{app.system_path_rom}/{os.path.basename(app.system_path_rom)}.apk')
        remove_oat.append(f'/{app.system_path_module}/oat')

    with open(f'{MISC_DIR}/module_template/AppUpdate/customize.sh', 'r', encoding='utf-8') as fi:
        content = string.Template(fi.read()).safe_substitute(var_remove_oat='\n'.join(remove_oat))
        with open('customize.sh', 'w', encoding='utf-8', newline='') as fo:
            fo.write(content)
