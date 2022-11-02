#!/bin/bash

function nic_summary
{
    local cycle_num=$1
    local nic_log_path=$2
    local driver_version=$3
    local nic=$4
    local driver_result=$5
    local nic_counts=$6
    local host=$(hostname | awk -F '.' '{print $1}')

    # output summary result
    more << EOF > ${nic_log_path}/summary_${host}_${cycle_num}_${nic}.log
===========================================

Time: $(date "+%F_%T")
Count: $cycle_num times check
Ethernet card: $nic
BDF: ${BDF}

===========================================
Summary:

Driver version: ${driver_result}
Nic counts: ${nic_counts}
EOF
}

function nic_mac_check
{
    if [ $cycle_num -eq 0 ]; then
        condition="old"
    else
        condition="new"
    fi
    for i in `ls /sys/class/net/ | grep -Ev 'docker|lo|virbr'`
    do
        cd /sys/class/net/$i
        cat uevent | grep "INTERFACE"
        cat address
    done > $sys_log_path/${condition}_mac.log
    compare_log "nic mac addr" $sys_log_path mac.log $summary_log
}

function nic_check
{
    ping_test
    nic_log_path=$nic_log_path
    local nic_info=$(lspci | grep -ci 'ethernet')
    local nic_dev=$(ls /sys/class/net | egrep -v "lo|virbr0|docker")
    local host=$(hostname | awk -F '.' '{print $1}')
    if [ $cycle_num -eq 0 ]; then
        if [ "$(command -v ethtool)" != "" ]; then
            for nic in $nic_dev
            do
                ethtool -i $nic | tee ${nic_log_path}/origin_${nic}.log
            done
            echo $nic_info | tee ${nic_log_path}/origin_nic_count.log
        else
            echo "cmd: ethtool not found.\n"
            exit 1
        fi
    fi
    nic_mac_check
    if [ $cycle_num -gt 0 ]; then
        local nic_count=$(cat $nic_log_path/origin_nic_count.log)

        for nic in $nic_dev
        do
            local driver_num_origin=$(cat $nic_log_path/origin_${nic}.log \
                                      | egrep '^bus-info' \
                                      | awk -F '0000:' '{print $2}')
            ethtool -i $nic | tee ${nic_log_path}/${host}_${cycle_num}_${nic}.log
            local driver_num=$(cat ${nic_log_path}/${host}_${cycle_num}_${nic}.log \
                               | egrep '^bus-info' \
                               | awk -F '0000:' '{print $2}')
            if [ "$driver_num" == "$driver_num_origin" ]; then
                local driver_result="PASS"
            else
                local driver_result="FAIL"
            fi
            if [ "$nic_info" == "$nic_count" ]; then
                local nic_count_result="PASS"
            else
                local nic_count_result="FAIL"
            fi
            nic_summary $cycle_num $nic_log_path $driver_num $nic $driver_result $nic_count_result

            # append netcard driver detect result
            if [ "$driver_result" == "FAIL" ]; then
                sum_msg $summary_fail_log "$(log_ti) $nic driver check $driver_result"
                sum_msg $summary_log "$(log_ti) $nic driver check $driver_result"
            else
                sum_msg $summary_log "$(log_ti) $nic driver check $driver_result"
            fi

            # append netcard check result
            if [ "$nic_count_result" == "FAIL" ]; then
                sum_msg $summary_fail_log "$(log_ti) $nic info check $nic_count_result"
                sum_msg $summary_log "$(log_ti) $nic info check $nic_count_result"
            else
                sum_msg $summary_log "$(log_ti) info check $nic_count_result"
            fi
        done
    fi
    chk_vendor
    chk_nic_error_register
}

function ping_test
{
    if [ -n "$ping_ip" ]; then
	    for ip in $ping_ip
    	do
	        split_line $nic_log_path/ping.log "NO. $cycle_num $(date +%F_%T) $nic ping test"
	        ping -c 3  $ip >> $nic_log_path/ping.log 2>&1
	        if [ $? -ne 0 ]; then
	            sum_msg $summary_log "$(log_ti) ping $ip FAIL"
	        else
	            sum_msg $summary_log "$(log_ti) ping $ip PASS"
	        fi
		done
    fi
}

# This function check vendor and network card's speed in each cycle
function chk_vendor
{
    local vendor_info=`lspci | grep -i Ethernet \
                       | awk -F "Ethernet controller:" '{print $1, ":", $2}'`
    generate_log -m "$vendor_info" \
                 -p $nic_log_path \
                 -f vendor_info.log \
                 -ff vendor_info_full.log
    split_line $nic_log_path/vendor_info_full.log "NIC Vendor info Collection"
    compare_log "NIC Vendor info" $nic_log_path vendor_info.log $summary_log

    # network card speed check
    for BDF in `ls /sys/class/net | egrep -v "lo|virbr0|docker"`
    do
        local speed_info=`ethtool $BDF | grep -iE "Speed:|Duplex:|link detected:"`
        generate_log -m "$speed_info" \
                     -p $nic_log_path \
                     -f ${BDF}_speed.log \
                     -ff ${BDF}_speed_full.log
        split_line $nic_log_path/${BDF}_speed_full.log "${BDF} Speed Collection"
        compare_log "${BDF} Speed" $nic_log_path ${BDF}_speed.log $summary_log
    done
}

function chk_nic_error_register
{
    nic_log_path=$nic_log_path
    if [ $cycle_num -eq 0 ]; then
        ifconfig -a > ${nic_log_path}/ifconfig_old.log

    else
        ifconfig -a > ${nic_log_path}/ifconfig_new.log
        mesg="===== $cycle_num cycle ======="
        echo $mesg >> ${nic_log_path}/ifconfig_full.log
        cat ${nic_log_path}/ifconfig_new.log >>  ${nic_log_path}/ifconfig_full.log
        new_ifconfig=`cat ${nic_log_path}/ifconfig_new.log |grep -iE "tx errors|rx errors"`
        old_ifconfig=`cat ${nic_log_path}/ifconfig_old.log |grep -iE "tx errors|rx errors"`
        if [ "$new_ifconfig" == "$old_ifconfig" ]; then
            sum_msg $summary_log "$(log_ti) check nic ifconfig PASS"
        else
            fail_msg="$(log_ti) check nic ifconfig FAIL"
            sum_msg $summary_log "$(log_ti) check nic ifconfig FAIL"
            sum_msg $summary_fail_log "$fail_msg"
        fi
     fi
}
