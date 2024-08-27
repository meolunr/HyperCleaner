SUPER_SIZE = 9126805504
SUPER_PARTITIONS = ('mi_ext', 'odm', 'product', 'system', 'system_dlkm', 'system_ext', 'vendor', 'vendor_dlkm')
MODIFY_PACKAGE = (
    'com.miui.packageinstaller',
    'com.android.thememanager',
    'com.android.systemui',
    'com.android.mms',
    'com.android.phone',
    'com.miui.securitycenter',
    'com.lbe.security.miui',
    'com.xiaomi.market'
)

unpack_partitions = {'product', 'system', 'system_ext', 'vendor'}
device: str
version: str
sdk: int
