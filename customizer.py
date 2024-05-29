import os
import re
import shutil
import sys
from glob import glob

from build.apkfile import ApkFile
from build.smali import MethodSpecifier
from hcglobal import MISC_DIR, log


def rm_files():
    def ignore_comment(line: str):
        annotation_index = line.find('#')
        if annotation_index >= 0:
            line = line[:annotation_index]
        return line.strip()

    with open(f'{sys.path[0]}/remove-files.txt', 'r', encoding='utf-8') as f:
        for item in map(ignore_comment, f.readlines()):
            if len(item) == 0:
                continue
            if os.path.exists(item):
                log(f'删除文件: {item}')
                shutil.rmtree(item)
            else:
                log(f'文件不存在: {item}')


def replace_analytics():
    log('替换 BlankAnalytics')
    analytics = 'product/app/AnalyticsCore/AnalyticsCore.apk'
    if os.path.exists(analytics):
        os.remove(analytics)
        shutil.rmtree('product/app/AnalyticsCore/oat')
        shutil.copy(f'{MISC_DIR}/BlankAnalytics.apk', analytics)


def remove_system_signature_check():
    log('去除系统签名检查')
    apk = ApkFile('system/system/framework/services.jar')
    apk.decode()

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


def run():
    rm_files()
    replace_analytics()
    remove_system_signature_check()


# Unused Code ==================================================================================
# SecurityCenter
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


# SecurityCenter
def disable_wifi_blocked_notification(apk_file: ApkFile):
    smali_file = apk_file.open_smali('com/miui/networkassistant/utils/NotificationUtil.smali')
    specifier = MethodSpecifier()
    specifier.name = 'sendWifiNetworkBlockedNotify'
    smali_file.method_nop(specifier)


# SecurityCenter
def lock_100_score(apk_file: ApkFile):
    specifier = MethodSpecifier()

    smali_file = apk_file.open_smali('com/miui/securityscan/ui/main/MainContentFrame.smali')
    specifier.name = 'onClick'
    smali_file.method_nop(specifier)

    smali_file = apk_file.open_smali('com/miui/securityscan/scanner/ScoreManager.smali')
    specifier.name = None
    specifier.keywords.append('getMinusPredictScore')
    smali_file.method_return0(specifier)


# PowerKeeper
def disable_cloud_control(apk_file: ApkFile):
    smali_file = apk_file.open_smali('com/miui/powerkeeper/cloudcontrol/LocalUpdateUtils.smali')
    specifier = MethodSpecifier()
    specifier.name = 'startCloudSyncData'
    smali_file.method_nop(specifier)


# PowerKeeper
def global_maximum_fps(apk_file: ApkFile):
    smali_file = apk_file.open_smali('com/miui/powerkeeper/statemachine/DisplayFrameSetting.smali')
    specifier = MethodSpecifier()
    specifier.name = 'setScreenEffect'
    specifier.parameters = 'Ljava/lang/String;II'
    smali_file.method_nop(specifier)


# Joyose
def process_joyose():
    apk_file = ApkFile('Joyose.apk')
    apk_file.decode()

    smali_file = apk_file.find_smali('allow connect:')
    specifier = MethodSpecifier()
    specifier.keywords.append('allow connect:')
    smali_file.method_nop(specifier)


# MiuiSystemUI
def process_systemui():
    apk_file = ApkFile('MiuiSystemUI.apk')
    apk_file.decode()

    smali_file = apk_file.open_smali('com/android/settingslib/bluetooth/LocalBluetoothAdapter.smali')
    specifier = MethodSpecifier()
    specifier.name = 'isSupportBluetoothRestrict'
    smali_file.method_return0(specifier)
