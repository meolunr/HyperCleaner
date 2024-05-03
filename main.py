import hashlib
import io
import os
import re
import shutil
import sys
import zipfile

import imgfile
import vbmeta
from build import ApkFile
from build.method_specifier import MethodSpecifier
from util import AdbUtils

BIN_DIR = os.path.join(sys.path[0], 'bin')
OVERLAY_DIR = os.path.join(sys.path[0], 'overlay')
UNPACK_IMG = ('mi_ext', 'odm', 'product', 'system', 'system_dlkm', 'system_ext', 'vendor', 'vendor_dlkm')


def log(string: str):
    print(f'\n>>> {string}')


def process_in_tmp(func):
    def wrapper(*args, **kwargs):
        cwd = os.getcwd()
        if os.path.exists('tmp'):
            print('Delete temp files ...')
            shutil.rmtree('tmp')

        os.mkdir('tmp')
        os.chdir('tmp')
        result = func(*args, **kwargs)

        os.chdir(cwd)
        shutil.rmtree('tmp')
        return result

    return wrapper


def disable_wakeup_dialog(apk_file: ApkFile):
    smali_file = apk_file.open_smali('com/miui/wakepath/ui/ConfirmStartActivity.smali')
    specifier = MethodSpecifier()
    specifier.access = MethodSpecifier.Access.PROTECTED
    specifier.keywords.append('"android.intent.action.PICK"')
    new_method_fragment = '''\
    const/4 v0, 0x0

    const/4 v1, -0x1

    invoke-virtual {p0, v0, v1}, Lcom/miui/wakepath/ui/ConfirmStartActivity;->onClick(Landroid/content/DialogInterface;I)V

    invoke-virtual {p0}, Landroid/app/Activity;->finish()V

    return-void\
    '''
    new_method_body = smali_file.find_method(specifier).replace('return-void', new_method_fragment)
    smali_file.method_replace(smali_file.find_method(specifier), new_method_body)


def disable_wifi_blocked_notification(apk_file: ApkFile):
    smali_file = apk_file.open_smali('com/miui/networkassistant/utils/NotificationUtil.smali')
    specifier = MethodSpecifier()
    specifier.name = 'sendWifiNetworkBlockedNotify'
    smali_file.method_nop(specifier)


def lock_100_score(apk_file: ApkFile):
    specifier = MethodSpecifier()

    smali_file = apk_file.open_smali('com/miui/securityscan/ui/main/MainContentFrame.smali')
    specifier.name = 'onClick'
    smali_file.method_nop(specifier)

    smali_file = apk_file.open_smali('com/miui/securityscan/scanner/ScoreManager.smali')
    specifier.name = None
    specifier.keywords.append('getMinusPredictScore')
    smali_file.method_return0(specifier)


def disable_cloud_control(apk_file: ApkFile):
    smali_file = apk_file.open_smali('com/miui/powerkeeper/cloudcontrol/LocalUpdateUtils.smali')
    specifier = MethodSpecifier()
    specifier.name = 'startCloudSyncData'
    smali_file.method_nop(specifier)


def global_maximum_fps(apk_file: ApkFile):
    smali_file = apk_file.open_smali('com/miui/powerkeeper/statemachine/DisplayFrameSetting.smali')
    specifier = MethodSpecifier()
    specifier.name = 'setScreenEffect'
    specifier.parameters = 'Ljava/lang/String;II'
    smali_file.method_nop(specifier)


@process_in_tmp
def process_security_center():
    print('>>> Process SecurityCenter.apk')
    AdbUtils.pull('/system/priv-app/SecurityCenter/SecurityCenter.apk')
    apk_file = ApkFile('SecurityCenter.apk')
    apk_file.decode()

    disable_wakeup_dialog(apk_file)
    disable_wifi_blocked_notification(apk_file)
    lock_100_score(apk_file)

    path = apk_file.build()
    AdbUtils.push_as_root(path, '/system/priv-app/SecurityCenter/')


@process_in_tmp
def process_power_keeper():
    print('>>> Process PowerKeeper.apk')
    AdbUtils.pull('/system/app/PowerKeeper/PowerKeeper.apk')
    apk_file = ApkFile('PowerKeeper.apk')
    apk_file.decode()

    disable_cloud_control(apk_file)
    global_maximum_fps(apk_file)

    path = apk_file.build()
    AdbUtils.push_as_root(path, '/system/app/PowerKeeper/')
    AdbUtils.exec_as_root('rm -rf /data/vendor/thermal/config')


@process_in_tmp
def process_joyose():
    print('>>> Process Joyose.apk')
    AdbUtils.pull('/system/app/Joyose/Joyose.apk')
    apk_file = ApkFile('Joyose.apk')
    apk_file.decode()

    smali_file = apk_file.find_smali('allow connect:')
    specifier = MethodSpecifier()
    specifier.keywords.append('allow connect:')
    smali_file.method_nop(specifier)

    path = apk_file.build()
    AdbUtils.push_as_root(path, '/system/app/Joyose/')
    AdbUtils.exec_as_root('pm clear com.xiaomi.joyose')


@process_in_tmp
def process_systemui():
    print('>>> Process MiuiSystemUI.apk')
    AdbUtils.pull('/system_ext/priv-app/MiuiSystemUI/MiuiSystemUI.apk')
    apk_file = ApkFile('MiuiSystemUI.apk')
    apk_file.decode()

    smali_file = apk_file.open_smali('com/android/settingslib/bluetooth/LocalBluetoothAdapter.smali')
    specifier = MethodSpecifier()
    specifier.name = 'isSupportBluetoothRestrict'
    smali_file.method_return0(specifier)

    path = apk_file.build()
    AdbUtils.push_as_root(path, '/system_ext/priv-app/MiuiSystemUI/')


def unzip():
    test_file = 'miui_SHENNONG_OS1.0.39.0.UNBCNXM_c67d65e7de_14.0.zip'
    log(f'解压 {test_file}')
    with zipfile.ZipFile(test_file) as f:
        f.extract('payload.bin', 'out')


def dump_payload():
    if os.path.exists('payload.bin'):
        log('解包 payload.bin')
        payload = os.path.join(BIN_DIR, 'payload.exe')
        os.system(f'{payload} -o images payload.bin')
    else:
        log('未找到 payload.bin 文件')
        exit()


def unpack_img():
    extract_erofs = os.path.join(BIN_DIR, 'extract.erofs.exe')
    for img in os.listdir('images'):
        file = os.path.join('images', img)
        if imgfile.file_system(file) == imgfile.FS_TYPE_EROFS:
            log(f'提取分区文件: {img}')
            os.system(f'{extract_erofs} -x -i {file}')


def patch_vbmeta(file):
    log(f'修补 vbmeta: {file}')
    avb_magic = b'AVB0'
    flags_offset = 0x7b
    flags_to_set = b'\x03'

    with open(file, 'rb+') as f:
        buf = f.read(len(avb_magic))
        if buf == avb_magic:
            f.seek(flags_offset)
            f.write(flags_to_set)
        else:
            print('无法修改，非验证引导文件')


def disable_avb_and_dm_verity(file: str):
    log(f'禁用 AVB 验证引导和 Data 加密: {file}')
    with open(file, 'r+') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = re.sub(',avb(?:=.+?,|,)', ',', line)
            line = re.sub(',avb_keys=.+avbpubkey', '', line)

            line = re.sub(',fileencryption=.+?,', ',', line)
            line = re.sub(',metadata_encryption=.+?,', ',', line)
            line = re.sub(',keydirectory=.+?,', ',', line)
            lines[i] = line
        f.seek(0)
        f.truncate()
        f.writelines(lines)


def repack_img():
    mkfs_erofs = os.path.join(BIN_DIR, 'mkfs.erofs.exe')
    for img in UNPACK_IMG:
        log(f'打包分区文件: {img}')
        fs_config = f'config/{img}_fs_config'
        contexts = f'config/{img}_file_contexts'
        os.system(f'{mkfs_erofs} -zlz4hc,1 -T 1230768000 --mount-point /{img} --fs-config-file {fs_config} --file-contexts {contexts} images/{img}.img {img}')


def repack_super():
    log('打包 super.img')
    super_size = 9126805504
    output = io.StringIO()
    output.write(os.path.join(BIN_DIR, 'lpmake.exe '))
    output.write('--metadata-size 65536 ')
    output.write('--super-name super ')
    output.write('--metadata-slots 3 ')
    output.write('--virtual-ab ')
    output.write(f'--device super:{super_size} ')
    output.write(f'--group qti_dynamic_partitions_a:{super_size} ')
    output.write(f'--group qti_dynamic_partitions_b:{super_size} ')

    for img in UNPACK_IMG:
        img_path = f'images/{img}.img'
        size = os.path.getsize(img_path)
        output.write(f'--partition {img}_a:readonly:{size}:qti_dynamic_partitions_a ')
        output.write(f'--image {img}_a={img_path} ')
        output.write(f'--partition {img}_b:none:0:qti_dynamic_partitions_b ')

    output.write('--force-full-image ')
    output.write('--output images/super.img')
    cmd = output.getvalue()
    os.system(cmd)

    for img in UNPACK_IMG:
        img_path = f'images/{img}.img'
        if os.path.exists(img_path):
            os.remove(img_path)

    log('使用 zstd 压缩 super.img')
    zstd = os.path.join(BIN_DIR, 'zstd.exe')
    os.system(f'{zstd} --rm images/super.img -o images/super.img.zst')


def generate_script():
    log('生成刷机脚本')
    with open(os.path.join(OVERLAY_DIR, 'update-binary'), encoding='utf-8') as fi:
        content = fi.read()
        with open('update-binary', 'w', encoding='utf-8', newline='') as fo:
            fo.write(content)


def compress_zip():
    log('构建刷机包')
    with zipfile.ZipFile('tmp.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as f:
        for i in os.listdir('images'):
            f.write(os.path.join('images', i))
        f.write('update-binary', 'META-INF/com/google/android/update-binary')
        f.write(os.path.join(OVERLAY_DIR, 'zstd'), 'META-INF/com/google/android/zstd')

    md5 = hashlib.md5()
    with open('tmp.zip', 'rb') as f:
        md5.update(f.read())
    file_hash = md5.hexdigest()[:10]
    os.rename('tmp.zip', f'HC_shennong_OS1.0.39.0_{file_hash}_14.zip')


def main():
    unzip()
    os.chdir('out')
    vbmeta.patch('images/vbmeta.img')
    # dump_payload()

    # recovery_img = 'images/recovery.img'
    # if os.path.exists(recovery_img):
    #     os.remove(recovery_img)
    #
    # unpack_img()

    # for img in glob('vbmeta*.img', root_dir='images'):
    #     patch_vbmeta(os.path.join('images', img))

    # for file in glob('**/etc/fstab.*', recursive=True):
    #     disable_avb_and_dm_verity(file)

    # appmodifier.run()
    # repack_img()
    # repack_super()
    # generate_script()
    # compress_zip()
    os.chdir('..')

    # AdbUtils.mount_rw('/')
    # AdbUtils.mount_rw('/system_ext')
    # AdbUtils.mount_rw('/product')
    # AdbUtils.mount_rw('/vendor')

    # delete_rubbish()
    # process_security_center()
    # process_power_keeper()
    # process_joyose()
    # process_systemui()


if __name__ == '__main__':
    main()
