import hashlib
import io
import os
import re
import shutil
import string
import sys
from datetime import datetime
from glob import glob

import config
import customizer
import imgfile
import vbmeta
from log import log

BIN_DIR = os.path.join(sys.path[0], 'bin')
OVERLAY_DIR = os.path.join(sys.path[0], 'overlay')


def unzip():
    test_file = 'miui_SHENNONG_OS1.0.39.0.UNBCNXM_c67d65e7de_14.0.zip'
    log(f'解压 {test_file}')
    _7z = os.path.join(BIN_DIR, '7za.exe')
    os.system(f'{_7z} e {test_file} payload.bin -oout')


def dump_payload():
    if os.path.exists('payload.bin'):
        log('解包 payload.bin')
        payload = os.path.join(BIN_DIR, 'payload.exe')
        os.system(f'{payload} -o images payload.bin')
    else:
        log('未找到 payload.bin 文件')
        exit()


def remove_official_recovery():
    recovery_img = 'images/recovery.img'
    if os.path.exists(recovery_img):
        log('去除官方 Recovery')
        os.remove(recovery_img)


def unpack_img():
    extract_erofs = os.path.join(BIN_DIR, 'extract.erofs.exe')
    for partition in config.UNPACK_PARTITIONS:
        img = f'{partition}.img'
        file = os.path.join('images', img)
        if imgfile.file_system(file) == imgfile.FS_TYPE_EROFS:
            log(f'提取分区文件: {img}')
            os.system(f'{extract_erofs} -x -i {file}')


def patch_vbmeta():
    for img in glob('vbmeta*.img', root_dir='images'):
        log(f'修补 vbmeta: {img}')
        vbmeta.patch(os.path.join('images', img), 'images/boot.img')


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
    log('处理盘古架构')
    if not os.path.exists('product/pangu'):
        return

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
    mkfs_erofs = os.path.join(BIN_DIR, 'mkfs.erofs.exe')
    for partition in config.UNPACK_PARTITIONS:
        log(f'打包分区文件: {partition}')
        fs_config = f'config/{partition}_fs_config'
        contexts = f'config/{partition}_file_contexts'
        os.system(f'{mkfs_erofs} -zlz4hc,1 -T 1230768000 --mount-point /{partition} --fs-config-file {fs_config} --file-contexts {contexts} images/{partition}.img {partition}')


def repack_super():
    log('打包 super.img')
    output = io.StringIO()
    output.write(os.path.join(BIN_DIR, 'lpmake.exe '))
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
    os.system(cmd)

    for partition in config.SUPER_PARTITIONS:
        img = f'images/{partition}.img'
        if os.path.exists(img):
            os.remove(img)

    log('使用 zstd 压缩 super.img')
    zstd = os.path.join(BIN_DIR, 'zstd.exe')
    os.system(f'{zstd} --rm images/super.img -o images/super.img.zst')


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

    template_dict = {
        'var_device': config.device,
        'var_version': config.version,
        'var_sdk': config.sdk,
        'var_flash_img': output.getvalue()
    }
    with open(os.path.join(OVERLAY_DIR, 'update-binary'), 'r', encoding='utf-8') as fi:
        content = string.Template(fi.read()).safe_substitute(template_dict)
        with open('update-binary', 'w', encoding='utf-8', newline='') as fo:
            fo.write(content)


def compress_zip():
    log('构建刷机包')
    archives = ['META-INF', 'images/super.img.zst']
    for img in os.listdir('images'):
        archives.append(os.path.join('images', img))

    flash_script_dir = 'META-INF/com/google/android'
    if not os.path.exists(flash_script_dir):
        os.makedirs(flash_script_dir)
    shutil.move('update-binary', os.path.join(flash_script_dir, 'update-binary'))
    shutil.copy(os.path.join(OVERLAY_DIR, 'zstd'), os.path.join(flash_script_dir, 'zstd'))

    _7z = os.path.join(BIN_DIR, '7za.exe')
    os.system(f'{_7z} a tmp.zip {' '.join(archives)}')

    md5 = hashlib.md5()
    with open('tmp.zip', 'rb') as f:
        md5.update(f.read())
    file_hash = md5.hexdigest()[:10]
    os.rename('tmp.zip', f'HC_{config.device}_{config.version}_{file_hash}_{config.sdk}.zip')


def main():
    start = datetime.now()
    unzip()
    os.chdir('out')
    dump_payload()
    remove_official_recovery()
    unpack_img()
    patch_vbmeta()
    disable_avb_and_dm_verity()
    handle_pangu_overlay()
    customizer.run()
    repack_img()
    repack_super()
    generate_script()
    compress_zip()
    result = datetime.now() - start
    log(f'已完成, 耗时 {int(result.seconds / 60)} 分 {result.seconds % 60} 秒')


if __name__ == '__main__':
    main()
