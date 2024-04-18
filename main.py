import encodings.utf_8
import os
import shutil
import sys
import zipfile

import imgfile
from build import ApkFile
from build.method_specifier import MethodSpecifier
from util import AdbUtils

OUT_DIR = 'out'
BIN_DIR = os.path.join(sys.path[0], 'bin')


def log(string: str):
    print(f'>>> {string}')


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


def delete_rubbish():
    def ignore_annotation(line: str):
        annotation_index = line.find('#')
        if annotation_index >= 0:
            line = line[:annotation_index]
        return line.strip()

    model = AdbUtils.exec_with_result('getprop ro.product.name')[:-1]
    print('>>> Delete rubbish files, device: %s' % model)

    rubbish_file_list = 'rubbish-files-%s.txt' % model
    if not os.path.isfile(rubbish_file_list):
        rubbish_file_list = 'rubbish-files.txt'

    with open(rubbish_file_list, encoding=encodings.utf_8.getregentry().name) as file:
        for rubbish in map(ignore_annotation, file.readlines()):
            if len(rubbish) != 0:
                print('Deleting %s' % rubbish)
                AdbUtils.exec_as_root('rm -rf %s' % rubbish)


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
    test_file = 'miui_SHENNONG_OS1.0.33.0.UNBCNXM_bd2a9334c8_14.0.zip'
    log(f'解压 {test_file}')
    with zipfile.ZipFile(test_file) as file:
        file.extract('payload.bin', OUT_DIR)


def dump_payload():
    if os.path.exists('payload.bin'):
        payload = os.path.join(BIN_DIR, 'payload.exe')
        os.system(f'{payload} -o image payload.bin')
    else:
        log('未找到 payload.bin 文件')
        exit()


def unpack_img():
    extract_erofs = os.path.join(BIN_DIR, 'extract.erofs.exe')
    for img in os.listdir('image'):
        file = os.path.join('image', img)
        if imgfile.file_system(file) == 'erofs':
            os.system(f'{extract_erofs} -x -i {file}')


def main():
    # unzip()
    os.chdir(OUT_DIR)
    # dump_payload()
    unpack_img()
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
