#!/bin/bash

#**************************************************************************************#
# ScriptName: driver_load_unload.sh
# Description: repeatedly loading and unloading drivers tool
# Author: Ben
# Create Date: 2021.08.03
# Modify Date: 2021.11.12
# Version: 2.0
#**************************************************************************************#

set -e
ping_num=4
green="\033[32m"
red="\033[31m"
# yellow="\033[33;1m"
off="\033[0m"
tools="dhclient ethtool rmmod lsmod modprobe dmesg ifconfig ipmitool"

function usage() {
    more <<EOF
    ************************************************************************************
    -h|--help  cat help info
    -rt        loading and unlaoding number of times
    -c         set count ECHO_REQUEST packets, default set 4
    -ip incoming parameters the same network segment Server status IP address eg: Single IP: 10.10.10.10 Multiple IP: "10.10.10.10 20.20.20.20"
    ************************************************************************************
    Example: 
    $0 -rt 500 -ip "10.10.10.10 20.20.20.20"
    $0 -rt 500 -ip "10.10.10.10 20.20.20.20"-c 5
    ************************************************************************************
EOF
    exit 0
}

#=============================================================================
# Function Name: delete_file
# Description  : delete  files
# Parameter    : files name
# Returns      : none
#=============================================================================
function delete_file {
    for file in "$@"; do
        if [ -f "$file" ]; then
            rm -rf "$file"
        fi
    done
}

#=============================================================================
# Function Name: ping_ip
# Description  : test single ip network connect
# Parameter    : remote ip/ECHO_REQUEST packets nums/local nic address
# Returns      : none
#=============================================================================
function ping_ip {
    ping -c "$2" -I "$3" "$1" >ping_"$3"
    num=$(grep "$2 packets" ping_"$3" | awk '{print $4}')
    cat ping_"$3" >>ping_nic.log
    rm -rf ping_"$3"
    if [ "$num" != "$2" ]; then
        echo -e "$red network cannot connect, pls check it.$off"
        exit 1
    fi
}

#=============================================================================
# Function Name: mul_ip_ping
# Description  : test multiply ip network connect
# Parameter    : multiply ip
# Returns      : none
#=============================================================================
function mul_ip_ping {
    array=($1)
    for ip in ${array[@]}; do
        net_seg=$(echo $ip | awk '{match($0,"(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){2}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])",a)}{print a[0]}')
        nic_dev=$(ifconfig | grep -B1 "$net_seg" | grep -v "$net_seg" | awk -F ":" '{print $1}')
        ping_ip "$ip" $ping_num "$nic_dev"
    done
}


function dhclient_leases_file_path_chk {
    # check whether the OS is centos  redhat or euleros
    if grep -iE 'centos|redhat|euleros' /proc/version; then
        dhclient_leases_file_path="/var/lib/dhclient/dhclient.leases"
        delete_file $dhclient_leases_file_path
    else
        # check whether the OS is ubuntu or debian
        if grep -iE 'ubuntu|debian' /proc/version; then
            dhclient_leases_file_path="/var/lib/dhcp/dhclient.leases"
            delete_file $dhclient_leases_file_path
        else
            echo -e "$red can not find os version, please contact author.$off"
            exit 1
        fi
    fi
    dhclient -r
    dhclient
}

#=============================================================================
# Function Name: driver_loading_unloading
# Description  : loading and unloading drivers repeatedly
# Parameter    : Number of times of loading and unloading drivers repeatedly
# Returns      : none
#=============================================================================
function driver_loading_unloading {
    for ((i = 1; i <= $1; i++)); do
        echo -e "$green driver loading unloading $i time. $off"
        driver_name=$(ethtool -i "$nic_dev" | grep driver | awk -F ': ' '{print $2}')
        #4.卸载网卡driver依赖卸载网卡对应驱动
        ret="$(lsmod | grep "^$driver_name" | awk '{print $3}')"
        if [ "$ret" == "0" ]; then
            rmmod "$driver_name"
        elif [ "$ret" == "1" ]; then
            d2=$(lsmod | grep "^$driver_name" | awk '{print $4}')
            rmmod "$d2"
            sleep 10
            rmmod "$driver_name"
        else
            for i in $(lsmod | grep "^$driver_name" | awk '{print $4}' | tr ',' ' '); do
                ret=$(lsmod | grep "^$driver_name" | awk '{print $3}')
                if [ "$ret" == 0 ]; then
                    rmmod "$i"
                    sleep 10
                else
                    echo -e "$red Too many driver dependencies, please contact the author.$off"

                    exit 1
                fi
            done
            rmmod "$driver_name"
        fi
        # 5.加载卸载驱动脚本中加入睡眠时间
        sleep 10
        # 6.加载网卡对应驱动
        modprobe "$driver_name"
        sleep 10
        # 7.检测dmesg 信息 端口数量
        if dmesg | grep -iE "error|fail|warn|wrong|bug|respond|pending" >dmesg.log; then
            echo -e "$red dmesg error please check it.$off" | tee -a dmesg.log
            exit 1
        fi
        num=$(ifconfig -a | grep -vE 'lo|br|bond|vnet|vtap|docker' | grep -c mtu)
        echo "$date driver loading unloading $i time. lan card num: $num." >>nic-port-num.log
        nic_bus_id=$(lspci | grep -i eth | awk '{print $1}' | tr "\n" " " | awk '$1=$1')
        if [ ! -f "$nic_bus_id" ]; then
            for j in $nic_bus_id; do
                echo "$date driver loading unloading $i time. $j LnkCap LnkSta." >>lspci_width.log
                lspci -vvvxxx -s "$j" | grep -i width >>lspci_width.log
            done
        fi
    done
}

#=============================================================================
# Function Name: before_test_clear_env
# Description  : initialize the test environment
# Parameter    : none
# Returns      : none
#=============================================================================
function before_test_clear_env {
    # 删除之前测试生成文件
    delete_file ping_nic.log dmesg.log driver.log lspci_width.log nic-port-num.log messages log sel.log sdr.log
    # 确认测试工具是否都存在
    for tool in $tools; do
        if ! command -v "$tool"; then
            echo -e "$red cmd: $tool not found.$off"
            exit 1
        fi
    done
    # 记录系统下识别的网卡端口数量   清除日志
    dmesg -c >/dev/null 2>&1
    cat /dev/null >/var/log/messages
    num=$(ifconfig -a | grep -vE 'lo|br|bond|vnet|vtap|docker' | grep -c mtu)
    echo "$date before driver loading unloading lan card num: $num." >>nic-port-num.log
    nic_bus_id=$(lspci | grep -i eth | awk '{print $1}' | tr "\n" " " | awk '$1=$1')
    if [ ! -f "$nic_bus_id" ]; then
        for j in $nic_bus_id; do
            echo "$date before driver loading unloading lan card $j LnkCap LnkSta." >>lspci_width.log
            lspci -vvvxxx -s "$j" | grep -i width >>lspci_width.log
        done
    fi
}

#=============================================================================
# Function Name: after_test_collect_message
# Description  : collecting logs after test finish
# Parameter    : none
# Returns      : none
#=============================================================================
function after_test_collect_message {
    dmesg >dmesg.log
    cp /var/log/messages messages.log
    ipmitool sdr elist >sdr.log
    ipmitool sel elist >sel.log
}

function main {
    if [ ! -f "$static_ip" ]; then
        before_test_clear_env
        mul_ip_ping "$static_ip"
        driver_loading_unloading $run_times
        sleep 10
        mul_ip_ping "$static_ip"
        after_test_collect_message
    else
        echo -e "$red please input static_ip.$off"
        exit 1
    fi
}

if [ "$#" -eq 0 ]; then
    echo "Invalid arguments, try '-h/--help' for more information."
    exit 1
fi
while [ "$1" != "" ]; do
    case $1 in
    -h | --help)
        usage
        ;;
    -rt | --run_times)
        shift
        run_times=$1
        ;;
    -c | --count)
        shift
        ping_num=$1
        ;;
    -ip)
        shift
        static_ip=$1
        ;;
    *)
        echo "Invalid arguments, try '-h/--help' for more information."
        exit 1
        ;;
    esac
    shift
done

main
