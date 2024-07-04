import os
import re
import shutil
import sys
from glob import glob
from zipfile import ZipFile

from build.apkfile import ApkFile
from build.smali import MethodSpecifier
from hcglobal import MISC_DIR, log

_MODIFIED_FLAG = b'HC-Mod'


def modified(file: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            f = ZipFile(file, 'r')
            comment = f.comment
            f.close()

            if comment != _MODIFIED_FLAG:
                result = func(*args, **kwargs)

                with ZipFile(file, 'a') as f:
                    f.comment = _MODIFIED_FLAG
                oat = f'{os.path.dirname(file)}/oat'
                if os.path.exists(oat):
                    shutil.rmtree(oat)

                return result

        return wrapper

    return decorator


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
    specifier.keywords.add('getMinimumSignatureSchemeVersionForTargetSdk')
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


def disable_wake_path_dialog():
    log('禁用关联启动对话框')
    apk = ApkFile('system_ext/framework/miui-services.jar')
    apk.decode()

    smali = apk.open_smali('miui/app/ActivitySecurityHelper.smali')
    specifier = MethodSpecifier()
    specifier.name = 'getCheckStartActivityIntent'
    old_body = smali.find_method(specifier)
    pattern = 'if-eqz p6, :cond_.+'
    match = re.search(pattern, old_body)
    new_body = old_body.replace(match.group(0), '')
    smali.method_replace(old_body, new_body)

    apk.build()
    for file in glob('system_ext/framework/**/miui-services.*', recursive=True):
        if not os.path.samefile(apk.file, file):
            os.remove(file)


@modified('product/priv-app/MIUIPackageInstaller/MIUIPackageInstaller.apk')
def patch_package_installer():
    apk = ApkFile('product/priv-app/MIUIPackageInstaller/MIUIPackageInstaller.apk')
    apk.refactor()
    apk.decode(False)

    # Remove ads
    smali = apk.open_smali('com/miui/packageInstaller/model/ApkInfo.smali')
    specifier = MethodSpecifier()
    specifier.name = 'getSystemApp'
    smali.method_return_boolean(specifier, True)

    # Disable ads switch by default
    specifier = MethodSpecifier()
    specifier.return_type = 'Z'
    specifier.keywords.add('"ads_enable"')
    for smali in apk.find_smali('"ads_enable"'):
        smali.method_return_boolean(specifier, False)

    # Allow installation of system applications
    specifier = MethodSpecifier()
    specifier.parameters = 'Landroid/content/Context;Ljava/lang/String;'
    specifier.return_type = 'Z'
    specifier.keywords.add('getApplicationInfo')
    for smali in apk.find_smali('"PackageUtil"'):
        smali.method_return_boolean(specifier, False)

    # Turn on the safe mode UI without enabling its features
    invoke_specifier = MethodSpecifier()
    invoke_specifier.parameters = 'Landroid/content/Context;'
    invoke_specifier.return_type = 'Z'
    invoke_specifier.keywords.add('"safe_mode_is_open_cloud_config"')

    specifier = MethodSpecifier()
    specifier.parameters = ''
    specifier.return_type = 'Z'
    specifier.invoke_methods.add(invoke_specifier)
    for smali in apk.find_smali('"FullSafeHelper"'):
        smali.method_return_boolean(specifier, True)

    # Hide outdated switches
    xml = apk.open_xml('xml/settings.xml')
    root = xml.get_root()
    for element in root.findall('miuix.preference.CheckBoxPreference'):
        if element.get(xml.make_attr_key('android:key')) == 'pref_key_open_ads':
            element.set(xml.make_attr_key('app:isPreferenceVisible'), 'false')
    for element in root.findall('miuix.preference.TextPreference'):
        if element.get(xml.make_attr_key('android:key')) == 'pref_key_security_mode_security_verify_risk_app':
            element.set(xml.make_attr_key('app:isPreferenceVisible'), 'false')
    xml.commit()

    # Hide feedback button
    xml = apk.open_xml('menu/full_safe_installer_prepare_action_bar.xml')
    group_tree = xml.get_root().find('group')
    for element in group_tree.findall('item'):
        if element.get(xml.make_attr_key('android:id')) == '@id/feedback':
            group_tree.remove(element)
    xml.commit()

    apk.build()


def run_on_rom():
    rm_files()
    replace_analytics()
    remove_system_signature_check()
    disable_wake_path_dialog()
    patch_package_installer()


def run_on_module():
    patch_package_installer()


# Unused Code ==================================================================================
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


# MiuiSystemUI
def systemui():
    apk_file = ApkFile('MiuiSystemUI.apk')
    apk_file.decode()

    smali_file = apk_file.open_smali('com/android/settingslib/bluetooth/LocalBluetoothAdapter.smali')
    specifier = MethodSpecifier()
    specifier.name = 'isSupportBluetoothRestrict'
    smali_file.method_return0(specifier)
