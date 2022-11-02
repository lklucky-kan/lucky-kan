#!/bin/bash

function parser_fio_args
{
    local fio_old_args="$1"
    local fio_change_args="$2"
    for para in $fio_change_args
    do
        if [ `echo $para | grep -ic "="` -ne 0 ]; then
            replase=`echo $para | awk -F\= '{print $1}'`
            replase1=`echo "$replase" | sed 's/\-/\\\-/g'`
            if [ `echo $fio_old_args | grep -ic $replase1` -ne 0 ]; then
                fio_old_args=`echo $fio_old_args | sed -E "s/${replase}=\S+/$para/g"`
            else
                fio_old_args="$fio_old_args $para"
            fi
        else
            para1=`echo "$para" | sed 's/\-/\\\-/g'`
            if [ `echo $fio_old_args | grep -ic $para1` -eq 0 ]; then
                fio_old_args="$fio_old_args $para"
            else
                continue
            fi
        fi
    done
    echo $fio_old_args
}

function start_fio
{
    echo "`log_ti` fio run arguments:" | tee -a $fio_log_path/fio_args.log
    for dev in ${dev_list}
    do
        echo "$fio_path $fio_args --name=$(basename $dev) --filename=$dev" | tee -a $fio_log_path/fio_args.log
        $fio_path $fio_args --name=$(basename $dev) --filename=$dev >$fio_log_path/fio_cycle${cycle_num}.log &
    done
}
