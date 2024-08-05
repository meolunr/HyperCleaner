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
    pattern = '''\
    invoke-static .+?, Landroid/util/apk/ApkSignatureVerifier;->getMinimumSignatureSchemeVersionForTargetSdk\\(I\\)I

    move-result ([v|p]\\d)
'''
    repl = '''\
    const/4 \\g<1>, 0x0
'''
    for smali in apk.find_smali('getMinimumSignatureSchemeVersionForTargetSdk'):
        old_body = smali.find_method(specifier)
        new_body = re.sub(pattern, repl, old_body)
        smali.method_replace(old_body, new_body)

    apk.build()
    for file in glob('system/system/framework/oat/arm64/services.*'):
        os.remove(file)


def patch_miui_service():
    apk = ApkFile('system_ext/framework/miui-services.jar')
    apk.decode()

    log('禁用关联启动对话框')
    smali = apk.open_smali('miui/app/ActivitySecurityHelper.smali')
    specifier = MethodSpecifier()
    specifier.name = 'getCheckStartActivityIntent'
    old_body = smali.find_method(specifier)
    pattern = 'if-eqz p6, :cond_.+'
    match = re.search(pattern, old_body)
    new_body = old_body.replace(match.group(0), '')
    smali.method_replace(old_body, new_body)

    log('防止主题恢复')
    smali = apk.open_smali('com/android/server/am/ActivityManagerServiceImpl.smali')
    specifier = MethodSpecifier()
    specifier.name = 'finishBooting'
    specifier.parameters = ''
    old_body = smali.find_method(specifier)
    pattern = '''\
    invoke-static {.+?}, Lmiui/drm/DrmBroadcast;->getInstance\\(Landroid/content/Context;\\)Lmiui/drm/DrmBroadcast;

    move-result-object .+?

    invoke-virtual {.+?}, Lmiui/drm/DrmBroadcast;->broadcast\\(\\)V
'''
    new_body = re.sub(pattern, '', old_body)
    smali.method_replace(old_body, new_body)

    apk.build()
    for file in glob('system_ext/framework/**/miui-services.*', recursive=True):
        if not os.path.samefile(apk.file, file):
            os.remove(file)


@modified('product/priv-app/MIUIPackageInstaller/MIUIPackageInstaller.apk')
def patch_package_installer():
    log('净化应用包管理组件')
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


@modified('product/app/MIUIThemeManager/MIUIThemeManager.apk')
def patch_theme_manager():
    apk = ApkFile('product/app/MIUIThemeManager/MIUIThemeManager.apk')
    apk.decode()

    log('去除主题商店广告')
    smali = apk.open_smali('com/android/thememanager/basemodule/ad/model/AdInfoResponse.smali')
    specifier = MethodSpecifier()
    specifier.name = 'isAdValid'
    smali.method_return_boolean(specifier, False)

    # Filter advertising elements
    smali = apk.find_smali('"DetailRecommendFactory.java"').pop()
    specifier = MethodSpecifier()
    specifier.parameters = 'Lcom/android/thememanager/router/recommend/entity/UICard;'
    specifier.return_type = 'Ljava/util/List;'

    old_body = smali.find_method(specifier)
    pattern = '''\
    :goto_(\\d)
    invoke-interface {.+?}, Ljava/util/Iterator;->hasNext\\(\\)Z
'''
    match = re.search(pattern, old_body)
    goto = match.group(1)
    pattern = '''\
    check-cast ([v|p]\\d), Lcom/android/thememanager/router/recommend/entity/UIImageWithLink;
(?:.|\n)*?
    const/4 ([v|p]\\d), 0x1
'''
    repl = f'''\
    check-cast \\g<1>, Lcom/android/thememanager/router/recommend/entity/UIImageWithLink;

    iget-object \\g<2>, \\g<1>, Lcom/android/thememanager/router/recommend/entity/UIImageWithLink;->adInfo:Lcom/android/thememanager/basemodule/ad/model/AdInfoResponse;

    if-nez \\g<2>, :goto_{goto}

    const/4 \\g<2>, 0x1
'''
    new_body = re.sub(pattern, repl, old_body)
    smali.method_replace(old_body, new_body)

    log('破解主题免费')
    smali = apk.open_smali('com/android/thememanager/detail/theme/model/OnlineResourceDetail.smali')
    specifier = MethodSpecifier()
    specifier.name = 'toResource'
    specifier.return_type = 'Lcom/android/thememanager/basemodule/resource/model/Resource;'

    old_body = smali.find_method(specifier)
    pattern = '''\
    return-object ([v|p]\\d)
'''
    match = re.search(pattern, old_body)
    register1 = match.group(1)
    num = int(register1[1:]) - 1
    if num < 0:
        num += 2
    register2 = f'{register1[:1]}{num}'

    new_segment = f'''\
    const/4 {register2}, 0x1

    iput-boolean {register2}, p0, Lcom/android/thememanager/detail/theme/model/OnlineResourceDetail;->bought:Z
    
    return-object {register1}
'''
    new_body = old_body.replace(match.group(0), new_segment)
    smali.method_replace(old_body, new_body)

    smali = apk.open_smali('com/android/thememanager/basemodule/views/DiscountPriceView.smali')
    specifier = MethodSpecifier()
    specifier.name = 'setPrice'
    specifier.parameters = 'II'

    old_body = smali.find_method(specifier)
    lines = old_body.splitlines()
    lines.insert(2, '    const/4 p1, 0x0')
    lines.insert(3, '    const/4 p2, 0x0')
    smali.method_replace(old_body, '\n'.join(lines))

    smali = apk.find_smali('"DrmService.java"', '"theme"', '"check rights isLegal: "').pop()
    specifier = MethodSpecifier()
    specifier.parameters = 'Lcom/android/thememanager/basemodule/resource/model/Resource;'
    specifier.return_type = 'Lmiui/drm/DrmManager$DrmResult;'

    old_body = smali.find_method(specifier)
    lines = old_body.splitlines()
    new_body = f'''\
{lines[0]}
    .locals 0
    
    sget-object p0, Lmiui/drm/DrmManager$DrmResult;->DRM_SUCCESS:Lmiui/drm/DrmManager$DrmResult;

    return-object p0
.end method
'''
    smali.method_replace(old_body, new_body)

    smali = apk.open_smali('com/miui/maml/widget/edit/MamlutilKt.smali')
    specifier = MethodSpecifier()
    specifier.name = 'themeManagerSupportPaidWidget'
    specifier.parameters = 'Landroid/content/Context;'
    smali.method_return_boolean(specifier, False)

    apk.build()


@modified('system_ext/priv-app/MiuiSystemUI/MiuiSystemUI.apk')
def patch_system_ui():
    apk = ApkFile('system_ext/priv-app/MiuiSystemUI/MiuiSystemUI.apk')
    apk.decode()

    # Disable historical notifications
    log('禁用历史通知')
    smali = apk.open_smali('com/android/systemui/statusbar/notification/NotificationUtil.smali')
    specifier = MethodSpecifier()
    specifier.name = 'shouldSuppressFold'
    smali.method_return_boolean(specifier, True)

    smali = apk.open_smali('com/android/systemui/statusbar/notification/collection/coordinator/FoldCoordinator.smali')
    specifier = MethodSpecifier()
    specifier.name = 'attach'
    specifier.parameters = 'Lcom/android/systemui/statusbar/notification/collection/NotifPipeline;'
    smali.method_nop(specifier)

    # Hide the HD icon
    log('隐藏状态栏 HD 图标')
    smali = apk.open_smali('com/android/systemui/statusbar/phone/MiuiIconManagerUtils.smali')
    old_body = smali.find_constructor()

    pattern = '''\
(    sput-object ([v|p]\\d), Lcom/android/systemui/statusbar/phone/MiuiIconManagerUtils;->RIGHT_BLOCK_LIST:Ljava/util/ArrayList;)
(?:.|\n)*?
(    const-string ([v|p]\\d), "mute")
'''
    match = re.search(pattern, old_body)
    register1 = match.group(2)
    register2 = match.group(4)
    new_segment = '''\
{}

    const-string {}, "hd"

    invoke-virtual {{{}, {}}}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z

{}
'''
    new_body = old_body.replace(match.group(0), new_segment.format(match.group(1), register2, register1, register2, match.group(3)))

    pattern = '''\
(    sput-object ([v|p]\\d), Lcom/android/systemui/statusbar/phone/MiuiIconManagerUtils;->CONTROL_CENTER_BLOCK_LIST:Ljava/util/ArrayList;)
(?:.|\n)*?
(    const-string ([v|p]\\d), "car")
'''
    match = re.search(pattern, old_body)
    register1 = match.group(2)
    register2 = match.group(4)
    new_body = new_body.replace(match.group(0), new_segment.format(match.group(1), register2, register1, register2, match.group(3)))

    smali.method_replace(old_body, new_body)

    log('重定向通知渠道设置')
    smali = apk.find_smali('"com.android.settings.Settings$AppNotificationSettingsActivity"').pop()
    smali.add_affiliated_smali(f'{MISC_DIR}/smali/NotificationChannel.smali', 'HcInjector.smali')
    specifier = MethodSpecifier()
    specifier.name = 'onClick'
    specifier.parameters = 'Landroid/view/View;'

    old_body = smali.find_method(specifier)
    pattern = '''\
    iget-object ([v|p]\\d), .+?, Lcom/android/systemui/statusbar/notification/row/MiuiNotificationMenuRow;->mSbn:Lcom/android/systemui/statusbar/notification/ExpandedNotification;
'''
    repl = '''\\g<0>
    sput-object \\g<1>, Lcom/android/systemui/statusbar/notification/row/HcInjector;->sbn:Landroid/service/notification/StatusBarNotification;
'''
    new_body = re.sub(pattern, repl, old_body)

    pattern = '''\
(    const-string .+?, ":settings:show_fragment_args"
(?:.|\n)*?
    invoke-virtual {([v|p]\\d), .+?, .+?}, Landroid/content/Intent;->putExtra\\(Ljava/lang/String;Landroid/os/Bundle;\\)Landroid/content/Intent;)
(?:.|\\n)*?
    return-void
(?:.|\\n)*?
    iget-object ([v|p]\\d), .+?, Lcom/android/systemui/statusbar/notification/row/MiuiNotificationMenuRow.+?
'''
    match = re.search(pattern, new_body)
    register1 = match.group(2)
    register2 = match.group(3)

    pattern = f'''\
    new-instance {register1}, Landroid/content/Intent;
(?:.|\\n)*?
{re.escape(match.group(1))}
((?:.|\\n)*?)
    return-void
'''
    repl = f'''\
    invoke-static {{}}, Lcom/android/systemui/statusbar/notification/row/HcInjector;->makeChannelSettingIntent()Landroid/content/Intent;

    move-result-object {register1}
\\g<1>
    const/4 {register2}, 0x0

    sput-object {register2}, Lcom/android/systemui/statusbar/notification/row/HcInjector;->sbn:Landroid/service/notification/StatusBarNotification;

    return-void
'''
    new_body = re.sub(pattern, repl, new_body)
    smali.method_replace(old_body, new_body)

    log('隐藏锁屏相机和负一屏')
    smali = apk.open_smali('com/android/keyguard/injector/KeyguardBottomAreaInjector.smali')

    specifier = MethodSpecifier()
    specifier.name = 'updateIcons'
    old_body = smali.find_method(specifier)
    new_body = '''\
.method public final updateIcons()V
    .locals 2

    const/16 v0, 0x8

    iget-object v1, p0, Lcom/android/keyguard/injector/KeyguardBottomAreaInjector;->mLeftAffordanceViewLayout:Landroid/widget/LinearLayout;

    if-eqz v1, :cond_0

    invoke-virtual {v1, v0}, Landroid/widget/LinearLayout;->setVisibility(I)V

    :cond_0
    iget-object v1, p0, Lcom/android/keyguard/injector/KeyguardBottomAreaInjector;->mRightAffordanceViewLayout:Landroid/widget/LinearLayout;

    if-eqz v1, :cond_1

    invoke-virtual {v1, v0}, Landroid/widget/LinearLayout;->setVisibility(I)V

    :cond_1
    return-void
.end method
'''
    smali.method_replace(old_body, new_body)

    specifier = MethodSpecifier()
    specifier.name = 'updateRightAffordanceViewLayoutVisibility'
    smali.method_nop(specifier)

    apk.build()


@modified('product/priv-app/MiuiMms/MiuiMms.apk')
def remove_mms_ads():
    apk = ApkFile('product/priv-app/MiuiMms/MiuiMms.apk')
    apk.decode()

    log('去除短信输入框广告')
    smali = apk.open_smali('com/miui/smsextra/ui/BottomMenu.smali')
    specifier = MethodSpecifier()
    specifier.name = 'allowMenuMode'
    specifier.return_type = 'Z'
    smali.method_return_boolean(specifier, False)

    log('去除短信下方广告')
    specifier = MethodSpecifier()
    specifier.name = 'setHideButton'
    specifier.is_abstract = False
    pattern = '''\
    iput-boolean ([v|p]\\d), p0, L.+?;->.+?:Z
'''
    repl = '''\
    const/4 \\g<1>, 0x1

\\g<0>'''
    for smali in apk.find_smali('final setHideButton'):
        old_body = smali.find_method(specifier)
        new_body = re.sub(pattern, repl, old_body)
        smali.method_replace(old_body, new_body)

    apk.build()


@modified('system/system/priv-app/TeleService/TeleService.apk')
def show_network_type_settings():
    log('显示网络类型设置')
    apk = ApkFile('system/system/priv-app/TeleService/TeleService.apk')
    apk.decode()

    smali = apk.open_smali('com/android/phone/NetworkModeManager.smali')
    specifier = MethodSpecifier()
    specifier.name = 'isRemoveNetworkModeSettings'

    specifier.parameters = 'I'
    smali.method_return_boolean(specifier, False)
    specifier.parameters = 'Lcom/android/internal/telephony/Phone;'
    smali.method_return_boolean(specifier, False)

    apk.build()


def patch_security_center():
    apk = ApkFile('product/priv-app/MIUISecurityCenter/MIUISecurityCenter.apk')
    apk.decode()

    log('去除应用信息举报按钮')
    smali = apk.open_smali('com/miui/appmanager/ApplicationsDetailsActivity.smali')
    specifier = MethodSpecifier()
    specifier.parameters = 'Landroid/content/Context;Landroid/net/Uri;'
    specifier.return_type = 'Z'
    specifier.keywords.add('"android.intent.action.VIEW"')
    specifier.keywords.add('"com.xiaomi.market"')
    smali.method_return_boolean(specifier, False)

    apk.build()


def run_on_rom():
    rm_files()
    replace_analytics()
    remove_system_signature_check()
    patch_miui_service()
    patch_package_installer()
    patch_theme_manager()
    patch_system_ui()
    remove_mms_ads()
    show_network_type_settings()
    patch_security_center()


def run_on_module():
    patch_package_installer()
    patch_theme_manager()
    patch_system_ui()
    remove_mms_ads()
    show_network_type_settings()
    patch_security_center()


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
