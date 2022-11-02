#!/bin/bash

function check_tool
{
    local tool=$1
    if [ "`command -v $tool 2> /dev/null`" == "" ]; then
        echo "Test tool $tool not found in current environment."
        exit 1
    fi
}

function progressbar
{
    local time=$1
    local msg=$2
    for i in `seq 1 $time`
    do
        local dot=.$dot
        if [ $(( $i % 4 )) -eq 0 ]; then
            printf "%80s\r" " "
            local dot=""
        fi
        local j=$(( $time - $i ))
        printf "%s\r" "Waiting ${j}s for ${msg}$dot" # | tee /dev/null
        sleep 1
    done
}

function clean_back_proc
{
    echo "Wait few seconds for background processes cleanup..."
    for e in iostat fio
    do
        local ps_num=`ps -ef | grep -v grep | awk '{print $8}' | grep -c $e`
        if [ $ps_num -ne 0 ]; then
            kill_ps $e
            sleep 5
        fi
    done
}

function kill_ps
{
    local key=$1
    until [ `ps -ef | awk '{print $8}' | grep -v grep | grep -c $key` -eq 0 ]
    do
        for e in `ps -ef | awk '{print $2 ":" $8}' | grep -v grep | grep $key`
        do
            p_id=`echo $e | awk -F\: '{print $1}' | tr -d ' '`
            p_name=`echo $e | awk -F\: '{print $2}' | tr -d ' '`
            kill -9 $p_id
        done
        sleep 1
    done
}

function get_os_disk
{
    local filter_rule=$1
    local tmp_letter=$2
    dev1=`df | grep -i /boot | awk '{print $1}' | grep -Eo $filter_rule | head -n1`
    dev2=`df | awk '{print $1 ":" $6}' | grep '/$' | grep -Eo $filter_rule`
    for dev in $dev1 $dev2
    do
        if [ "`blkid $dev`" != "" ]; then
            os_drive=$dev
            os_drive_letter=`basename $os_drive`
            return 0
        fi
    done
    if [ "$sys_mode" != "True" ]; then
        local tmp_letter=sda
    fi
    if [ "`blkid /dev/$tmp_letter`" == "" ]; then
        echo "Retrieve OS drive occurred unexpected error."
        exit 1
    fi
    os_drive=/dev/$tmp_letter
    os_drive_letter=$tmp_letter
}

function get_sd_disks
{
    grep -P 'sd\w+$' /proc/partitions 2> /dev/null \
         | grep -Pv '\d+$' \
         | grep -vE "usb|$os_drive_letter" \
         | awk '{print $NF}' \
         | sort -V
}

function get_nvme_disks
{
    grep -P 'nvme\w+$' /proc/partitions 2> /dev/null \
         | grep -Pv 'p\d+$' \
         | awk '{print $NF}' \
         | sort -V
}

function get_fio_ps
{
    local get_fio_ps=`ps -ef \
                         | grep -v grep \
                         | grep fio \
                         | awk '{print $8}' \
                         | grep -c ^fio`
    if [ `echo $get_fio_ps | grep -cE '^[0-9]+$'` -eq 0 ]; then
        echo "Retrieve fio process quantity occurred unexpected error."
        exit 1
    fi
    echo $get_fio_ps
}
