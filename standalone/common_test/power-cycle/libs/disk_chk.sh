#!/bin/bash

#检查磁盘 smart/speed/dmesg速率
function disk_check
{
    disk_partition_check
    disk_smartlog_check
    disk_SN_check
    disk_speed_check
    disk_dmesg_check
}

# 检查 HDD/NVME Smart log
function disk_smartlog_check
{
    # del old log
    split_line $disk_log_path/disk_sn_full.txt "disk Serial Number Collection"
    if [ -f $disk_log_path/new_disk_sn.txt ];then
        rm -rf $disk_log_path/new_disk_sn.txt
    fi
    # check hdd smartlog
    local hdd_num=`cat /proc/partitions | grep -Pc sd[a-zA-Z]+`
    if [ $hdd_num -ne 0 ]; then
        hdd_info_check
    fi

    # check nvme smartlog
    if [ `cat /proc/partitions | grep -c nvme` -ne 0 ]; then
        nvme_smart_path=$smart_log_path/nvme
        if [ ! -d $nvme_smart_path ]; then
            mkdir -p $nvme_smart_path
        fi
        nvme_list=`cat /proc/partitions | grep -P "nvme\d+n\d+" \
                   | grep -Pv "nvme\d+n\d+p\d+" \
                   | awk '{print $4}' \
                   | sort -V`
        nvme_info_check
    fi
}

#check hdd smart log
function hdd_info_check
{
    # collect hdd info
     hdd_info_collect
    # check hdd info
    for hdd in `cat /proc/partitions \
                | grep -vP 'sd[a-zA-Z]+\d+' \
                | grep -Po 'sd[a-zA-Z]+' \
                | sort -V`
    do
        compare_log "HDD $hdd smartlog" $disk_log_path hdd_${hdd}_smart.log $summary_log
        if [ $? -eq 1 ]; then
            smartctl -a /dev/$hdd >$fail_log_path/cycle${cycle_num}_${hdd}_fullsmart.log 2>&1
        fi
    done

}

# collect hdd SN&smart log
function hdd_info_collect
{
    split_line $disk_log_path/hdd_smart_full.log "HDD Smart Log Collect"
    for hdd in `cat /proc/partitions | grep -vP 'sd[a-zA-Z]+\d+' \
                | grep -Po 'sd[a-zA-Z]+' | sort`
    do
        local drive_sn=`smartctl -i /dev/$hdd | grep -i 'Serial Number:' \
                  | awk -F\: '{print $2}' | tr -d ' '`
        local smart_info=`smartctl -a /dev/$hdd`
        generate_log -m "/dev/$hdd $drive_sn" \
                     -p $disk_log_path \
                     -f disk_sn.txt \
                     -ff disk_sn_full.txt \
                     -a
        local hdd_smart_msg=`echo "$smart_info" | egrep -i \
                       "Reallocated_Sector_Ct|Current_Pending_Sector|Offline_Uncorrectable"`
        generate_log -m "$hdd_smart_msg" \
                     -p $disk_log_path \
                     -f hdd_${hdd}_smart.log \
                     -ff hdd_smart_full.log
        generate_log -m "$smart_info" \
                     -p $smart_log_path \
                     -f ${hdd}_smart_cycle${cycle_num}.log
    done
}

function nvme_info_check
{
    nvme_info_collect
    for nvme in $nvme_list
    do
        echo "$nvme_smart_path/new_nvme_${nvme}_smartcrc.log"
        if [ -f $nvme_smart_path/new_nvme_${nvme}_smartcrc.log ]; then
            compare_log "NVME $nvme smartadd crc" \
                         $nvme_smart_path \
                         nvme_${nvme}_smartcrc.log \
                         $summary_log
        fi
        compare_log "NVME $nvme smartlog" \
                     $nvme_smart_path \
                     nvme_${nvme}_smart.log \
                     $summary_log
    done
}

function nvme_info_collect
{
    # nvme SN&smart_log collect
    echo "########$(log_ti) NVME Smart Log Collect########" \
          | tee -a $nvme_smart_path/nvme_smart_full.log
    local nvme_tool=`command -v nvme`
    local nvme_sn_msg=`$nvme_tool list | grep -P '\/dev.*' | awk '{print $1 " " $2}' | sort -V`
    generate_log -m "$nvme_sn_msg" \
                 -p $disk_log_path \
                 -f disk_sn.txt \
                 -ff disk_sn_full.txt \
                 -a
    for nvme in $nvme_list
    do
        local nvme_smart_log=`$nvme_tool smart-log /dev/$nvme | \
                              egrep -i "media_errors|critical_warning|num_err_log_entries"`
        local smart_info=`$nvme_tool smart-log /dev/$nvme`
        if [[ `$nvme_tool list | grep -i /dev/$nvme | grep -i intel` ]]; then
            local intel_smart_add=`$nvme_tool intel smart-log-add /dev/$nvme`
            local intel_smart_crc=`$nvme_tool intel smart-log-add /dev/$nvme | grep -i crc`
            generate_log -m "$intel_smart_crc" \
                         -p $nvme_smart_path \
                         -f nvme_${nvme}_smartcrc.log \
                         -ff nvme_smartcrc_full.log
            generate_log -m "$intel_smart_add" \
                         -p $nvme_smart_path \
                         -f ${nvme}_smartadd_cycle${cycle_num}.log
        fi
        generate_log -m "$nvme_smart_log" \
                     -p $nvme_smart_path \
                     -f nvme_${nvme}_smart.log \
                     -ff nvme_smart_full.log
        generate_log -m "$smart_info" \
                     -p $nvme_smart_path \
                     -f ${nvme}_smart_cycle${cycle_num}.log
    done
}

function disk_SN_check
{
    compare_log "disk serial number" \
                $disk_log_path \
				disk_sn.txt \
				$summary_log
}

function disk_speed_check
{
    # check HDD rate in smartctl
    local fail_count=0
    #`grep -wE "s..|sd.[a-z]+|nvme...|nvme...." /proc/partitions | awk '{print $NF}' | sort`
    local drives=`grep -wE "s..|sd.[a-z]+" /proc/partitions \
                  | awk '{print $NF}' | sort`
    split_line ${disk_log_path}/disk_speed.log "check speed log"
    for e in $drives
    do
        smartinfo=`smartctl -a /dev/$e | grep -i "SATA Version is" | awk -F, '{print $2}'`
        drive_speed1=`echo $smartinfo | awk '{print $1}'`
        drive_speed2=`echo $smartinfo | awk '{print $4}'`
        if [ "$drive_speed1" != "$drive_speed2" ]; then
            sum_msg ${disk_log_path}/disk_speed.log "The drive /dev/$e speed: ${drive_speed1}, current: ${drive_speed2} are mis-match."
            sum_msg $summary_fail_log "The drive /dev/$e speed: ${drive_speed1}, current: ${drive_speed2} are mis-match."
            sum_msg $summary_log "disk /dev/$e speed check FAIL"
            smartctl -a /dev/$e >> $fail_log_path/cycle_$cycle_num_${e}_smart.log
            fail_count=$(( $fail_count + 1 ))
        else
            sum_msg ${disk_log_path}/disk_speed.log "The drive /dev/$e speed: ${drive_speed1}, current: ${drive_speed2} ckeck PASS"
        fi
    done
    echo fail_count=$fail_count
    if [ $fail_count -eq 0 ]; then
        sum_msg $summary_log "$(log_ti) Disk speed check PASS"
    else
        sum_msg $summary_log "$(log_ti) Disk speed check FAIL"
    fi
}

function disk_dmesg_check
{
    #检查 dmesg "SATA link" 日志
    local old_hdd_speed_log=$disk_log_path/old_hdd_speed.log
    local new_hdd_speed_log=$disk_log_path/new_hdd_speed.log
    if [ $cycle_num -eq 1 ]; then
        if [ `dmesg | grep -ci "SATA link"` -eq 0 ]; then
            echo "NO. $cycle_num still can not detected SATA speed in dmesg." >> $summary_log
            CheckResume
        fi
        dmesg | grep -i "SATA link" | awk -F "]" '{print $2}' \
              | sort | tee $old_hdd_speed_log
    elif [ $cycle_num -gt 1 ]; then
        dmesg | grep -i "SATA link" | awk -F "]" '{print $2}' \
              | sort | tee $new_hdd_speed_log
        compare_log "disk speed" \
                     $disk_log_path hdd_speed.log $summary_log
    fi
}

function disk_partition_check
{
    split_line $disk_log_path/disk_partition_full.log "disk partition info collect"
    local disk_partition=`cat /proc/partitions \
                          | grep -v "dm-" \
                          | sort -k 4 \
                          | awk '{print $4 "\t" $3 }'\
                          | sort -V`

    generate_log -m "$disk_partition" \
                 -p $disk_log_path \
                 -f disk_partition.log \
                 -ff disk_partition_full.log

    compare_log "disk parition" \
                 $disk_log_path \
                 disk_partition.log \
                 $summary_log
}


function interact_test
{
    disks=`fdisk -l |grep -iEo 'Disk /dev/sd[a-z]+|Disk /dev/nvme\w+n\w' | awk '{print $2}'`
    os_disk=`df |grep -i /boot | awk '{print $1}' | grep -Eo '/dev/sd[a-z]+|/dev/nvme\w+n\w'  | head -n1`
    for disk in $disks
    do 
    if [ $os_disk == $disk ]; then
    echo os disk
    else
    echo y | parted $disk mklabel gpt 2>/dev/null
    parted $disk mkpart p1 0GB 50% 2>/dev/null
    parted $disk mkpart p2 50% 100% 2>/dev/null
    fi 
    done

    for disk in $disks
    do
    if [ $os_disk == $disk ]; then
    echo os disk
    else

    part1=`fdisk -l |grep -Po "${disk}p?1"`
    echo $part1
    echo y | mkfs.ext4 $part1
    if [ $? -ne 0 ]; then
            echo "create ext4 file system on /dev/$part1 FAIL" \
                 | tee -a $fail_log_path/avms_fail.log
            echo "Please resolve this problem:" \
                 "the drive /dev/$part1 can not be formated to EXT4 filesystem." \
                 | tee -a $fail_log_path/avms_fail.log
            exit 1
    fi
       if [ ! -d $avme_log_path$part1 ];then
            mkdir -p $avme_log_path$part1
        fi
    mount $part1 $avme_log_path$part1
    if [ $? -ne 0 ]; then
            echo "mount /dev/$part1 on $avme_log_path/$part1 FAIL" \
                 | tee -a $fail_log_path/avms_fail.log
            echo "Please resolve this problem:" \
                 "the path $avme_log_path/$part1 can not be mounted." \
                 | tee -a $fail_log_path/avms_fail.log
            exit 1
        fi
    dd if=/dev/zero of=$avme_log_path$part1/write_file bs=1G count=100
    md5sum $avme_log_path$part1/write_file > $avme_log_path${part1}.md5 

    fi
    done

}