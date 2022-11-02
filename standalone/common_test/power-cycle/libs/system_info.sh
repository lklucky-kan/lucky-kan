#!/bin/bash


function system_check
{
	fru_check
	memory_check
	cpu_check
	smbios_check
}

function fru_check
{
    # collect fru.bin
    sleep 3
    if [ $cycle_num -eq 0 ]; then
        ipmitool fru read 0 $sys_log_path/old_fru.bin &> /dev/null
    else
        ipmitool fru read 0 $sys_log_path/new_fru.bin &> /dev/null
        compare_log "FRU" $sys_log_path fru.bin $summary_log
    fi
    split_line $sys_log_path/fru_info_full.log "FRU info Collect"
    fru_info=`ipmitool fru print`
    generate_log -m "$fru_info" \
                 -p $sys_log_path \
                 -ff fru_info_full.log

}

function memory_check
{
    # check memory info
    mem_size=`free -m | grep Mem | awk '{print $2}'`
    generate_log -m "$mem_size" \
                 -p $sys_log_path \
                 -f mem_size.log \
                 -ff mem_size_full.log
    if [ $cycle_num -gt 0 ]; then
        mem_old=`cat $sys_log_path/old_mem_size.log`
        mem_new=`cat $sys_log_path/new_mem_size.log`
        mem_diff=$[ $mem_old - $mem_new ]
        if [ $mem_diff -lt 0 ]; then
            mem_diff=$(( 0 - $mem_diff ))
        fi
        if [ $mem_diff -lt 10 -a $mem_diff -ge 0 ]; then
            echo "`log_ti` MEM SIZE check PASS" >> $summary_log
        else
            cp $sys_log_path/new_mem_size.log $fail_log_path/cycle${cycle_num}_mem_size.log
            echo "`log_ti` MEM SIZE check FAIL, please refer $fail_log_path/cycle${cycle_num}_mem_size.log for detail" >>$summary_log
            echo "compare $sys_log_path/old_mem_size.log and $fail_log_path/cycle${cycle_num}_mem_size.log" >>$summary_fail_log
            CheckResume
        fi
    fi
}

function cpu_check
{
    # check cpu frequency and ips
    cpuinfo=`cat /proc/cpuinfo | grep -Eiv '^(cpu MHz|bogomips)'`
    generate_log -m "$cpuinfo" \
                 -p $sys_log_path \
                 -f cpu_info.log \
                 -ff cpu_info_all.log
    compare_log "CPU info" $sys_log_path cpu_info.log $summary_log
}

function smbios_check
{
    local smbios_msg=`dmidecode \
                      | egrep -vi 'Wake-up Type|[Cc]hange [Tt]oken'`
    local change_token=`dmidecode \
                        | grep -i '[Cc]hange [Tt]oken' \
                        | awk '{print $3}'`
    generate_log -m "$smbios_msg" \
                 -p $sys_log_path \
                 -f smbios.log
    compare_log "SMBIOS Info" $sys_log_path smbios.log $summary_log

    split_line $sys_log_path/change_token.log "change token number change"
    generate_log -m "$change_token" \
                 -p $sys_log_path \
                 -f change_token.log \
                 -a
}


function get_serial_log
{
    ssh-keygen -R $bmc_ip
    /usr/bin/expect << EOF
spawn  scp -r $bmc_user@$bmc_ip:/mnt/data1/log/hostlog  $serial_log_path/${cycle_num}_serial
expect  "*yes/no*"
send "yes\n"
expect  "*pass*"
send "$bmc_passwd\n"
expect eof
EOF

}