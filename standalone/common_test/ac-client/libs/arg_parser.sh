#!/bin/bash

# Argument Parser
function arg_parse
{
    argvs=$@
    if [ "$#" -eq 0 ]; then
        Usage
        exit 1
    fi
    while [ "$1" != "" ]
    do
        case $1 in
            -h|--help)
                Usage;;
            -i|--ini)
                shift
                config_file=$1;;
            * ) echo "Invalid arguments, Please try '-h/--help' for more infomation"
                exit 1;;
        esac
        shift
    done
}

function Usage
{
    more << EOF
Usage: `basename $0` Arguments:
      -h  get 
      -i  Define Run AC .ini config file

Test Example:
    $0 -i sample.ini
EOF
    exit 1
}

function show_config
{
    more << EOF
############################################
######        AC Run Arguments        ######
############################################

 - Summary:
    - AC Total Cycles: $total_cycle
    - AC Boot Delay: $boot_delay

 - BMC Args:
    - BMC IP: $BMC_IP
    - BMC Username: $bmc_user
    - BMC Password: $bmc_pwd
    - BMC Interface: $bmc_interface
    - BMC Up Time: $bmc_up_time
    - BMC Up Retry Times: $bmc_up_retry_times
    - BMC Up Retry Interval: $bmc_up_retry_interval
    - BMC Auto Bootup: $bmc_auto_poweron

 - PDU:
    - PDU IP: $PDU_IP
    - PDU Username: $pdu_user
    - PDU Password: $pdu_pwd
    - PDU Off Delay: $pdu_off_delay
    - PDU RPC Ports: $PDU_Ports

 - Advance:
    - BMC Auto Poweron: $bmc_auto_poweron
    - BMC Sel Event Retry Times: $sel_event_retry_times
    - BMC Sel Event Retry Interval: $bmc_up_retry_interval
EOF
}

function quebec_show_config
{
    more << EOF
############################################
######        AC Run Arguments        ######
############################################

 - Summary:
    - AC Total Cycles: $total_cycle
    - AC Boot Delay: $boot_delay

 - Server BMC Args:
    - BMC IP: $server_bmc_ip
    - BMC Username: $server_bmc_user
    - BMC Password: $server_bmc_pwd
    - BMC Interface: $server_bmc_lanplus
 - GPU BOX BMC Args:
    - BMC IP: $GPU_BOX_bmc_ip
    - BMC Username: $GPU_BOX_bmc_user
    - BMC Password: $GPU_BOX_bmc_pwd
    - BMC Interface: $GPU_BOX_bmc_lanplus
 - BMC Common Args:
    - BMC Up Time: $bmc_up_time
    - BMC Up Retry Times: $bmc_up_retry_times
    - BMC Up Retry Interval: $bmc_up_retry_interval
    - BMC Auto Bootup: $bmc_auto_poweron

 - PDU Common Args:
    - PDU IP: $PDU_IP
    - PDU Username: $pdu_user
    - PDU Password: $pdu_pwd
    - PDU Off Delay: $pdu_off_delay
 - Server PDU:
    - PDU RPC Ports: $server_pdu_port
 - GPU BOX PDU Args:
    - PDU RPC Ports: $GPU_BOX_pdu_port


 - Advance:
    - BMC Auto Poweron: $bmc_auto_poweron
    - BMC Sel Event Retry Times: $sel_event_retry_times
    - BMC Sel Event Retry Interval: $bmc_up_retry_interval
EOF
}

function vars_check
{
    # PDU IP Check
    local sum_res=pass
    res=`ping_test "$PDU_IP"`
    if [ $res == 'fail' ]; then
        echo -e "PDU IP: $PDU_IP can't ping"
        sum_res=fail
    else
        echo -e "PDU IP: $PDU_IP can normal ping"
    fi

    bmc_chk_cmd="ipmitool -U $bmc_user -P $bmc_pwd -I $bmc_interface -H $BMC_IP raw 6 1"
    $bmc_chk_cmd
    if [ $? -ne 0 ]; then
        echo -e "BMC IP $BMC_IP not up, please use cmd:\n    $bmc_chk_cmd\n to check"
        sum_res=fail
    else
        echo -e "BMC IP $BMC_IP is up"
    fi
    if [ $sum_res == 'fail' ]; then
        echo -e '\n'
        showfail
        exit 1
    fi
}

function args_check
{
    local sum_res=pass
    pdu_check $PDU_IP
    if [ $? -ne 0 ]; then
        sum_res=fail
    fi

    bmc_check $server_bmc_lanplus $server_bmc_ip $server_bmc_user $server_bmc_pwd
    if [ $? -ne 0 ]; then
        sum_res=fail
    fi

    bmc_check $GPU_BOX_bmc_lanplus $GPU_BOX_bmc_ip $GPU_BOX_bmc_user $GPU_BOX_bmc_pwd
    if [ $? -ne 0 ]; then
        sum_res=fail
    fi

    if [ $sum_res == 'fail' ]; then
        echo -e '\n'
        showfail
        exit 1
    fi

}

function pdu_check
{
    local pdu_ip=$1
    res=`ping_test "$pdu_ip"`
    if [ $res == 'fail' ]; then
        echo -e "PDU IP: $pdu_ip can't ping"
        return 1
    else
        echo -e "PDU IP: $pdu_ip can normal ping"
        return 0
    fi
}

function bmc_check
{   
    local b_interface=$1
    local b_ip=$2
    local b_user=$3
    local b_pwd=$4

    bmc_chk_cmd="ipmitool -U $b_user -P $b_pwd -I $b_interface -H $b_ip raw 6 1"
    $bmc_chk_cmd
    if [ $? -ne 0 ]; then
        echo -e "BMC IP $b_ip not up, please use cmd:\n    $bmc_chk_cmd\n to check"
        return 1
    else
        echo -e "BMC IP $b_ip is up"
        return 0
    fi
}