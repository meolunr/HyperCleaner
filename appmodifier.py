import os

from util import AdbUtils


def rm_files():
    # TODO: Placeholder
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

    with open(rubbish_file_list, encoding='utf-8') as file:
        for rubbish in map(ignore_annotation, file.readlines()):
            if len(rubbish) != 0:
                print('Deleting %s' % rubbish)
                AdbUtils.exec_as_root('rm -rf %s' % rubbish)


def run():
    rm_files()
