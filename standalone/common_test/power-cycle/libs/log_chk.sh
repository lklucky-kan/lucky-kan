#!/bin/bash

function chk_log
{
    local logtype=$1
    local log_path=$result_path/${logtype}_log
    local log_file=$log_path/${logtype}.log
    local fail_log=$log_path/${logtype}_fail.log

    if [ -f $fail_log ]; then
        rm -rf $fail_log
    fi
    black_white_list $logtype
    case $logtype in
        sel)
            chk_sel $log_file $fail_log;;
        dmesg)
            check_dmesg $log_file $fail_log;;
        messages)
            check_messages $fail_log;;
        *)
            echo "log can not parse";;
    esac
    if [ -f $fail_log ]; then
        cat $fail_log | sort | uniq | tee $fail_log
    fi
    if [ `cat $fail_log 2>/dev/null | grep -v "^# *" |wc -l` -ne 0 ]; then
        sum_log $summary_log "$logtype log check FAIL, refer $fail_log_path/${logtype}_error_full.log for detail"
        sum_log $summary_fail_log "$logtype log check FAIL, refer $fail_log_path/${logtype}_error_full.log for detail"
        split_line $fail_log_path/${logtype}_error_full.log "$logtype check fail"
        sum_msg $fail_log_path/${logtype}_error_full.log "`cat $fail_log`"
        CheckResume
    else
        sum_log $summary_log "$logtype log check PASS"
    fi
    if [ "$cycle_mode" != "ac" ]; then
        ipmitool sel clear &> /dev/null
        sleep 5
    fi
}

function chk_sel
{
    local logfile=$1
    local faillog=$2
    for item in "${black_list[@]}"
    do
        grep -ir "${item}" $logfile &> /dev/null
        if [ $? -eq 0 ]; then
            white_head_all=""
            for white_item in "${white_list[@]}"
            do
                white_head=`echo "$white_item" | awk -F "|" '{print $1}'`
                white_tail=`echo "$white_item" | awk -F "|" '{print $2}'`
                white_head_all="$white_head_all $white_head"
                if [ "$white_head"x = "$item"x ]; then
                    grep -ir "${item}" $logfile | grep -iv "${white_tail}" &> /dev/null
                    if [ $? -eq 0 ]; then
                        grep -ir "${item}" $logfile | grep -iv "${white_tail}" >> $faillog
                    fi
                fi
            done
            echo "$white_head_all" | grep -io "$item" &> /dev/null
            if [ $? -eq 1 ]; then
                grep -ir "${item}" $logfile >>  $faillog
            fi
        fi
    done
}

function check_dmesg
{
    local logfile=$1
    local faillog=$2
    for item in "${black_list[@]}"
    do
        grep -ir " ${item}" $logfile &> /dev/null
        if [ $? -eq 0 ]; then
            grep -ir " ${item}" $logfile | while read line
            do
                local white_num=0
                for white_item in "${white_list[@]}"
                do
                    if echo "$line" | grep -ic "$white_item" &> /dev/null; then
                        white_num=$(( $white_num + 1 ))
                    fi
                done
                if [ $white_num -eq 0 ]; then
                    echo "$line" >> $faillog
                fi
            done
        fi
    done
}

function check_messages
{
    local faillog=$1
    for log in /var/log/messages*
    do
        for blk in "${black_list[@]}"
        do
            blk_line=`grep -ia "$blk" $log`
            if [ "$blk_line" ]; then
                echo -e "# ====== $log ======" >> $faillog
                echo -e "$blk_line" >> $faillog
            fi
        done
    done
    if [ -f $faillog ]; then
        for wht in "${white_list[@]}"
        do
            sed  -i "/$wht/d" $faillog
        done
        sed -i '/^\s*$/d' $faillog
    fi
    cp -r /var/log/messages* $msg_log_path/
}


function log_collect
{
    local sel_name=$1
    local cmd=$2
    local log_file=$3
    local full_log_file=$4
    local log_path=$5
    split_line $log_path/$full_log_file "$sel_name"
    $cmd | tee $log_path/$log_file
    $cmd | tee -a $log_path/$full_log_file
}

function sel_log_save
{
    log_collect "sel list collect" \
                "ipmitool sel list" \
                sel.log \
                sel_full.log \
                $sel_log_path
    log_collect "sel vlist collect" \
                "ipmitool sel list -vvv" \
                sel_vlist.log \
                sel_vlist_full.log \
                $sel_log_path
    log_collect "sel elist collect" \
                "ipmitool sel elist" \
                sel_elist.log \
                sel_elist_full.log \
                $sel_log_path
    ipmitool sel save $sel_log_path/sel_save.log
    sum_msg $sel_log_path/sel_save_full.log \
            "`cat $sel_log_path/sel_save.log`"
    sleep 3
}

function dmesg_log_save
{
    log_collect "dmesg info collect" \
                "dmesg" \
                dmesg.log \
                dmesg_full.log \
                $dmesg_log_path
    sleep 3
}

function log_check
{
    local logtype=$1
    case $logtype in
        sel)
            sel_log_save
            chk_log 'sel';;
        dmesg)
            dmesg_log_save
            chk_log 'dmesg';;
        messages)
            chk_log 'messages';;
    esac
}

function sys_log_check
{
    log_check 'sel'
    log_check 'dmesg'
}

function mce_check
{
    local  faillog=$result_path/fail_log/mce_fail.log
    local  status=True
    for log in /var/log/mce*
        do
            errorinfo=`cat $log`
            if [ "$errorinfo" ]; then
                echo -e "# ====== $log ======" >> $faillog
                echo -e "# ====== $cycle_num cycle ======" >> $faillog
                echo -e "$errorinfo" >> $faillog
                status=False
            fi
        done
    if [ $status == True ]; then
        sum_msg $summary_log "$(log_ti) check MCE log PASS"
     else
        fail_msg="$(log_ti) check MCE log FAIL"
        sum_msg $summary_log "$(log_ti) check MCE log FAIL"
        sum_msg $summary_fail_log "$fail_msg"
     fi

}

