#!/bin/bash

function pci_info
{
    local info_key='lnksta:|uesta|cesta|lnkcap'
    for e in $(lspci | awk '{print $1}');
    do
        if [ -n "`lspci -s $e -vvv 2>/dev/null | grep -Ei $info_key`" ]; then
            lspci -s $e | grep $e
            lspci -s $e -vvv 2>/dev/null \
                        | grep -iE $info_key \
                        | sed s',NonFatalErr[+-],,'g \
                        | sed -E 's,^\s+|\s+$,,g'
        fi
    done
}

function lspci_check
{
    local lspci_log_full=$lspci_log/lspci_full.log
    pci_msg="$(pci_info)"
    echo -e "$pci_msg" > $lspci_log/lspci_cycle${cycle_num}.log
    generate_log -m "$pci_msg" \
                 -p $lspci_log \
                 -f lspci.log \
                 -ff lspci_full.log
    if [ $cycle_num -eq 0 ]; then
        # 检查 uesta 和 cesta 这两行中是否存在+号 
        local error_info=$(cat $lspci_log/old_lspci.log \
                            | egrep -i "downgrade")
        if [ "$error_info" ]; then
            more << EOF
======================================================================================
Show "$error_info" info , Please input keyword(y/n), Continue execution test
======================================================================================
EOF
            read -p "Please input (y/n), Other keys indicate that execution continues :" stop_flag
            if [[ $stop_flag == 'n' || $stop_flag == 'N' ]]; then
                fail_msg="$(log_ti) lspci have 'downgrad' in $lspci_log/lspci_old.log ($error_info), check FAIL"
                sum_msg $summary_fail_log "$fail_msg"
                sum_msg $summary_log "$fail_msg"
                assumeyes=False
                CheckResume
            else
                sum_msg $summary_log "$(log_ti) lspci check PASS"
            fi
        else
            sum_msg $summary_log "$(log_ti) lspci check PASS"
        fi
	else
	    # after first cycle
		compare_log "lspci 'UESta|CESta|LnkCap|LnkSta'" \
                     $lspci_log \
                     lspci.log \
                     $summary_log
	fi
}
