#!/bin/bash

# Swich to main script path
main_path=$(cd `dirname $0` && pwd)
cd $main_path

source lib/common.sh
# define global vars
test_name=`echo $0 | awk -F '.' '{print $1}' | sed 's,_,-,g'`
total_cycle=50
size=100G
disk_type=nvme
disk_list=all
md5sum=md5sum
fio_mode=False
md5_mode=False
hp_mode=None
assumeyes=False
fio_delay=180
s_time=`date '+%s'`
logdir=${main_path}/reports
tmpdir=${main_path}/temp
script_name=`basename $0`
bus_id_regex='[a-zA-Z0-9]{4}\:[a-zA-Z0-9]{2}\:[a-zA-Z0-9]{2}\.[a-zA-Z0-9]+'
split_line="==============================================================================="

sata_smart_keys=(
    "SATA" \
    "Reallocated_Sector_Ct" \
    "Current_Pending_Sector" \
    "UDMA_CRC_Error_Count"
)

nvme_smart_keys=(
    "NVME" \
    "critical_warning" \
    "media_errors" \
    "num_err_log_entries" \
    "Warning Temperature Time"
)

fio_paras=(
    "--ioengine=libaio" "--direct=1" "--bs=4k" "--thread=1" "--iodepth=1" \
    "--rw=randwrite" "--size=100%" "--rwmixread=50" "--numjobs=1" \
    "--runtime=8h" "--time_based=1" "--norandommap=1" "--randrepeat=0" \
    "--group_reporting" "--log_avg_msec=1000" "--bwavgtime=1000"
)

# define global functions
function usage
{
    more << EOF
Usage: $0 Usage:

SATA HDD/SSD or NVMe SSD Hotplug with FIO Test.

Options:
  -c, --cycle           define total cycle number (default: $total_cycle)
  -t, --type            define disk type (default: $disk_type)
                        choices: ['sata', 'nvme']
  -d, --drives          specify test disk list, eg -d 'nvme1n1, nvme2n1' (default: $disk_list)
  -ushp, --unsafe-hp    doing hotplug without notification
  -shp, --safe-hp       doing hotplug in safe with notification
  -lkreset, --linkreset doing linkreset test
  -ioreset             doing ioreset test
  -y, --assumeyes       answer yes for all questions

FIO Options:
  Run fio process for each test disk with specified parameters.
  --fio            Raising fio during test cycle
  --fiopara        change fio test parameters
                   (default: ${fio_paras[@]})
  --fio-delay      fio runing time (default: ${fio_delay}s)

MD5 Checksum:
  doing md5sum check during test.
  --md5check       create partition and doing md5sum check
  -s, --size       define md5 file size (default: $size)
                   format: ['1K', '1M', '1G']

Safety hotplug with MD5 check test on all $disk_type disks on SUT:
  bash $(basename $0) -c $total_cycle -t $disk_type --fio --md5check --fio-delay 60 -shp

Unsafety hotplug with MD5 check test on specified disks:
  bash $(basename $0) -d "nvme1n1 nvme2n1" -c $total_cycle -t $disk_type --fio --md5check -ushp

Doing NVME LinkReset test:
  bash $(basename $0) -c $total_cycle -t nvme --fio --md5check --fio-delay 60 -lkreset

Doing NVME IOReset test:
  bash $(basename $0) -c $total_cycle -t nvme --fio --md5check --fio-delay 60 -ioreset
PS:
  If want to temporarily stop this test, you can press: <CTRL+Z>
  And if want to continue the stoped test, you can press "fg"
EOF
    exit 0
}

function clean_dir
{
    local dir=`basename $1`
    local ext=$2
    local ignore="$3"
    if [ "$ignore" == "" ]; then
        local quantity=`ls ${dir}/*${ext} 2> /dev/null | wc -l`
    else
        local quantity=`ls ${dir}/*${ext} 2> /dev/null | grep -vE "$ignore" | wc -l`
    fi
    if [ $quantity -ne 0 ]; then
        if [ "$assumeyes" == "False" ]; then
            read -ep "Continue to remove all the $ext in ${dir}/*${ext} (default: no) [Y/n]: " \
                 -i "Y" ans
        else
            ans=y
        fi
        case $ans in
            y*|Y*)
                echo "Starting remove the $ext file..."
                for e in `ls ${dir}/`
                do
                    if [ `echo $e | grep -cE "^$ignore$"` -eq 1 ]; then
                        continue
                    fi
                    local file_abs_path=`realpath ${dir}/$e`
                    if [ -d $file_abs_path ] ||
                       [ `echo $e | grep -cE "${ext}$"` -ne 0 ]; then
                        echo " ---> remove file $file_abs_path"
                        rm -rf $file_abs_path
                    fi
                done
                echo -e '\ndone!\n'
                ;;
            * )
                return 1
                ;;
        esac
    fi
}

function disk_sn_get
{
    local dev=$1
    case $disk_type in
        sata)
            check_tool smartctl
            smartctl -a /dev/$dev | grep -i 'serial number' | awk -F\: '{print $NF}' | tr -d ' ' 2> /dev/null
            ;;
        nvme)
            check_tool nvme
            nvme list 2> /dev/null | grep /dev/$dev | awk '{print $2}' | tr -d ' '
            ;;
    esac
}

function smartinfo_get
{
    local operation=$1
    local dev=$2
    local log=${logdir}/smart/${disk_type}_${dev}_smart_${operation}.log
    for key in ${smart_keys[@]:1:${#smart_keys[@]}}
    do
        if [ "${smart_keys[0]}" == "SATA" ]; then
            local value=`smartctl -A /dev/$dev 2> /dev/null \
                                  | grep -i "$key" \
                                  | awk -F ' - ' '{print $NF}' \
                                  | tr -d ' '`
            echo "Drive: /dev/${dev}, Key: ${key}, Value: $value" >> $log
        elif [ "${smart_keys[0]}" == "NVME" ]; then
            local value=`nvme smart-log /dev/$dev 2> /dev/null \
                               | grep -i "$key" \
                               | awk -F ':' '{print $NF}' \
                               | tr -d ' '`
            echo "Drive: /dev/${dev}, Key: ${key}, Value: $value" >> $log
        fi
    done
}

function smart_chk
{
    local dev=$1
    for log in ${logdir}/smart/${disk_type}_${dev}_smart_*.log
    do
        if [ `echo $log | grep -co criteria` -eq 1 ]; then
            smart_criteria=`cat $log`
        elif [ `echo $log | grep -co compare` -eq 1 ]; then
            smart_compare=`cat $log`
        fi
    done
    if [ "`echo $smart_criteria | tr -d ' '`" == "" ] ||
       [ "`echo $smart_compare | tr -d ' '`" == "" ]; then
        echo "smart log is null"
        exit 1
    fi
    if [ "$smart_criteria" == "$smart_compare" ]; then
        echo "Check $disk_type disk /dev/$dev smartlog PASS."
    else
        echo "Check $disk_type disk /dev/$dev smartlog FAIL."
        echo "Please run 'diff ./reports/${disk_type}_${dev}_smart_criteria.log" \
             "./reports/${disk_type}_${dev}_smart_compare.log' for any details."
    fi
}

function single_fio
{
    local fio_dev=$1
    local tmpfiodir=${logdir}/fio
    local fio_log=${tmpfiodir}/${fio_dev}_thread1_randrw_cycle${c}.log
    if [ "$fio_mode" != "True" ]; then
        return 0
    fi
    if [ ! -d $tmpfiodir ]; then
        mkdir -p $tmpfiodir
    fi
    fio --name=${tmpfiodir}/${test_name}_$fio_dev \
        --filename=/dev/$fio_dev \
        ${fio_paras[@]} 2>/dev/null >> $fio_log &
}

function fio_other_disks
{
    local tmpfiodir=${logdir}/fio
    if [ "$fio_mode" != "True" ]; then
        return 0
    fi
    if [ ! -d $tmpfiodir ]; then
        mkdir -p $tmpfiodir
    fi
    fio_num=0
    echo -e "\nStarting run fio test..."

    local tmp_fio_count=`get_fio_ps`
    if [ $tmp_fio_count -ne 0 ]; then
        echo "--> There is ${tmp_fio_count} fio process exists," \
             "start killing it."
        kill_ps fio 2> /dev/null
        sleep 3
    fi

    # fio on disks without hotplug disk and os driver
    for dev in ${drives[@]}
    do
        if [ "$dev" == "$os_drive_letter" ] ||
           [ `grep -iPo $dev <<< "${dlist[@]}"` ]; then
            continue
        fi
        local fio_log=${tmpfiodir}/${dev}_thread1_randrw.log
        echo -e "\n${split_line}\n" >> $fio_log
        echo " ---> run fio to partition /dev/$dev"
        fio --name=${tmpfiodir}/${test_name}_$dev \
            --filename=/dev/$dev \
            ${fio_paras[@]} 2> /dev/null >> $fio_log &
        fio_num=$(( $fio_num + 1 ))
    done

    # check fio ps quantity
    if [ "$fio_mode" = "True" ]; then
        echo " ---> wait ${fio_delay}s for fio process running"
        sleep $fio_delay
    fi

    local fio_p_num=`get_fio_ps`
    if [ $fio_num -ne $fio_p_num ]; then
        echo "fio process mis-match with drive quantity."
        echo " - NO Hotplug Disk Quantity: $fio_num"
        echo " - Fio Quantity:   $fio_p_num"
        exit 1
    fi
    echo -e '\ndone!\n'
}

function check_md5
{
    local dev=$1
    if [ "$md5_mode" != "True" ]; then
        return 0
    fi

    echo -e "\nStart creating MD5 file..\n"
    local sn=`disk_sn_get $dev`
    local mount_point=${tmpdir}/${dev}$partition1
    local file=${tmpdir}/${dev}${partition1}/${sn}.tmp

    if [ "$dev" == "$os_drive_letter" ]; then
        continue
    fi

    echo " ---> create 2 GPT partitions on disk /dev/${dev}"
    if [ "$(mount | grep -i /dev/$dev)" ]; then
        mount_point=$(mount | grep -i '$dev' | awk '{print $1}')
        umount -f -R $mount_point
    fi
    parted /dev/$dev rm 2 > /dev/null 2>&1
    parted /dev/$dev rm 1 > /dev/null 2>&1
    echo y | parted /dev/$dev mklabel gpt > /dev/null 2>&1
    parted -s /dev/$dev mkpart md5 0% 50% > /dev/null 2>&1
    parted -s /dev/$dev mkpart fio 50% 100% > /dev/null 2>&1
    partprobe > /dev/null 2>&1
    mkfs.ext4 /dev/${dev}$partition1 > /dev/null 2>&1
    if [ ! -d $mount_point ]; then
        echo " ---> create mount point ${mount_point}"
        mkdir -p $mount_point
    fi
    echo " ---> mount partition /dev/${dev}$partition1 to mount point ${mount_point}"
    mount /dev/${dev}$partition1 $mount_point &> /dev/null
    echo " ---> create ${size}B of file ${file}"
    dd if=/dev/zero of=$file bs=1 count=0 seek=$size 2> /dev/null
    echo -e " --> checking md5sum From:\n    ${file}\nTo:\n    ${logdir}/check_${sn}.md5"
    $md5sum $file > ${logdir}/check_${sn}.md5
    echo -e '\ndone!\n'
    umount -f $mount_point
}

function rechk_md5
{
    local dev=$1
    local err_count=0
    local sn=`disk_sn_get $dev`
    local mount_point=${tmpdir}/${dev}$partition1
    if [ "$md5_mode" != "True" ]; then
        return 0
    fi
    if [ "/dev/$dev" == "$os_drive" ]; then
        continue
    fi
    echo -e "\nStart checking disk /dev/${dev} checksum value..\n"
    echo " ---> mount partition /dev/${dev}$partition1 to mount point ${mount_point}"
    mount /dev/${dev}$partition1 $mount_point &> /dev/null
    echo " ---> check md5sum file ${logdir}/check_${sn}.md5"
    $md5sum -c ${logdir}/check_${sn}.md5 > ${logdir}/re_check_${sn}.log

    local md5_relog=${logdir}/re_check_${sn}.log
    local md5_reret=`awk -F\: '{print $NF}' $md5_relog | tr -d ' '`
    if [ "`echo $md5_reret | awk '{print tolower($1)}'`" != "ok" ]; then
        local err_count=$(( $err_count + 1 ))
    fi
    echo " ---> unmount $mount_point"
    umount -R -f $mount_point &> /dev/null
    echo -e '\ndone!\n'

    if [ $err_count -eq 0 ]; then
        echo "Check $disk_type /dev/$dev md5 checksum PASS."
    else
        echo "Check $disk_type /dev/$dev md5 checksum FAIL.">> ${logdir}/md5_full.log
        echo "Please check '${md5_relog}' for more information.">> ${logdir}/md5_full.log

    fi
}

function format_disks
{
    for dev in ${dlist[@]}
    do
        parted /dev/$dev rm 2 > /dev/null 2>&1
        parted /dev/$dev rm 1 > /dev/null 2>&1

    done
}

function disk_exist_chk
{
    local retry=600
    local operation=$1
    local mark_idx=$2
    local drive_letter=$3
    local not_show=$4
    if [ -z "$not_show" ]; then
        echo "Please $operation the $mark_idx drive $drive_letter"
    fi
    for r in `seq 1 $retry`
    do
        case $disk_type in
            sata)
                local tmp_drives=`get_sd_disks`
                ;;
            nvme)
                local tmp_drives=`get_nvme_disks`
                ;;
        esac
        for dev in ${dlist[@]}
        do
            if [ "$dev" != "$drive_letter" ]; then
                continue
            fi
            local get_dev_num=`grep -cE "${dev}$" /proc/partitions`
            case $operation in
                remove)
                    if [ $get_dev_num -eq 0 ]; then
                        echo " ---> the $mark_idx drive $drive_letter has been removed"
                        return 0
                    fi
                    ;;
                insert)
                    if [ $get_dev_num -ne 0 ]; then
                        echo " ---> the $mark_idx drive $drive_letter has been inserted"
                        return 0
                    fi
                    ;;
            esac
        done

        sleep 1
        if [ $r -gt $retry ]; then
            echo "NO. $c check drive link status retry for $r times" \
                 "in each 3s is limited."
            exit 1
        fi
    done
}

function hotplug_test
{
# drives is all disk in test SUT
    dlist=${drives[@]}
    if [ "$disk_list" != "all" ]; then
        dlist=($disk_list)
    fi
    format_disks
    disk_len=${#dlist[@]}
    disk_ls=()
    for i in `seq 0 $(( $disk_len - 1 ))`
        do
        disk_ls[$i]="/dev/${dlist[$i]}"
        done
    type_upper=`echo $disk_type | awk '{print toupper($1)}'`

    more << EOF

$split_line
Hotplug Test Arguments:
  - Hotplug Cycle:         $total_cycle
  - Drive Type:            $type_upper
  - System Drive:          $os_drive
  - Disk List:             ${drives[@]}
  - Disk Under Testing:    ${disk_list[@]}
  - Hotplug Mode:          $hp_mode
  - Fio Test:              $fio_mode
  - MD5 Check:             $md5_mode
  - MD5 Check File Size:    $size
$split_line

EOF

if [ ! -d ${logdir}/iostat ]; then
    mkdir -p ${logdir}/iostat
fi
nohup iostat -xmt 1 >> ${logdir}/iostat/iostat_1s.log &

# run fio in unhotplug disks
fio_other_disks

for d in ${dlist[@]}
do
    if [ "$d" == "$os_drive_letter" ]; then
        continue
    fi
    # get disk criteria smart info
    smartinfo_get criteria $d

    # md5 check
    check_md5 $d
done
for c in `seq 1 $total_cycle`
do
    #python3 log-parser/log_parser.py -b
    python3 ../../common_test/log-parser/log_parser.py -b
    echo -e "\n$split_line"
    for d in ${dlist[@]}
    do
        echo -e "`date +%F_%T` NO. $c Starting hotplug $type_upper" \
                "/dev/$d ...\n"
    if [ "$md5_mode" == "True" ]; then
            single_fio ${d}${partition2}
        else
            single_fio $d
        fi
    done
    if [ "$fio_mode" = "True" ]; then
        echo " ---> wait ${fio_delay}s for processing all fio"
        sleep $fio_delay
    fi


    # safety hotplug or unsafety hotplug mode
    if [ "$hp_mode" == "safe_hotplug" -o "$hp_mode" == "unsafe_hotplug" ]; then
        counter=1
        if [ $disk_type == 'nvme' ]; then
            for d in ${dlist[@]}
            do
                if [ "$hp_mode" == "safe_hotplug" ]; then
                    nvme_bdf_long=`readlink -f /sys/block/$d \
                                          | grep -oE $bus_id_regex \
                                          | tail -1`
                    nvme_bdf=`echo $nvme_bdf_long | sed -E 's,^[a-zA-Z0-9]{4}\:,,g'`
                    slot_id=`lspci -s $nvme_bdf -vvv \
                                   | grep -i physical \
                                   | awk -F\: '{print $NF}' \
                                   | sed -E 's,^\ +|\ +$,,g'`
                    echo 1 > /sys/bus/pci/devices/${nvme_bdf_long}/remove
                    echo " ---> the ${counter} drive /dev/$d" \
                         "was safety removed"
                    echo " ---> please remove the drive /dev/$d out manually"
                    sleep 5
                fi
                # remove drive
                disk_exist_chk remove ${counter}th $d
                counter=$(( $counter + 1 ))
            done
        else
            for d in ${dlist[@]}
            do
                disk_exist_chk remove ${counter}th $d
                counter=$(( $counter + 1 ))
            done
        fi
        counter=1
        for d in ${dlist[@]}
        do
            # insert drive
            disk_exist_chk insert ${counter}th $d
            sleep 10
            counter=$(( $counter + 1 ))
        done
    elif [ "$hp_mode" == "linkreset" ]; then
        counter=1
        for d in ${dlist[@]}
        do
            nvme_bdf_long=`readlink -f /sys/block/$d \
                                  | grep -oE $bus_id_regex \
                                  | tail -1`
            nvme_bdf=`echo $nvme_bdf_long | sed -E 's,^[a-zA-Z0-9]{4}\:,,g'`
            slot_id=`lspci -s $nvme_bdf -vvv \
                           | grep -i physical \
                           | awk -F\: '{print $NF}' \
                           | sed -E 's,^\ +|\ +$,,g'`
            echo "`date +%F_%T` No. ${c} starting disk $d linkreset test..."
            echo "poweroff disk $d by cmd: echo 0 > /sys/bus/pci/slots/%{slot_id}/power"
            echo 0 > /sys/bus/pci/slots/%{slot_id}/power
            sleep 5
            disk_exist_chk remove ${counter}th $d unshow
            echo "poweron disk $d by cmd: echo 0 > /sys/bus/pci/slots/%{slot_id}/power"
            echo 1 > /sys/bus/pci/slots/%{slot_id}/power
            sleep 3
            disk_exist_chk insert ${counter}th $d unshow
            counter=$(( $counter + 1 ))
        done
    elif [ "$hp_mode" == "ioreset" ]; then
        counter=1
        for d in ${dlist[@]}
        do
            local nvme_dev=$( echo $d | grep -iPo 'nvme\d+' )
            echo "Start ioreset disk $d by cmd: nvme reset /dev/$nvme_dev"
            nvme reset /dev/$nvme_dev
            sleep 3
            disk_exist_chk insert ${counter}th $d unshow
            counter=$(( $counter + 1 ))
        done
    fi
    for d in ${dlist[@]}
    do
        sleep 10
        # re-check md5
        rechk_md5 $d
    done
    #python lib/collect_smart.py after
    #python3 log-parser/log_parser.py -a
    python3 ../../common_test/log-parser/log_parser.py -a
    sleep 5
    mv ../../common_test/log-parser/reports reports/system_${c}log
    #rm -rf log_parser/*.log
done
        # clear background processes
        kill_ps fio > /dev/null 2>&1
        kill_ps iostat > /dev/null 2>&1

        

for d in ${dlist[@]}
do
        # get drive compare smart info
        smartinfo_get compare $d
        smart_chk $d



done
}

function main
{
    # clean reports dir
    clean_dir "${logdir}"

    # check args
    case $disk_type in
        sata)
            get_os_disk '/dev/sd[a-z]+' sda
            drives=(`get_sd_disks`)
            partition1=1
            partition2=2
            smart_keys=(${sata_smart_keys[@]})
            ;;
        nvme)
            get_os_disk '/dev/nvme[0-9]+\n[0-9]+' nvme0n1
            drives=(`get_nvme_disks`)
            partition1=p1
            partition2=p2
            smart_keys=(${nvme_smart_keys[@]})
            ;;
    esac
    python lib/collect_smart.py before
    hotplug_test
    python lib/collect_smart.py after
    runtime=$(( `date '+%s'` - $s_time ))
    echo -e "\nFinish runing $total_cycle cycles hotplug test"
    echo -e "Summary test time: ${runtime}s\n"
    format_disks
    clean_back_proc
}

# parse arguments
if [ "$#" -eq 0 ]; then
    echo "Invalid arguments, try '-h/--help' for more information."
    exit 1
fi
while [ "$1" != "" ]
do
    case $1 in
        -h|--help)
            usage
            ;;
        -c|--cycle)
            shift
            total_cycle=$1
            ;;
        -t|--type)
            shift
            disk_type=$1
            ;;
        -d|--drives)
            shift
            disk_list="$1"
            ;;
        -ushp|--unsafe-hp)
            hp_mode="unsafe_hotplug"
            ;;
        -shp|--safe-hp)
            hp_mode="safe_hotplug"
            ;;
        -lkreset|--linkreset)
            hp_mode="linkreset"
            ;;
        -ioreset)
            hp_mode="ioreset"
            ;;
        --fio)
            fio_mode=True
            ;;
        --fiopara)
            shift
            fio_paras=$1
            ;;
        --fio-delay)
            shift
            fio_delay=$1
            ;;
        --md5check)
            md5_mode=True
            ;;
        -s|--size)
            shift
            size=$1
            ;;
        -y|--assumeyes)
            assumeyes=True
            ;;
        * ) echo "Invalid arguments, try '-h/--help' for more information."
            exit 1
            ;;
    esac
    shift
done

# clean background process when recive ctrl+C
trap clean_back_proc 2

sumlog="${logdir}/test_summary.log"

clean_dir "${logdir}"
# main
main | tee $sumlog
