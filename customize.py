import io
import os
import re
import shutil
import string
import sys
from glob import glob
from zipfile import ZipFile

import config
from build.apkfile import ApkFile
from build.smali import MethodSpecifier
from hcglobal import MISC_DIR, log

_MODIFIED_FLAG = b'HC-Mod'


def modified(file: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not os.path.isfile(file):
                return None
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
            else:
                return None

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


def patch_services():
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

    # Remove the black screen when capturing display
    smali = apk.open_smali('com/android/server/wm/WindowState.smali')
    specifier = MethodSpecifier()
    specifier.name = 'isSecureLocked'
    smali.method_return_boolean(specifier, False)

    apk.build()
    for file in glob('system/system/framework/oat/arm64/services.*'):
        os.remove(file)


def patch_miui_services():
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

    log('允许对任意应用截屏')
    smali = apk.open_smali('com/android/server/wm/WindowManagerServiceImpl.smali')
    specifier = MethodSpecifier()
    specifier.name = 'notAllowCaptureDisplay'
    specifier.parameters = 'Lcom/android/server/wm/RootWindowContainer;I'
    smali.method_return_boolean(specifier, False)

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
    for smali in apk.find_smali('"PackageUtil"', '"getPackageVersionCode"'):
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
    for element in root.findall('.//miuix.preference.CheckBoxPreference'):
        if element.get(xml.make_attr_key('android:key')) == 'pref_key_open_ads':
            element.set(xml.make_attr_key('app:isPreferenceVisible'), 'false')
    for element in root.findall('.//miuix.preference.TextPreference'):
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

    repl = f'''\
    const/4 {register2}, 0x1

    iput-boolean {register2}, p0, Lcom/android/thememanager/detail/theme/model/OnlineResourceDetail;->bought:Z

    return-object {register1}
'''
    new_body = old_body.replace(match.group(0), repl)
    smali.method_replace(old_body, new_body)

    smali = apk.open_smali('com/android/thememanager/basemodule/views/DiscountPriceView.smali')
    specifier = MethodSpecifier()
    specifier.name = 'setPrice'
    specifier.parameters = 'II'

    old_body = smali.find_method(specifier)
    lines = old_body.splitlines()
    lines.insert(12, '    const/4 p1, 0x0')
    lines.insert(13, '    const/4 p2, 0x0')
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
    smali = apk.open_smali('com/miui/systemui/notification/MiuiBaseNotifUtil.smali')
    specifier = MethodSpecifier()
    specifier.name = 'shouldSuppressFold'
    smali.method_return_boolean(specifier, True)

    smali = apk.open_smali('com/android/systemui/statusbar/notification/collection/coordinator/FoldCoordinator.smali')
    specifier.name = 'attach'
    specifier.parameters = 'Lcom/android/systemui/statusbar/notification/collection/NotifPipeline;'
    smali.method_nop(specifier)

    # Hide the HD icon
    log('隐藏状态栏 HD 图标')
    smali = apk.open_smali('com/android/systemui/statusbar/policy/HDController.smali')
    specifier = MethodSpecifier()
    specifier.name = 'update'
    specifier.parameters = ''
    smali.method_nop(specifier)

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


@modified('product/priv-app/MIUISecurityCenter/MIUISecurityCenter.apk')
def patch_security_center():
    apk = ApkFile('product/priv-app/MIUISecurityCenter/MIUISecurityCenter.apk')
    apk.decode()

    log('去除应用信息举报按钮')
    smali = apk.open_smali('com/miui/appmanager/fragment/ApplicationsDetailsFragment.smali')
    specifier = MethodSpecifier()
    specifier.parameters = 'Landroid/content/Context;Landroid/net/Uri;'
    specifier.return_type = 'Z'
    specifier.keywords.add('"android.intent.action.VIEW"')
    specifier.keywords.add('"com.xiaomi.market"')
    smali.method_return_boolean(specifier, False)

    log('显示电池健康度')
    smali = apk.find_smali('.class Lcom/miui/powercenter/nightcharge/ChargeProtectFragment$', '.super Landroid/os/Handler;').pop()
    specifier = MethodSpecifier()
    specifier.name = 'handleMessage'
    specifier.parameters = 'Landroid/os/Message;'
    old_body = smali.find_method(specifier)

    utils_smali = apk.find_smali('"BatteryHealthUtils"').pop()
    utils_type_signature = utils_smali.get_type_signature()

    specifier = MethodSpecifier()
    specifier.keywords.add('"persist.vendor.smart.battMntor"')
    method_signature_1 = utils_smali.find_method(specifier).splitlines()[0].split(' ')[-1]
    specifier.keywords.clear()
    specifier.keywords.add('"key_get_battery_health_value"')
    method_signature_2 = utils_smali.find_method(specifier).splitlines()[0].split(' ')[-1]
    specifier.keywords.clear()
    specifier.keywords.add('"getBatterySoh: "')
    method_signature_3 = utils_smali.find_method(specifier).splitlines()[0].split(' ')[-1]

    pattern = f'''\
    invoke-static {{}}, {utils_type_signature}->{re.escape(method_signature_1)}

    move-result .+?

    if-eqz .+?, :cond_\\d

    invoke-static {{}}, {utils_type_signature}->{re.escape(method_signature_2)}

    move-result ([v|p]\\d)
'''
    repl = f'''\
    invoke-static {{}}, {utils_type_signature}->{method_signature_3}

    move-result-object \\g<1>

    :try_start_114
    invoke-static {{\\g<1>}}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I

    move-result \\g<1>
    :try_end_514
    .catch Ljava/lang/NumberFormatException; {{:try_start_114 .. :try_end_514}} :catch_1919

    goto :goto_810

    :catch_1919
    move-exception \\g<1>

    const/4 \\g<1>, -0x1

    :goto_810
'''
    new_body = re.sub(pattern, repl, old_body)
    smali.method_replace(old_body, new_body)

    log('显示电池温度')
    smali = apk.open_smali('com/miui/powercenter/nightcharge/ChargeProtectFragment.smali')
    specifier = MethodSpecifier()
    specifier.parameters = 'Landroid/content/Context;'
    specifier.return_type = 'Ljava/lang/String;'
    specifier.is_static = True
    specifier.keywords.add('-0x80000000')
    old_body = smali.find_method(specifier)

    pattern = f'''\
    invoke-static {{p0}}, L.+?;->.+?\\(Landroid/content/Context;\\)I

    move-result ([v|p]\\d)

    invoke-static {{p0}}, L.+?;->.+?\\(Landroid/content/Context;\\)I

    move-result ([v|p]\\d)

    const/high16 .+?, -0x80000000
(?:.|\\n)*?
    const/4 ([v|p]\\d), 0x5

    if-le .+?, \\3, :cond_(\\d)

    :cond_\\d
    move \\1, \\2

    :cond_\\4
'''
    match = re.search(pattern, old_body)
    register1 = match.group(1)
    register2 = match.group(2)
    cond = match.group(4)

    pattern = f'''\
    :cond_{cond}
(?:.|\\n)*?
.end method'''
    repl = f'''\
    :cond_{cond}
    new-instance {register2}, Ljava/lang/StringBuilder;

    invoke-direct {{{register2}}}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {{{register2}, {register1}}}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    const-string {register1}, "℃"

    invoke-virtual {{{register2}, {register1}}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {{{register2}}}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object {register1}

    return-object {register1}
.end method'''
    new_body = re.sub(pattern, repl, old_body)
    smali.method_replace(old_body, new_body)

    log('手机管家 100 分')
    # Lock 100 score
    smali = apk.open_smali('com/miui/securityscan/scanner/ScoreManager.smali')
    specifier = MethodSpecifier()
    specifier.return_type = 'I'
    specifier.keywords.add('getMinusPredictScore')

    old_body = smali.find_method(specifier)
    lines = old_body.splitlines()
    new_body = f'''\
{lines[0]}
    .locals 0

    const/16 p0, 0x0

    return p0
.end method
'''
    smali.method_replace(old_body, new_body)

    # Disable click events
    smali = apk.open_smali('com/miui/securityscan/ui/main/MainContentFrame.smali')
    specifier = MethodSpecifier()
    specifier.name = 'onClick'
    specifier.parameters = 'Landroid/view/View;'
    smali.method_nop(specifier)

    log('显示详细耗电数据')
    # Show battery usage data for all apps
    smali = apk.find_smali('"PowerRankHelperHolder"', '"getBatteryUsageStats"').pop()
    specifier = MethodSpecifier()
    specifier.access = MethodSpecifier.Access.PUBLIC
    specifier.is_static = True
    specifier.parameters = ''
    specifier.return_type = 'Z'
    specifier.keywords.add('sget-boolean')
    specifier.keywords.add('Lcom/miui/powercenter/legacypowerrank/')
    smali.method_return_boolean(specifier, False)

    # Show battery usage data for touchscreen
    specifier.access = MethodSpecifier.Access.PRIVATE
    smali.method_return_boolean(specifier, False)

    # Hide unknown battery usage data
    specifier.keywords.clear()
    specifier.keywords.add('"ishtar"')
    specifier.keywords.add('"nuwa"')
    specifier.keywords.add('"fuxi"')
    smali.method_return_boolean(specifier, True)

    log('禁用耗电项优化建议')
    smali = apk.find_smali('"key_show_battery_power_save_suggest"').pop()
    specifier = MethodSpecifier()
    specifier.is_static = True
    specifier.return_type = 'Z'
    specifier.keywords.add('"key_show_battery_power_save_suggest"')
    smali.method_return_boolean(specifier, False)

    log('禁用 Root 权限检查')
    smali = apk.find_smali('"key_check_item_root"').pop()
    specifier = MethodSpecifier()
    specifier.is_static = True
    specifier.return_type = 'Z'
    specifier.keywords.add('"key_check_item_root"')
    smali.method_return_boolean(specifier, False)

    log('去除危险操作倒计时确认')
    smali = apk.open_smali('com/miui/permcenter/privacymanager/model/InterceptBaseActivity.smali')
    specifier = MethodSpecifier()
    specifier.name = 'onCreate'
    specifier.parameters = 'Landroid/os/Bundle;'

    old_body = smali.find_method(specifier)
    lines = old_body.splitlines()
    locals_line = list(lines[1])
    if int(locals_line[-1]) < 2:
        locals_line[-1] = '2'
    lines[1] = ''.join(locals_line)
    new_body = '\n'.join(lines)

    pattern = '''\
    invoke-super {p0, p1}, Lmiuix/appcompat/app/AppCompatActivity;->onCreate\\(Landroid/os/Bundle;\\)V
'''
    repl = '''\\g<0>
    if-nez p1, :cond_114514

    new-instance v0, Landroid/os/Bundle;

    invoke-direct {v0}, Landroid/os/Bundle;-><init>()V

    move-object p1, v0

    :cond_114514

    const-string v0, "KET_STEP_COUNT"

    const/4 v1, 0x0

    invoke-virtual {p1, v0, v1}, Landroid/os/Bundle;->putInt(Ljava/lang/String;I)V

    const-string v0, "KEY_ALLOW_ENABLE"

    const/4 v1, 0x1

    invoke-virtual {p1, v0, v1}, Landroid/os/Bundle;->putBoolean(Ljava/lang/String;Z)V
'''
    new_body = re.sub(pattern, repl, new_body)
    smali.method_replace(old_body, new_body)

    apk.build()


@modified('system_ext/priv-app/AuthManager/AuthManager.apk')
def disable_sensitive_word_check():
    log('禁用设备名称敏感词检查')
    apk = ApkFile('system_ext/priv-app/AuthManager/AuthManager.apk')
    apk.decode()

    smali = apk.open_smali('com/miui/privacy/WNProvider.smali')
    specifier = MethodSpecifier()
    specifier.name = 'call'
    specifier.parameters = 'Ljava/lang/String;Ljava/lang/String;Landroid/os/Bundle;'
    specifier.return_type = 'Landroid/os/Bundle;'
    old_body = smali.find_method(specifier)
    new_body = '''\
.method public call(Ljava/lang/String;Ljava/lang/String;Landroid/os/Bundle;)Landroid/os/Bundle;
    .locals 4

    const/4 p2, 0x0

    if-eqz p3, :cond_0

    new-instance v0, Landroid/os/Bundle;

    invoke-direct {v0}, Landroid/os/Bundle;-><init>()V

    const-string v1, "key_state"

    const/4 v2, 0x0

    invoke-virtual {v0, v1, v2}, Landroid/os/Bundle;->putInt(Ljava/lang/String;I)V

    const-string v1, "key_has_ques"

    invoke-virtual {v0, v1, v2}, Landroid/os/Bundle;->putBoolean(Ljava/lang/String;Z)V

    invoke-static {p1}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I

    move-result v1

    if-nez v1, :cond_1

    return-object v0

    :cond_1
    const/4 v2, 0x1

    if-ne v1, v2, :cond_0

    invoke-static {}, Landroid/os/Message;->obtain()Landroid/os/Message;

    move-result-object v2

    invoke-virtual {v2, v0}, Landroid/os/Message;->setData(Landroid/os/Bundle;)V

    const-string v3, "callback"

    invoke-virtual {p3, v3}, Landroid/os/Bundle;->getParcelable(Ljava/lang/String;)Landroid/os/Parcelable;

    move-result-object v3

    check-cast v3, Landroid/os/Messenger;

    if-eqz v3, :cond_0

    :try_start_0
    invoke-virtual {v3, v2}, Landroid/os/Messenger;->send(Landroid/os/Message;)V
    :try_end_0
    .catch Landroid/os/RemoteException; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_0

    :catch_0
    move-exception p3

    :cond_0
    :goto_0
    return-object p2
.end method
'''
    smali.method_replace(old_body, new_body)

    apk.build()


@modified('product/app/MiTrustService/MiTrustService.apk')
def disable_mi_trust_service_mrm():
    log('禁用 Mrm 风险检测')
    apk = ApkFile('product/app/MiTrustService/MiTrustService.apk')
    apk.decode()

    smali = apk.open_smali('com/xiaomi/trustservice/remoteservice/eventhandle/statusEventHandle.smali')
    specifier = MethodSpecifier()
    specifier.name = 'initIMrmService'
    smali.method_return_boolean(specifier, False)

    apk.build()


@modified('product/app/MIUISuperMarket/MIUISuperMarket.apk')
def not_update_modified_app():
    log('不检查修改过的系统应用更新')
    apk = ApkFile('product/app/MIUISuperMarket/MIUISuperMarket.apk')
    apk.decode()

    smali = apk.open_smali('com/xiaomi/market/data/LocalAppManager.smali')
    specifier = MethodSpecifier()
    specifier.name = 'getUpdateInfoFromServer'
    old_body = smali.find_method(specifier)
    pattern = '''\
    invoke-direct/range {.+?}, Lcom/xiaomi/market/data/LocalAppManager;->loadInvalidSystemPackageList\\(\\)Ljava/util/List;

    move-result-object ([v|p]\\d+?)
'''
    repl = '''\\g<0>
    invoke-static {\\g<1>}, Lcom/xiaomi/market/data/HcInjector;->addModifiedPackages(Ljava/util/List;)V
'''
    new_body = re.sub(pattern, repl, old_body)
    smali.method_replace(old_body, new_body)

    # If the hccm (HyperCleaner Check Modified) file exists in the internal storage root directory, ignore adding packages
    smali.add_affiliated_smali(f'{MISC_DIR}/smali/IgnoreAppUpdate.smali', 'HcInjector.smali')
    smali = apk.open_smali('com/xiaomi/market/data/HcInjector.smali')
    specifier.name = 'addModifiedPackages'
    old_body = smali.find_method(specifier)
    output = io.StringIO()
    for package in config.MODIFY_PACKAGE:
        output.write(f'    const-string v1, "{package}"\n\n')
        output.write('    invoke-interface {p0, v1}, Ljava/util/List;->add(Ljava/lang/Object;)Z\n\n')
    new_body = string.Template(old_body).safe_substitute(var_modify_package=output.getvalue())
    smali.method_replace(old_body, new_body)

    apk.build()


def run_on_rom():
    rm_files()
    replace_analytics()
    patch_services()
    patch_miui_services()
    patch_package_installer()
    patch_theme_manager()
    patch_system_ui()
    remove_mms_ads()
    show_network_type_settings()
    patch_security_center()
    disable_sensitive_word_check()
    disable_mi_trust_service_mrm()
    not_update_modified_app()


def run_on_module():
    patch_package_installer()
    patch_theme_manager()
    patch_system_ui()
    remove_mms_ads()
    show_network_type_settings()
    patch_security_center()
    disable_sensitive_word_check()
    disable_mi_trust_service_mrm()
    not_update_modified_app()


# Unused Code ==================================================================================
# SecurityCenter
def disable_wifi_blocked_notification(apk_file: ApkFile):
    smali_file = apk_file.open_smali('com/miui/networkassistant/utils/NotificationUtil.smali')
    specifier = MethodSpecifier()
    specifier.name = 'sendWifiNetworkBlockedNotify'
    smali_file.method_nop(specifier)


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
