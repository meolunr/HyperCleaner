SUPER_SIZE = 9126805504
SUPER_PARTITIONS = ('mi_ext', 'odm', 'product', 'system', 'system_dlkm', 'system_ext', 'vendor', 'vendor_dlkm')
MODIFY_PACKAGE = (
    'com.miui.packageinstaller'
)

unpack_partitions = dict.fromkeys((
    'product', 'system', 'system_ext', 'vendor'
), None)
remove_data_apps: set[str] = set()
device = ''
version = ''
sdk = 0
