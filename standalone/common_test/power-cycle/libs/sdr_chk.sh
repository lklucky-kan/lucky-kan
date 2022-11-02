#!/bin/bash


function sdr_check
{
    # 当 SDR 需要时间才能 Ready 的时候， 需要增加该等待时间
    sleep ${sdr_delay}m
    local sdr_msg=`ipmitool sdr elist`
    local sdr_log=${sdr_log_path}/sum_sdr.log
    local error_count=$(echo "$sdr_msg" \
                        | awk -F\| '{print $3}' \
                        | sed -E 's,^\s+|\s+$,,g' \
                        | egrep -cvi 'ns|ok')

    split_line ${sdr_log_path}/sdr_elist_full.log "sdr elist info collect"
    echo "$sdr_msg" >> ${sdr_log_path}/sdr_elist_full.log

    if [ $cycle_num -eq 0 ]; then
        echo "$sdr_msg" | awk -F\| '{print $1 " : " $3}' | tee ${sdr_log_path}/sdr_first.log
        if [ $(egrep -cvi "ok|ns" ${sdr_log_path}/sdr_first.log) -ne 0 ]; then
           echo "There is other SDR status fail expect ok&ns, Please check log in ${sdr_log_path}/sdr_first.log"
           CheckResume
        fi
	else
		echo "$sdr_msg" | awk -F\| '{print $1 " : " $3}' | tee ${sdr_log_path}/sdr_latest.log
        if [ -n "$(diff -b ${sdr_log_path}/sdr_latest.log ${sdr_log_path}/sdr_first.log)" \
             -o $error_count -ne 0 ]; then
            local result='FAIL'
            local after_msg=$(diff -b ${sdr_log_path}/sdr_latest.log ${sdr_log_path}/sdr_first.log \
                             | sed -n '/:/p' \
                             | sed -n '/</p' \
                             | sed -E 's,^<,,g' \
                             | sed -E 's,^\s+|\s+$,,g')
            local before_msg=$(diff -b ${sdr_log_path}/sdr_latest.log ${sdr_log_path}/sdr_first.log \
                              | sed -n '/:/p' \
                              | sed -n '/>/p' \
                              | sed -E 's,^>,,g' \
                              | sed -E 's,^\s+|\s+$,,g')
            echo "$sdr_msg" | tee $fail_log_path/sdr_${cycle_num}.log
        else
            local result='PASS'
        fi


        if [ "$result" == "FAIL" ]; then
            sum_msg $summary_fail_log "$(log_ti) sdr check FAIL"
            sum_msg $summary_log "$(log_ti) sdr check FAIL"
            CheckResume
        else
        	sum_msg $summary_log "$(log_ti) sdr check PASS"
		fi
    fi
}
