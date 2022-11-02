#!/bin/bash

function ac_test
{
    bmc_outband_ti="ipmitool -U $bmc_user -P $bmc_pwd -I $bmc_interface -H $BMC_IP "
    echo "Clearing SEL log on $BMC_IP before test begin"
    bmc_outband "sel clear"

    # start client ac cycle test
    for c in `seq 1 $total_cycle`
    do
        single_cycle $c
    done
    echo "`date +'%F_%T'` $total_cycle Cycles AC cycle in client finish"
    showpass
}

function random_ac_test
{
    bmc_outband_ti="ipmitool -U $bmc_user -P $bmc_pwd -I $bmc_interface -H $BMC_IP "
    echo "Clearing SEL log on $BMC_IP before test begin"
    bmc_outband "sel clear"

    interval_ac_time=$random_ac_interval
    # while [ $interval_ac_time -lt $boot_delay ]
    while $stop_flag
    do
        single_random_cycle $interval_ac_time
        interval_ac_time=$[$interval_ac_time+$random_ac_interval]
    done 
}

function quebec_ac_test
{
    bmc_outband_ti="ipmitool -U $server_bmc_user -P $server_bmc_pwd -I $server_bmc_lanplus -H $server_bmc_ip "
    echo "Clearing SEL log on $server_bmc_ip before test begin"
    bmc_outband "sel clear"

    # start client ac cycle test
    for c in `seq 1 $total_cycle`
    do
        single_quebec_cycle $c
    done
    echo "`date +'%F_%T'` $total_cycle Cycles AC cycle in client finish"
    showpass
}

function bmc_outband
{
    local outband_cmd=$1
    local full_cmd="$bmc_outband_ti $outband_cmd"
    echo $full_cmd
    $full_cmd
}

function single_cycle
{
    local cycle_count=$1
    echo -e "\n$split_line"
    echo "`date +%F_%T` NO. cycle $cycle_count run client AC test"

    # set all PDU ports off
    for p in $PDU_Ports
    do
        echo "set PDU port $p off"
        repeat_trycmd 1 5 "snmpset -u $pdu_user -v $snmpset_ver $PDU_IP ${pdu_model}.${p} i 2 >/dev/null 2>&1" y n
        if [ $? -ne 0 ]; then
            echo "PDU port $p off fail"
        else
            echo "PDU port $p off success"
        fi
    done
    echo "sleep $pdu_off_delay and then set PDU port $PDU_Ports up"
    sleep $pdu_off_delay

    # set all PDU ports on
    for p in $PDU_Ports
    do
        echo "set PDU port $p on"
        repeat_trycmd 1 5 "snmpset -u $pdu_user -v $snmpset_ver $PDU_IP ${pdu_model}.${p} i 1 >/dev/null 2>&1" y n
        if [ $? -ne 0 ]; then
            echo "PDU port $p on fail"
        else
            echo "PDU port $p on success"
        fi
    done

    # waiting for BMC up
    repeat_trycmd 10  "$(( $bmc_up_time / 10 ))" "$bmc_outband_ti raw 6 1 >/dev/null 2>&1" y n
    if [ $? -ne 0 ]; then
        echo "BMC ip $BMC_IP is not up after waiting for ${bmc_up_time}s, start retry"
        repeat_trycmd $bmc_up_retry_interval $bmc_up_retry_times "$bmc_outband_ti raw 6 1 >/dev/null 2>&1" y y
        if [ $? -ne 0 ]; then
                echo "after waiting $(( $bmc_up_time + $bmc_up_retry_interval * $bmc_up_retry_times ))s, bmc still not up, test fail"
                showfail
                exit 1
	    fi
    else
        echo "BMC ip $BMC_IP is up"
    fi

    # Wake BMC up, and sleep for power_cycle finish in SUT
    if [ "$bmc_auto_poweron" != "Y" ]; then
        repeat_trycmd $bmc_poweron_retry_interval $bmc_poweron_retry_times "$bmc_outband_ti raw 0 2 1 >/dev/null 2>&1" y n
        for i in `seq 1 5`
        do
          if [ -n "`ipmitool  chassis status|grep -i 'system power' |grep -i on`" ]; then
            echo "chassis is power on "
            break
          else
            sleep 10
          fi
        done
    fi

    # check sel event 0x0e or 0x04
    local res=fail
    if [ $random != False ]; then
    rnd=$[$RANDOM%$randtime]
    echo $rnd >> $repo_path/Random_number.log
    sleep_progress $rnd
    else
        echo "waiting for SUT up and do power_cycle test.."
        python3 $main_path/libs/check_enter_os.py $SERVER_IP $SERVER_USER $SERVER_PWD
        if [ $? == 0 ]; then
            echo "os system started"
        else
            echo "os system hang-up"
            showfail
            exit 1
        fi
	      # sleep_progress $boot_delay
        #echo "Check if 0x04 or 0x0e in BMC SEL Log to make sure power_cycle test finish..."
        #for c in `seq 1 $sel_event_retry_times`
        #do
        #    sel_msg="`$bmc_outband_ti sel list`"
        #    if [ -n "`echo -e $sel_msg | grep -iE '120e6f01ffff'`" ]; then
        #        local res=pass
        #        break
        #    else
        #        echo -e "sel log not contain '0x0e|0x04', sleep $event_retry_time and retry."
        #        sleep $sel_event_retry_interval
        #    fi
        #done
        #if [ $res == 'fail' ]; then
        #   echo "After sleep $(( $sel_event_retry_interval * $sel_event_retry_times ))s, event 0x0e or 0x04 still can't find in BMC SEL log"
        #    showfail
        #    exit 1
        #else
        #    echo "BMC sel event check ok"
        #fi
    fi
    # Collect Sel log in bmc.log
    echo "====== `date +'%F_%T'` NO. $cycle_count times collect sel log ======" >> $sel_log
    repeat_trycmd 5 3 "$bmc_outband_ti sel list >> $sel_log" y n

    # Clear SEL Log
    echo "Clear BMC SEL Log before next cycle" 
    repeat_trycmd 5 3 "$bmc_outband_ti sel clear" y n
    if [ $? -eq 0 ]; then
        echo "Compelet clear SEL log"
    else
        echo "clear SEL log fail"
    fi
    sleep 6
    #
}

function single_random_cycle
{   
    local interval_sec=$1

    echo -e "\n$split_line"
    echo "`date +%F_%T` Delay $interval_sec seconds, execute ac action"

    set_pdu_ports_off $PDU_Ports
    set_pdu_ports_on $PDU_Ports
    # sleep x sec
    sleep_progress $interval_sec

    set_pdu_ports_off $PDU_Ports
    set_pdu_ports_on $PDU_Ports

    start_time=`date +%s`
    # 等待进入os 系统
    # waiting for BMC up
    repeat_trycmd 10  "$(( $bmc_up_time / 10 ))" "$bmc_outband_ti raw 6 1 >/dev/null 2>&1" y n
    if [ $? -ne 0 ]; then
        echo "BMC ip $BMC_IP is not up after waiting for ${bmc_up_time}s, start retry"
        repeat_trycmd $bmc_up_retry_interval $bmc_up_retry_times "$bmc_outband_ti raw 6 1 >/dev/null 2>&1" y y
        if [ $? -ne 0 ]; then
                echo "after waiting $(( $bmc_up_time + $bmc_up_retry_interval * $bmc_up_retry_times ))s, bmc still not up, test fail"
                showfail
                exit 1
	    fi
    else
        echo "BMC ip $BMC_IP is up"
    fi

    # check sel event 0x0e or 0x04
    local res=fail
    if [ $random != False ]; then
    rnd=$[$RANDOM%$randtime]
    echo $rnd >> $repo_path/Random_number.log
    sleep_progress $rnd
    else
        echo "waiting for SUT up and do power_cycle test.."
        python3 $main_path/libs/check_enter_os.py $SERVER_IP $SERVER_USER $SERVER_PWD
        if [ $? == 0 ]; then
            echo "os system started"
        else
            echo "os system hang-up"
            showfail
            exit 1
        fi
        end_time=`date +%s`
        daley_time=$(( $end_time - $start_time ))
        if [ $interval_sec -gt $daley_time ]; then
            stop_flag=false
        fi
        echo "Check if 0x04 or 0x0e in BMC SEL Log to make sure power_cycle test finish..."
        for c in `seq 1 $sel_event_retry_times`
        do
            sel_msg="`$bmc_outband_ti sel list`"
            if [ -n "`echo -e $sel_msg | grep -iE '120e6f01ffff'`" ]; then
                local res=pass
                break
            else
                echo -e "sel log not contain '120e6f01ffff', sleep $event_retry_time and retry."
                sleep $sel_event_retry_interval
            fi
        done
        if [ $res == 'fail' ]; then
            echo "After sleep $(( $sel_event_retry_interval * $sel_event_retry_times ))s, event 0x0e or 0x04 still can't find in BMC SEL log"
            showfail
            exit 1
        else
            echo "BMC sel event check ok"
        fi
    fi
    # Collect Sel log in bmc.log
    echo "====== `date +'%F_%T'` NO. $cycle_count times collect sel log ======" >> $sel_log
    repeat_trycmd 5 3 "$bmc_outband_ti sel list >> $sel_log" y n

    # Clear SEL Log
    echo "Clear BMC SEL Log before next cycle" 
    repeat_trycmd 5 3 "$bmc_outband_ti sel clear" y n
    if [ $? -eq 0 ]; then
        echo "Compelet clear SEL log"
    else
        echo "clear SEL log fail"
    fi
}

function single_quebec_cycle
{
    local cycle_count=$1
    echo -e "\n$split_line"
    echo "`date +%F_%T` NO. cycle $cycle_count run client AC test"
    # 机头下电
    set_pdu_ports_off $server_pdu_port 
    # 机尾下电
    set_pdu_ports_off $GPU_BOX_pdu_port

    for c in `seq 1 $GPU_BOX_up_retry_times`
    do

        set_pdu_ports_on $GPU_BOX_pdu_port
        # check bmc up
        #check_bmc_on $GPU_BOX_bmc_lanplus $GPU_BOX_bmc_ip $GPU_BOX_bmc_user $GPU_BOX_bmc_pwd
        local bmc_ti = "ipmitool -U $GPU_BOX_bmc_user -P $GPU_BOX_bmc_pwd -I $GPU_BOX_bmc_lanplus -H $GPU_BOX_bmc_ip "
        repeat_trycmd 10  "$(( $bmc_up_time / 10 ))" "$bmc_ti raw 6 1 >/dev/null 2>&1" y n
        if [ $? -ne 0 ]; then
            echo "BMC ip $GPU_BOX_bmc_ip is not up after waiting for ${bmc_up_time}s, start retry"
            repeat_trycmd $bmc_up_retry_interval $bmc_up_retry_times "$bmc_ti raw 6 1 >/dev/null 2>&1" y y
            if [ $? -ne 0 ]; then
                    echo "after waiting $(( $bmc_up_time + $bmc_up_retry_interval * $bmc_up_retry_times ))s, bmc still not up, test fail"
                    showfail
                    exit 1
            fi
        else
            echo "BMC ip $b_ip is up"
        fi

        power_status=`$bmc_ti power status`
        if [ -n "`echo -e $power_status | grep -iE 'on'`" ]; then
            break
        else
            if [ $GPU_BOX_up_mode == "debug" ]; then
                sleep $GPU_BOX_up_retry_interval
            else
                showfail 
                exit 1
            fi
        fi
    done

    # 机头上电
    set_pdu_ports_on $server_pdu_port
    # 等待进入os
    check_enter_os $server_bmc_ip $server_bmc_user $server_bmc_pwd

    end_action
}

function set_pdu_ports_on
{   
    local ports=$1
    # set all PDU ports on
    for p in $ports
    do
        echo "set PDU port $p on"
        repeat_trycmd 1 5 "snmpset -u $pdu_user -v $snmpset_ver $PDU_IP ${pdu_model}.${p} i 1 >/dev/null 2>&1" y n
        if [ $? -ne 0 ]; then
            echo "PDU port $p on fail"
        else
            echo "PDU port $p on success"
        fi
    done
}

function set_pdu_ports_off
{
    # set all PDU ports of
    local ports=$1
    for p in $ports
    do
        echo "set PDU port $p off"
        repeat_trycmd 1 5 "snmpset -u $pdu_user -v $snmpset_ver $PDU_IP ${pdu_model}.${p} i 2 >/dev/null 2>&1" y n
        if [ $? -ne 0 ]; then
            echo "PDU port $p off fail"
        else
            echo "PDU port $p off success"
        fi
    done
    echo "sleep $pdu_off_delay and then set PDU port $ports up"
    sleep $pdu_off_delay
}

function check_bmc_on 
{
    local b_interface=$1
    local b_ip=$2
    local b_user=$3
    local b_pwd=$4
    local bmc_ti = "ipmitool -U $b_user -P $b_pwd -I $b_interface -H $b_ip "
    repeat_trycmd 10  "$(( $bmc_up_time / 10 ))" "$bmc_ti raw 6 1 >/dev/null 2>&1" y n
    if [ $? -ne 0 ]; then
        echo "BMC ip $b_ip is not up after waiting for ${bmc_up_time}s, start retry"
        repeat_trycmd $bmc_up_retry_interval $bmc_up_retry_times "$bmc_ti raw 6 1 >/dev/null 2>&1" y y
        if [ $? -ne 0 ]; then
                echo "after waiting $(( $bmc_up_time + $bmc_up_retry_interval * $bmc_up_retry_times ))s, bmc still not up, test fail"
                showfail
                exit 1
	    fi
    else
        echo "BMC ip $b_ip is up"
    fi
}

function check_enter_os
{
    local b_ip=$1
    local b_user=$2
    local b_pwd=$3
    echo "waiting for SUT up and do power_cycle test.."
    python $main_path/libs/check_enter_os.py $b_ip $b_user $b_pwd
    if [ $? == 0 ]; then
        echo "os system started"
    else
        echo "os system hang-up"
        showfail
        exit 1
    fi
}

function end_action
{
    # Clear SEL Log
    echo "Clear BMC SEL Log before next cycle" 
    repeat_trycmd 5 3 "$bmc_outband_ti sel clear" y n
    if [ $? -eq 0 ]; then
        echo "Compelet clear SEL log"
    else
        echo "clear SEL log fail"
    fi
}
