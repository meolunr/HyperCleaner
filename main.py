from build import ApkFile


def main():
    test_file = ApkFile('MIUISecurityCenter.apk')
    test_file.decode()


if __name__ == '__main__':
    main()
