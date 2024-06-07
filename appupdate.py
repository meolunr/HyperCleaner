import io
import json
import os
import re
import shutil
from enum import Enum, auto

import config
from hcglobal import MISC_DIR, log
from util import adb, template

RECORD_JSON = 'product/UpdatedApp.json'


class NewApp(object):
    class Source(Enum):
        ROM = auto()
        MODULE = auto()
        DATA = auto()

    def __init__(self, package, data_path, system_path):
        self.package = package
        self.data_path = data_path
        self.system_path = system_path
        self.system_path_rom = self._combine_system_path(system_path, False)
        self.system_path_module = self._combine_system_path(system_path, True)
        self.source = None

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


def read_record():
    log('读取系统应用更新记录')
    if not os.path.isfile(RECORD_JSON):
        if not os.path.isdir('product'):
            os.mkdir('product')
        adb.pull(f'/{RECORD_JSON}', 'product')
        open(RECORD_JSON, 'a').close()

    with open(RECORD_JSON, 'r', encoding='utf-8') as f:
        try:
            data: dict = json.load(f)
            rom, module = set(data.get('rom', set())), set(data.get('module', set()))
        except json.decoder.JSONDecodeError:
            rom, module = set(), set()
    return rom, module


def write_record(rom: set = None, module: set = None):
    rom_to_be_written, module_to_be_written = read_record()
    log('写入系统应用更新记录')
    with open(RECORD_JSON, 'w+', encoding='utf-8', newline='\n') as f:
        if rom:
            rom_to_be_written = rom
        if module:
            module_to_be_written = module

        # Move rom-record of the app that has been updated when building rom to module-record
        for package in module_to_be_written:
            if package in rom_to_be_written:
                rom_to_be_written.remove(package)

        data = {}
        if len(rom_to_be_written) != 0:
            data['rom'] = tuple(rom_to_be_written)
        if len(module_to_be_written) != 0:
            data['module'] = tuple(module_to_be_written)
        json.dump(data, f)


def fetch_updated_app():
    apps = set()
    existing = set()

    path_map_data = get_app_in_data()
    path_map_system = get_app_in_system()
    for package, path_in_data in path_map_data.items():
        app = NewApp(package, path_in_data, path_map_system[package])
        app.source = NewApp.Source.DATA
        apps.add(app)
        existing.add(package)

    rom, module = read_record()
    for package in rom:
        if package in existing:
            continue
        path = adb.get_apk_path(package)
        app = NewApp(package, path, os.path.dirname(path))
        app.source = NewApp.Source.ROM
        apps.add(app)
    for package in module:
        if package in existing:
            continue
        path = adb.get_apk_path(package)
        app = NewApp(package, path, os.path.dirname(path))
        app.source = NewApp.Source.MODULE
        apps.add(app)

    return apps


def run_on_rom():
    for app in fetch_updated_app():
        log(f'更新系统应用: {app.system_path_rom}')
        adb.pull(app.data_path, f'{app.system_path_rom}/{os.path.basename(app.system_path_rom)}.apk')
        oat = f'{app.system_path_rom}/oat'
        if os.path.exists(oat):
            shutil.rmtree(oat)


def run_on_module():
    apps = [x for x in fetch_updated_app() if x.source != NewApp.Source.ROM and x.package in config.MODIFY_PACKAGE]
    packages = set()
    mount_output = io.StringIO()
    remove_oat = set()

    for app in apps:
        log(f'更新系统应用: {app.system_path_module}')
        os.makedirs(app.system_path_rom)
        adb.pull(app.data_path, f'{app.system_path_rom}/{os.path.basename(app.system_path_rom)}.apk')
        packages.add(app.package)
        mount_output.write(f'mount -o bind $modDir/{app.system_path_module} {app.system_path}\n')
        remove_oat.add(f'/{app.system_path_module}/oat')

    write_record(module=packages)
    template.substitute(f'{MISC_DIR}/module_template/AppUpdate/post-fs-data.sh', var_mount=mount_output.getvalue())
    template.substitute(f'{MISC_DIR}/module_template/AppUpdate/customize.sh', var_remove_oat='\n'.join(remove_oat))
