SUPER_SIZE = 9126805504
SUPER_PARTITIONS = ('mi_ext', 'odm', 'product', 'system', 'system_dlkm', 'system_ext', 'vendor', 'vendor_dlkm')
MODIFY_PACKAGE = (
    'com.miui.packageinstaller',
    'com.android.thememanager'
)

unpack_partitions = {'product', 'system', 'system_ext', 'vendor'}
remove_data_apps: set[str] = set()
device: str
version: str
sdk: int
