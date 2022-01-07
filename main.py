import encodings.utf_8
import os
import shutil

from build import ApkFile
from build.method_specifier import MethodSpecifier
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


def delete_rubbish():
    def ignore_annotation(line: str):
        annotation_index = line.find('#')
        if annotation_index >= 0:
            line = line[:annotation_index]
        return line.strip()

    model = AdbUtils.exec_with_result('getprop ro.product.name')[:-1]
    print('>>> Delete rubbish files, device: %s' % model)

    with open('rubbish-files-%s.txt' % model, encoding=encodings.utf_8.getregentry().name) as file:
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
    smali_file.replace_method(smali_file.find_method(specifier), new_method_body)


def disable_wifi_blocked_notification(apk_file: ApkFile):
    smali_file = apk_file.open_smali('com/miui/networkassistant/utils/NotificationUtil.smali')
    specifier = MethodSpecifier()
    specifier.name = 'sendWifiNetworkBlockedNotify'
    new_method_body = '''\
.method public static sendWifiNetworkBlockedNotify(Landroid/content/Context;Z)V
    .locals 0

    return-void
.end method\
    '''
    smali_file.replace_method(smali_file.find_method(specifier), new_method_body)


def lock_100_score(apk_file: ApkFile):
    specifier = MethodSpecifier()

    smali_file = apk_file.open_smali('com/miui/securityscan/ui/main/MainContentFrame.smali')
    specifier.name = 'onClick'
    new_method_body = '''\
.method public onClick(Landroid/view/View;)V
    .locals 0

    return-void
.end method\
    '''
    smali_file.replace_method(smali_file.find_method(specifier), new_method_body)

    smali_file = apk_file.open_smali('com/miui/securityscan/scanner/ScoreManager.smali')
    specifier.name = None
    specifier.keywords.append('getMinusPredictScore')
    old_method_body = smali_file.find_method(specifier)
    new_method_body = old_method_body.splitlines()[0] + '''
    .locals 1
    
    const/4 v0, 0x0

    return v0
.end method\
    '''
    smali_file.replace_method(smali_file.find_method(specifier), new_method_body)


@process_in_tmp
def process_security_center():
    print('>>> Process security center')
    print('>>> Pull SecurityCenter.apk')
    AdbUtils.pull('/system/priv-app/SecurityCenter/SecurityCenter.apk')
    apk_file = ApkFile('SecurityCenter.apk')
    apk_file.decode()

    disable_wakeup_dialog(apk_file)
    disable_wifi_blocked_notification(apk_file)
    lock_100_score(apk_file)

    path = apk_file.build()
    AdbUtils.push_as_root(path, '/system/priv-app/SecurityCenter/')
    AdbUtils.push_as_root('SecurityCenter.apk', '/system/priv-app/SecurityCenter/')


def main():
    AdbUtils.mount_rw('/')
    AdbUtils.mount_rw('/vendor')
    AdbUtils.mount_rw('/product')

    # AdbUtils.exec_as_root(
    #     'mv /system/app/MIUIThemeManager/MIUIThemeManager.apk /system/app/MIUIThemeManager/MIUIThemeManager.apk0')
    # exit()
    # delete_rubbish()
    process_security_center()


if __name__ == '__main__':
    main()
