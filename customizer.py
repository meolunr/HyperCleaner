import os
import re
import shutil
import sys
from glob import glob

from build.apkfile import ApkFile
from build.smali import MethodSpecifier
from hcglobal import OVERLAY_DIR
from hcglobal import log
from util import AdbUtils


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
    apk_file = ApkFile('SecurityCenter.apk')
    apk_file.decode()

    disable_wakeup_dialog(apk_file)
    disable_wifi_blocked_notification(apk_file)
    lock_100_score(apk_file)

    path = apk_file.build()


@process_in_tmp
def process_power_keeper():
    print('>>> Process PowerKeeper.apk')
    apk_file = ApkFile('PowerKeeper.apk')
    apk_file.decode()

    disable_cloud_control(apk_file)
    global_maximum_fps(apk_file)

    path = apk_file.build()


@process_in_tmp
def process_joyose():
    print('>>> Process Joyose.apk')
    apk_file = ApkFile('Joyose.apk')
    apk_file.decode()

    smali_file = apk_file.find_smali('allow connect:')
    specifier = MethodSpecifier()
    specifier.keywords.append('allow connect:')
    smali_file.method_nop(specifier)

    path = apk_file.build()


@process_in_tmp
def process_systemui():
    print('>>> Process MiuiSystemUI.apk')
    apk_file = ApkFile('MiuiSystemUI.apk')
    apk_file.decode()

    smali_file = apk_file.open_smali('com/android/settingslib/bluetooth/LocalBluetoothAdapter.smali')
    specifier = MethodSpecifier()
    specifier.name = 'isSupportBluetoothRestrict'
    smali_file.method_return0(specifier)

    path = apk_file.build()


def remove_system_signature_check():
    log('去除系统签名检查')
    apk = ApkFile('system/system/framework/services.jar')
    apk.decode()

    apk = ApkFile('system/system/framework/services.jar')
    specifier = MethodSpecifier()
    specifier.keywords.append('getMinimumSignatureSchemeVersionForTargetSdk')
    for smali in apk.find_smali('getMinimumSignatureSchemeVersionForTargetSdk'):
        old_body = smali.find_method(specifier)
        pattern = '''\
    invoke-static {[v|p]\\d}, Landroid/util/apk/ApkSignatureVerifier;->getMinimumSignatureSchemeVersionForTargetSdk\\(I\\)I

    move-result v(\\d)
'''
        match = re.search(pattern, old_body)
        new_segment = f'''\
    const/4 v{match.group(1)}, 0x0
'''
        new_body = old_body.replace(match.group(0), new_segment)
        smali.method_replace(old_body, new_body)

    apk.build()
    for file in glob('system/system/framework/oat/arm64/services.*'):
        os.remove(file)


def rm_files():
    def ignore_comment(line: str):
        annotation_index = line.find('#')
        if annotation_index >= 0:
            line = line[:annotation_index]
        return line.strip()

    with open(f'{sys.path[0]}/remove-files.txt', 'r', encoding='utf-8') as f:
        for item in map(ignore_comment, f.readlines()):
            if len(item) != 0:
                log(f'删除文件: {item}')
                os.remove(item)
    log('替换 BlankAnalytics')
    analytics = 'product/app/AnalyticsCore/AnalyticsCore.apk'
    if os.path.exists(analytics):
        os.remove(analytics)
        shutil.copy(f'{OVERLAY_DIR}/BlankAnalytics.apk', analytics)


def run():
    remove_system_signature_check()
    rm_files()
