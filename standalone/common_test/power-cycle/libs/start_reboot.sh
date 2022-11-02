#!/bin/bash

function start_reboot
{
    reboot_time_record
    case $cycle_mode in
        reboot)
            reboot_action "reboot" "warm reboot";;
        cold_reset)
            reboot_action "ipmitool raw 0 2 3" "cold reboot";;
        dc)
            reboot_action "ipmitool raw 0 2 2" "DC cycle";;
        reboot_dc)
            reboot_dccycle;;
        ac)
            reboot_action "" "AC Cycle";;
        *)
            echo "Invalid reboot mode"
            exit 1;;
    esac
}

function reboot_dccycle
{
    sleep $fio_delay_time
    disks=`fdisk -l |grep -iEo 'Disk /dev/sd[a-z]+|Disk /dev/nvme\w+n\w' | awk '{print $2}'`
    os_disk=`df |grep -i /boot | awk '{print $1}' | grep -Eo '/dev/sd[a-z]+|/dev/nvme\w+n\w'  | head -n1`
    if [ $cycle_num -le $total_cycle ]; then
        if [ $interact_mode == True ]; then
        for disk in $disks
        do 
        if [ $os_disk == $disk ]; then
           echo os disk
        else   
            part1=`fdisk -l |grep -Po "${disk}p?2"`
            if [ $cycle_num -ne 0 ]; then
                echo mount
                mount $part1 $avme_log_path$part1
                fi
            nohup fio --name=$avme_log_path${part1}_test --filename=$part1 --ioengine=libaio --direct=1 --thread=1 --numjobs=1 --iodepth=128 --rw=randrw --bs=4k --rwmixread=50 --runtime=3600 --time_based=1 --size=100% --norandommap=1 --randrepeat=0 --group_reporting --log_avg_msec=1000 --bwavgtime=1000 --minimal  2>&1 &
        sum_msg $summary_log "$(log_ti) fio --name=$avme_log_path${part1}_test --filename=$part1 --ioengine=libaio --direct=1 --thread=1 --numjobs=1 --iodepth=128 --rw=randrw --bs=4k --rwmixread=50 --runtime=3600 --time_based=1 --size=100% --norandommap=1 --randrepeat=0 --group_reporting --log_avg_msec=1000 --bwavgtime=1000 --minimal "
        fi
        done
        fi
        sleep 3
        fio_num=`ps -ef |grep fio |grep -v grep |wc -l` 
        if [ $fio_num -ne 0 ]; then
             sum_msg $summary_log "$(log_ti) fio is running"
           else
             sum_msg $summary_fail_log "$(log_ti) fio is fail"
           fi   
        
        sleep $fio_delay_time
         sum_msg $summary_log "$(log_ti) reboot cycle"

        reboot
    elif [ $cycle_num -gt $total_cycle -a $cycle_num -lt $(( $total_cycle * 2 )) ]; then
        if [ $interact_mode == True ]; then
        for disk in $disks
        do
        if [ $os_disk == $disk ]; then
           echo os disk
        else
            part1=`fdisk -l |grep -Po "${disk}p?2"`
            if [ $cycle_num -ne 0 ]; then
                echo mount
                mount $part1 $avme_log_path$part1
            fi

            nohup fio --name=$avme_log_path${part1}_test --filename=$part1 --ioengine=libaio --direct=1 --thread=1 --numjobs=1 --iodepth=128 --rw=randrw --bs=1M --rwmixread=50 --runtime=3600 --time_based=1 --size=100% --norandommap=1 --randrepeat=0 --group_reporting --log_avg_msec=1000 --bwavgtime=1000 --minimal 2>&1 &
        
        sum_msg $summary_log "$(log_ti) fio --name=$avme_log_path${part1}_test --filename=$part1 --ioengine=libaio --direct=1 --thread=1 --numjobs=1 --iodepth=128 --rw=randrw --bs=4k --rwmixread=50 --runtime=3600 --time_based=1 --size=100% --norandommap=1 --randrepeat=0 --group_reporting --log_avg_msec=1000 --bwavgtime=1000 --minimal "
        fi
        done
        fi
        sleep 3
        fio_num=`ps -ef |grep fio |grep -v grep |wc -l`
        if [ $fio_num -ne 0 ]; then
             sum_msg $summary_log "$(log_ti) fio is running"
           else
             sum_msg $summary_fail_log "$(log_ti) fio is fail"
           fi

        sleep $fio_delay_time
        sum_msg $summary_log "$(log_ti) dc cycle"
        ipmitool raw 0 2 2
    else
        log_check 'messages'
        if [ $interact_mode == True ]; then
        for disk in $disks
        do
        if [ $os_disk == $disk ]; then
           echo os disk
        else
            part1=`fdisk -l |grep -Po "${disk}p?1"`
            mount $part1 $avme_log_path$part1
            sleep 2
            md5sum -c  $avme_log_path${part1}.md5  >> ${avme_log_path}/md5_check.log
            sleep 3
        fi
        done
        fi
        echo "`ctime` $total_cycle cycles warm reboot and $total_cycle cycles DC cycle all finished." >> $summary_log
        bash $stop_cycle
    fi
}

function reboot_action
{
    local cycle_action=$1
    local cycle_type=$2
    if [ "$cycle_mode" == "ac" ]; then
      #echo "Check if 0x04 or 0x0e in BMC SEL Log to make sure power_cycle test finish..."
      #for c in `seq 1 10`
      #do
      #    ipmitool raw 0x0a 0x44 0 0 0xff 0 0 0 0 0x20 0 4 0x12 0x0e 0x6f 1 0xff 0xff
      #    ipmitool raw 4 2 1 2 3 4 5 6 7 8
      #    sel_msg="`ipmitool sel list`"
      #    if [ -n "`echo -e $sel_msg | grep -iE '120e6f01ffff'`" ]; then
      #        echo "`ctime` sel log add info successful " | tee -a $summary_log
	#      sync
	#      sleep 10
        #      break
        #  else
        #      sleep 5
        #      echo  "`ctime` sel log not contain '120e6f01ffff', retry." | tee -a $summary_log
        #  fi
      #done
        sync 
        sleep 10
	    echo "cycle=pass" > /root/power_cycle_end_flag.log
        echo "`ctime` os system check info successful " | tee -a $summary_log
    fi
    if [ $cycle_num -ge $total_cycle ]; then
        log_check 'messages'
        echo "`ctime` $total_cycle cycles $cycle_type test finished." | tee -a $summary_log
        bash $stop_cycle
    else
            sleep $fio_delay_time
            $cycle_action
    fi
}

function reboot_time_record
{
    if [ $cycle_num -eq 0 ]; then
        date +%s > $tmp_log_path/dateold.log
    else
        dateold=`cat $tmp_log_path/dateold.log`
        datenew=`date +%s`
        echo $datenew > $tmp_log_path/dateold.log
        date_use=$(( $datenew - $dateold ))
        echo "`log_ti` This cycle totally take: $date_use secs" >> $summary_log
    fi
}

function init_bootloader
{
    local sreboot_script=`basename $reboot_script`
    if grep -q "${sreboot_script}" $bootloader; then
        sed -i "/${sreboot_script}/d" $bootloader
    elif grep -q "${sreboot_script}" /root/.bashrc; then
        sed -i "/${sreboot_script}/d" /root/.bashrc
    fi
    if [ "$auto_login" == "True" ]; then
        echo "bash ${reboot_script} &" >> /root/.bashrc
    else
        echo "bash ${reboot_script} &" >> $bootloader
    fi
}

#!/bin/bash

function gene_stop_cycle
{
    if [ -f stop_cycle ]; then
        rm -rf $stop_cycle
    fi
    echo "Create stop script $stop_cycle in location: $main_path"
    cat > $stop_cycle << EOF
#!/bin/bash

summary_log=${summary_log}
reboot_script=`basename $reboot_script`
stop_cycle=${stop_cycle}
bootloader=$bootloader

sed -i "/\$reboot_script/d" $bootloader

killall fio
killall iostat
for p in \`ps -ef | grep -i \$reboot_script | grep -v grep | awk '{print \$2}'\`
do
    kill -9 \$p
done
EOF

chmod 777 ${stop_cycle}
}
