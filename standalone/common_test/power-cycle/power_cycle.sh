#!/bin/bash

# Swich to main script path
rm -rf /root/power_cycle_end_flag.log > /dev/null
main_path=$(cd `dirname $0` && pwd)
cd $main_path

# load modules
chmod +x libs/*
source libs/global_env.sh
source libs/argument.sh
source libs/start_reboot.sh
source libs/common.sh
source libs/fio_disk.sh
source libs/pci_chk.sh
source libs/nic_chk.sh
source libs/system_info.sh
source libs/sdr_chk.sh
source libs/disk_chk.sh
source libs/log_chk.sh
source libs/black_white.sh

# Argument Parser
## Judge if raw cycle
main_args="$@"
arg_num=$#
if [ $arg_num == 0 ]; then
    raw_cycle=False
else
    raw_cycle=True
fi

if [ $raw_cycle == True ]; then
    clearenv
    source libs/global_var.sh
	chmod 777 /etc/rc.d/rc.local
    arg_parse "$@"
    if [ $interact_mode == True ]; then
    interact_test
    fi
else
    sleep 20
    source libs/set_env.sh
fi


# Test Start
## Prepare test env
pre_env

## lspci check
lspci_check
## System info check, include: FRU/SMBIOS/MEMSIZE/CPUINFO
system_check

#save bmc serial log 
if [[ $serial_mode = True ]]; then
        get_serial_log
fi


## mce log check
#mce_check

## Net NIC Check
nic_check

## SDR info check
sdr_check

## Disk info check
disk_check

## Run fio
start_fio

## check sel/dmesg/messge logs
sys_log_check

## reboot
start_reboot
