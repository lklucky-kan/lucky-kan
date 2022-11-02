#!/bin/bash


# Init global variable
color_ye="\033[33m"
color_raw="\033[0m"
color_ge="\033[32m"
color_re="\033[31m"
os_drive=`df | grep -i /boot \
             | awk '{print $1}' \
             | awk  -F/ '{print $3}' \
             | grep -Po "sd[a-z]+|nvme\d+n\d+" \
             | uniq`
fio_path=`command -v fio`
reboot_script=$main_path/power_cycle.sh
bootloader='/etc/rc.d/rc.local'
splitline="====================================================================================="
