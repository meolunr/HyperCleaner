import argparse
import hashlib
import io
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from glob import glob

import appupdate
import config
import customize
import vbmeta
from hcglobal import LIB_DIR, MISC_DIR, log
from util import imgfile, template


def unzip(file: str):
    log(f'解压 {file}')
    _7z = f'{LIB_DIR}/7za.exe'
    subprocess.run(f'{_7z} e {file} payload.bin -oout', check=True)


def dump_payload():
    log('解包 payload.bin')
    payload = f'{LIB_DIR}/payload.exe'
    subprocess.run(f'{payload} -o images payload.bin', check=True)


def remove_official_recovery():
    recovery_img = 'images/recovery.img'
    if os.path.exists(recovery_img):
        log('去除官方 Recovery')
        os.remove(recovery_img)


def unpack_img():
    for partition in config.unpack_partitions.keys():
        config.unpack_partitions[partition] = imgfile.file_system(f'images/{partition}.img')

    extract_erofs = f'{LIB_DIR}/extract.erofs.exe'
    magiskboot = f'{LIB_DIR}/magiskboot.exe'

    for partition, filesystem in config.unpack_partitions.items():
        img = f'{partition}.img'
        file = f'images/{img}'
        log(f'提取分区文件: {img}, 格式: {filesystem}')
        match filesystem:
            case imgfile.FileSystem.EROFS:
                subprocess.run(f'{extract_erofs} -x -i {file}', check=True)
            case imgfile.FileSystem.BOOT:
                os.mkdir(partition)
                shutil.copy(file, f'{partition}/{img}')
                os.chdir(partition)
                subprocess.run(f'{magiskboot} unpack {img}', check=True)
                os.chdir('..')


def read_rom_information():
    def getvalue(prop: str):
        return prop.rstrip().split('=')[1]

    with open('product/etc/build.prop', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('ro.product.product.name'):
                config.device = getvalue(line)
            elif line.startswith('ro.product.build.version.incremental'):
                sub_version = re.match(r'V\d+(\.\d+\.\d+\.\d+)\..+', getvalue(line)).group(1)
                config.version = f'OS1{sub_version}'
            elif line.startswith('ro.product.build.version.release'):
                config.sdk = getvalue(line)


def custom_kernel(file: str):
    if not file and not os.path.isfile(file):
        return
    log('自定义内核镜像')
    shutil.copy(file, 'boot/kernel')


def patch_vbmeta():
    for img in glob('vbmeta*.img', root_dir='images'):
        log(f'修补 vbmeta: {img}')
        vbmeta.patch(f'images/{img}', 'images/boot.img')


def disable_avb_and_dm_verity():
    for file in glob('**/etc/fstab.*', recursive=True):
        log(f'禁用 AVB 验证引导和 Data 加密: {file}')
        with open(file, 'r+', encoding='utf-8', newline='') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                # Remove avb
                line = re.sub(',avb(?:=.+?,|,)', ',', line)
                line = re.sub(',avb_keys=.+avbpubkey', '', line)
                # Remove forced data encryption
                line = re.sub(',fileencryption=.+?,', ',', line)
                line = re.sub(',metadata_encryption=.+?,', ',', line)
                line = re.sub(',keydirectory=.+?,', ',', line)
                lines[i] = line
            f.seek(0)
            f.truncate()
            f.writelines(lines)


def handle_pangu_overlay():
    if not os.path.isdir('product/pangu'):
        return
    log('处理盘古架构')
    lines = []
    with open('config/product_file_contexts', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('/product/pangu'):
                splits = line.split(' ')
                path = splits[0][14:]
                if not os.path.exists(f'system{path}'):
                    lines.append(f'/system{path} {splits[1]}')
    with open('config/system_file_contexts', 'a', encoding='utf-8', newline='') as f:
        f.writelines(lines)

    lines.clear()
    with open('config/product_fs_config', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('product/pangu'):
                pos = line.index(' ')
                path = line[:pos][13:]
                if not os.path.exists(f'system{path}'):
                    lines.append(f'system{path}{line[pos:]}')
    with open('config/system_fs_config', 'a', encoding='utf-8', newline='') as f:
        f.writelines(lines)


def repack_img():
    mkfs_erofs = f'{LIB_DIR}/mkfs.erofs.exe'
    magiskboot = f'{LIB_DIR}/magiskboot.exe'

    for partition, filesystem in config.unpack_partitions.items():
        log(f'打包分区文件: {partition}')
        file = f'images/{partition}.img'
        match filesystem:
            case imgfile.FileSystem.EROFS:
                fs_config = f'config/{partition}_fs_config'
                contexts = f'config/{partition}_file_contexts'
                subprocess.run(f'{mkfs_erofs} -zlz4hc,1 -T 1230768000 --mount-point /{partition} --fs-config-file {fs_config} --file-contexts {contexts} {file} {partition}',
                               check=True)
            case imgfile.FileSystem.BOOT:
                os.chdir(partition)
                subprocess.run(f'{magiskboot} repack boot.img ../{file}', check=True)
                os.chdir('..')


def repack_super():
    log('打包 super.img')
    output = io.StringIO()
    output.write(f'{LIB_DIR}/lpmake.exe ')
    output.write('--metadata-size 65536 ')
    output.write('--super-name super ')
    output.write('--metadata-slots 3 ')
    output.write('--virtual-ab ')
    output.write(f'--device super:{config.SUPER_SIZE} ')
    output.write(f'--group qti_dynamic_partitions_a:{config.SUPER_SIZE} ')
    output.write(f'--group qti_dynamic_partitions_b:{config.SUPER_SIZE} ')

    for partition in config.SUPER_PARTITIONS:
        img = f'images/{partition}.img'
        size = os.path.getsize(img)
        log(f'动态分区: {partition}, 大小: {size} 字节')
        output.write(f'--partition {partition}_a:readonly:{size}:qti_dynamic_partitions_a ')
        output.write(f'--image {partition}_a={img} ')
        output.write(f'--partition {partition}_b:none:0:qti_dynamic_partitions_b ')

    output.write('--force-full-image ')
    output.write('--output images/super.img')
    cmd = output.getvalue()
    subprocess.run(cmd, check=True)

    for partition in config.SUPER_PARTITIONS:
        img = f'images/{partition}.img'
        if os.path.exists(img):
            os.remove(img)

    log('使用 zstd 压缩 super.img')
    zstd = f'{LIB_DIR}/zstd.exe'
    subprocess.run(f'{zstd} --rm images/super.img -o images/super.img.zst', check=True)


def generate_script():
    log('生成刷机脚本')
    output = io.StringIO()

    for img in os.listdir('images'):
        if not img.endswith('.img'):
            continue
        partition = os.path.splitext(img)[0]
        output.write(f'flash "images/{img}" "/dev/block/bootdevice/by-name/{partition}_a"\n')
        output.write(f'flash "images/{img}" "/dev/block/bootdevice/by-name/{partition}_b"\n')
    if os.path.exists('images/super.img.zst'):
        output.write('flashZstd "images/super.img.zst" "/dev/block/bootdevice/by-name/super"\n\n')
        for item in config.SUPER_PARTITIONS:
            output.write(f'remapSuper {item}_a\n')
    var_flash_img = output.getvalue()

    var_remove_data_app = ''
    if config.remove_data_apps:
        output.seek(0)
        output.truncate(0)
        output.write('\nprint "- 更新系统应用"\n')
        output.write('lookupPackagePath\n')
        for package in config.remove_data_apps:
            output.write(f'removeDataApp {package}\n')
        var_remove_data_app = output.getvalue()

    template_dict = {
        'var_device': config.device,
        'var_version': config.version,
        'var_sdk': config.sdk,
        'var_flash_img': var_flash_img,
        'var_remove_data_app': var_remove_data_app
    }
    template.substitute(f'{MISC_DIR}/update-binary', mapping=template_dict)


def compress_zip():
    log('构建刷机包')
    archives = ['META-INF']
    for img in os.listdir('images'):
        archives.append(f'images/{img}')

    flash_script_dir = 'META-INF/com/google/android'
    if not os.path.exists(flash_script_dir):
        os.makedirs(flash_script_dir)
    shutil.move('update-binary', f'{flash_script_dir}/update-binary')
    shutil.copy(f'{MISC_DIR}/zstd', f'{flash_script_dir}/zstd')

    _7z = f'{LIB_DIR}/7za.exe'
    subprocess.run(f'{_7z} a tmp.zip {' '.join(archives)}', check=True)

    md5 = hashlib.md5()
    with open('tmp.zip', 'rb') as f:
        md5.update(f.read())
    file_hash = md5.hexdigest()[:10]
    os.rename('tmp.zip', f'HC_{config.device}_{config.version}_{file_hash}_{config.sdk}.zip')


def make_update_module():
    log('构建系统应用更新模块')
    os.chdir('out/appupdate')  # Temporary folder for testing
    appupdate.run_on_module()
    if not os.path.isfile(appupdate.RECORD_JSON):
        return
    customize.run_on_module()

    # Let the module manager app handle partition path automatically
    for partition in config.unpack_partitions.keys():
        if partition != 'system' and os.path.isdir(partition):
            shutil.move(partition, f'system/{partition}')

    version_code = time.strftime('%Y%m%d')
    template.substitute(f'{MISC_DIR}/module_template/AppUpdate/module.prop', var_version=time.strftime('%Y.%m.%d'), var_version_code=version_code)
    _7z = f'{LIB_DIR}/7za.exe'
    subprocess.run(f'{_7z} a HC_AppUpdate_{version_code}.zip {' '.join(os.listdir())}', check=True)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('zip', help='需要处理的 ROM 包')
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='显示帮助信息')
    parser.add_argument('-k', '--kernel', help='自定义内核镜像')
    parser.add_subparsers().add_parser('appupdate', help='打包系统应用更新模块')
    args = parser.parse_args()

    if args.zip == 'appupdate':
        make_update_module()
        return

    if args.kernel:
        config.unpack_partitions['boot'] = None

    start = datetime.now()
    unzip(args.zip)
    os.chdir('out')
    dump_payload()
    remove_official_recovery()
    unpack_img()
    read_rom_information()
    custom_kernel(args.kernel)
    patch_vbmeta()
    disable_avb_and_dm_verity()
    handle_pangu_overlay()
    appupdate.run_on_rom()
    customize.run_on_rom()
    repack_img()
    repack_super()
    generate_script()
    compress_zip()
    result = datetime.now() - start
    log(f'已完成, 耗时 {int(result.seconds / 60)} 分 {result.seconds % 60} 秒')


if __name__ == '__main__':
    main()
