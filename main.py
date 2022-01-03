from build import ApkFile
from build.method_specifier import MethodSpecifier
from util import AdbUtils


def delete_rubbish():
    def ignore_annotation(line: str):
        annotation_index = line.find('#')
        return line[:annotation_index].strip()

    model = AdbUtils.exec_with_result('getprop ro.product.name')[:-1]
    print('>>> Delete rubbish files, device: %s' % model)

    with open('rubbish-files-%s.txt' % model) as file:
        for rubbish in map(ignore_annotation, file.readlines()):
            if len(rubbish) != 0:
                print('Deleting %s' % rubbish)
                # AdbUtils.exec_as_root('rm -rf %s' % rubbish)


def main():
    test_file = ApkFile('tmp/MIUISecurityCenter.apk')
    test_file.decode()
    smali_file = test_file.open_smali('com/miui/wakepath/ui/ConfirmStartActivity.smali')

    method = MethodSpecifier()
    method.access = MethodSpecifier.Access.PROTECTED
    # method.is_static = True
    # method.name = 'initPreferenceView'
    # method.parameters = 'Landroid/content/Intent;Ljava/lang/String;I'
    # method.return_type = 'V'
    method.keywords.append('"android.intent.action.PICK"')
    print(smali_file.find_method(method))
    # test_file.build()


if __name__ == '__main__':
    main()
