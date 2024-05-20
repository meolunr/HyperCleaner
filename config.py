from util import imgfile

SUPER_SIZE = 9126805504
SUPER_PARTITIONS = ('mi_ext', 'odm', 'product', 'system', 'system_dlkm', 'system_ext', 'vendor', 'vendor_dlkm')

unpack_partitions = {
    'product': imgfile.FS_TYPE_UNKNOWN,
    'system': imgfile.FS_TYPE_UNKNOWN,
    'system_ext': imgfile.FS_TYPE_UNKNOWN,
    'vendor': imgfile.FS_TYPE_UNKNOWN
}
device = ''
version = ''
sdk = 0
