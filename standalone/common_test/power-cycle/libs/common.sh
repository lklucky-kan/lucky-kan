#!/bin/bash

function log_ti
{
    echo "NO. $cycle_num $(ctime)"
}

function ctime
{
    echo "$(date +%F_%T)"
}

function clearenv
{
    # clear crach
    rm -rf /var/crash/*
    # clear message log
    rm -rf /var/log/messages*
    echo > /var/log/messages
}

function create_path
{
    for path in $@
    do
        if [ ! -d $path ]; then
            mkdir -p $path
        else
            rm -rf $path/*
        fi
    done
}

function cycle_num_count
{
    if [ ! -f $count_file ]; then
        echo 0 > $count_file
        cycle_num=0
    else
        local old_cycle_num=`cat $count_file`
        cycle_num=$(( $old_cycle_num + 1 ))
        echo $cycle_num > $count_file
    fi
}

function pre_env
{
	cycle_num_count
	if [ $cycle_num -eq 0 ]; then
		gene_env_set
		gene_stop_cycle
		echo "================ Starting $total_cycle Cycles $cycle_mode Test ======================"  > $summary_log
	else
		echo "$splitline" >> $summary_log
	fi
}

function CheckResume
{
    if [ "$assumeyes" != "True" ]; then
        sed -i "/${START_SCRIPT}/d" $bootloader
        exit 1
    fi
}

function compare_log
{
    local check_item=$1
    local cmp_file_path=$2
    local cmp_file=$3
    local report_log_file=$4
    if [ $cycle_num -gt 0 ]; then
        if diff $cmp_file_path/old_${cmp_file} $cmp_file_path/new_${cmp_file}; then
            echo "`log_ti` $check_item check PASS" | tee -a $report_log_file
            return 0
        else
            echo "`log_ti` $check_item check FAIL, \
                  fail log is saved in $fail_log_path/cycle${cycle_num}_${cmp_file}" | tee -a $report_log_file
            echo "`log_ti` $check_item check FAIL, \
                  fail log is saved in $fail_log_path/cycle${cycle_num}_${cmp_file}" | tee -a $summary_fail_log
            cp -rf $cmp_file_path/new_${cmp_file} $fail_log_path/cycle${cycle_num}_${cmp_file}
            CheckResume
            return 1
        fi
    fi
}

function generate_log
{
    while [ "$1" != "" ]
    do
        case $1 in
            -m|--message)
                shift
                local log_msg=$1;;
            -p|--path)
                shift
                local log_path=$1;;
            -f|--file)
                shift
                local log_file=$1;;
            -ff|--full_file)
                shift
                local full_log_file=$1;;
            -a|--append)
                local append="TRUE";;
        esac
        shift
    done
    if [ $cycle_num -eq 0 ]; then
        local log_sta="old"
    else
        local log_sta="new"
    fi
    if [ ! -z $log_file ];then
        if [  x"$append" == x"TRUE" ]; then
            echo "$log_msg" >> $log_path/${log_sta}_${log_file}
        else
            echo "$log_msg" >  $log_path/${log_sta}_${log_file}
        fi
    fi
    if [ ! -z $full_log_file ];then
        echo "$log_msg" >> $log_path/$full_log_file
    fi
}

function sum_msg
{
    local log_file=$1
    local msg=$2
    echo -e "$msg" >> $log_file
}

function sum_log
{
    local log_file=$1
    local msg=$2
    sum_msg "$log_file" "$(log_ti) $msg"
}

function split_line
{
    local log_file=$1
    local msg=$2
    sum_msg $log_file "====== $(log_ti) $msg ======"
}
