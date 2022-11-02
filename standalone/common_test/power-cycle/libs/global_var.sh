#!/bin/bash


# 初始化全局可变变量
cycle_mode=None
fio_mode=False
assumeyes=True
ping_ip=""

# 执行fio相关参数
fio_args="--end_fsync=0 \
    --group_reporting \
    --direct=1 \
    --ioengine=libaio \
    --time_based  \
    --invalidate=1 \
    --norandommap \
    --randrepeat=0 \
    --exitall \
    --size=100% \
    --readwrite=randrw \
    --rwmixread=70 \
    --bs=4k \
    --numjobs=1 \
    --runtime=1200s"
fio_dev_args=""
fio_para=""
lspci_raw_num=$(lspci | wc -l)
interact_mode=False
