MODDIR=${0%/*}

rm -f $0
mv $MODDIR/post-fs-data.sh.bak $MODDIR/post-fs-data.sh
. $MODDIR/post-fs-data.sh

