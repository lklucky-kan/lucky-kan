#!/bin/bash

# Argument Parser
function arg_parse
{
    argvs=$@
    if [ "$#" -eq 0 ]; then
        echo "Please use '-h/--help' for more infomation"
        exit 1
    fi
    while [ "$1" != "" ]
    do
        case $1 in
            -h|--help)
                Usage;;
            -d)
                shift
                dev_list=$1;;
            -c)
                shift
                total_cycle=$1;;
            -delay)
                shift
                fio_delay=$1;;
            -sdr-delay)
                shift
                sdr_delay=$1;;
            -bmc_ip)
                shift
                bmc_ip=$1;;
            -bmc_user)
                shift
                bmc_user=$1;;
            -bmc_passwd)
                shift
                bmc_passwd=$1;;
            
            -n|--no)
                assumeyes=False;;
            --serial)
                serial_mode=True;;
            --fio)
                fio_mode=True;;
            --interact)
                interact_mode=True;;
            --reboot)
                cycle_mode=reboot;;
            --reset)
                cycle_mode=cold_reset;;
            --reboot_dc)
                cycle_mode=reboot_dc;;
            --dc)
                cycle_mode=dc;;
            --ac)
                cycle_mode=ac;;
            -fio-para)
                shift
                fio_para=$1;;
	    -ping)
	        shift
	        ping_ip=$1;;
            * ) echo "Invalid argument, Please use '-h/--help' for more infomation"
                exit 1;;
        esac
        shift
    done
    manual_keyin
    args_check
    check_tool
    global_path
    init_bootloader
}

function Usage
{
    more << EOF
Usage: `basename $0` Arguments:
      -d  test disk eg: '/dev/sdb /dev/sdc'
      -c  power cycle total cycle, pure number
      -delay  sleep time before reboot (unit: minute)
      -sdr-delay  sleep time waiting for sdr ready (unit: minute)
      -n, --no      Stop test when meet error
	  -ping   ping ip when doing cycle test

    Serial Args:
        --serial       Save BMC Serial log 
        -bmc_ip        xx.xx.xx.xx
        -bmc_user      eg : root
        -bmc_passwd    eg : 1111

    Fio Args:
        --fio           do fio when with this argument
        fio default run args： "$fio_args"
        if need change fio args, use arg:
            -fio-para     modify fio args
        --interact      

    Reboot Type:
      --reboot       Reboot by command: reboot
      --reset        Reboot by command: ipmitool raw 0 2 3
      --dc           Reboot by command: ipmitool raw 0 2 2
      --reboot_dc    Run reboot first and run DC after
      --ac           Break power supply by PDU and then power PSU on, power SUT on finilly


      


Run Example:
    Normal Test:
      500 cycles Reboot:
        $0 -c 500 --reboot
      500 cycles Code Reset:
        $0 -c 500 --reset
      500 cycles DC:
        $0 -c 500 --dc
      500 cycles Reboot then 500 cycles DC:
        $0 -c 500 --reboot_dc
      500 cycles AC:
        $0 -c 500 --ac

	Do ping test when doing cycle test:
		$0 -c 500 --reboot -ping "10.67.13.67 192.168.2.158"

    Do Hard disk and whole machine interactive test:
        $0 -c 500 --reboot_dc --interact 

    Run fio with disk when doing cycle test:
      $0 -c 500 --reboot -d "/dev/sdb /dev/sdc" --fio
      If need change fio argument, such as change '--bs=4k' to '--bs=128k':
      $0 -c 500 --reboot -d "/dev/sdb /dev/sdc" --fio -fio-para '--bs=128k'

    Run test non-interactive mode, such as reboot delay 2 minutes, sdr delay 1 minutes, stop when meet failure:
      $0 -c 500 --reboot -d "/dev/sdb /dev/sdc" --fio -delay 2 -sdr-delay 1 -n

    Run get bmc serial on V2 :
      $0 -c 20 --reboot --serial -bmc_ip 192.168.20.20 -bmc_user admin -bmc_passwd admin

EOF
    exit 1
}

function args_check
{
    # check run cycle number
    if [ `echo $total_cycle | grep -cP '^\d+$'` -eq 0 ]; then
        echo "Invalid parameter, total cycles must be pure number, refer '-h/--help' for more infomation."
        exit 1
    fi
    if [ "$cycle_mode" == "None" ]; then
        echo "Invalid reboot type，reboot type must choose from [--reboot, --reboot_dc, --reset, --dc, --ac]"
        exit 1
    fi
    if [ "$fio_mode" == "True" -a "$dev_list" == "" ]; then
        echo "Must add '-d' when doing fio test"
        exit 1
    fi
    if [ "$fio_para" != "" ]; then
        fio_args=`parser_fio_args "$fio_args" "$fio_para"`
    fi
}

function check_tool
{
    # check fio command
    if [ "$fio_mode" == "True" -a "$fio_path" == "" ] ; then
        echo "Please install tool 'fio' first"
        exit 1
    fi

    # check nvme tool
    if [ "`cat /proc/partitions | grep nvme`" ]; then
        if [ -z "$(command -v nvme 2> /dev/null)" ]; then
            echo "There is nvme disk in test machine but no 'nvme' tool installed, please install nvme at first"
            exit 1
        else
            if [ -z "$(find /usr/bin/ -name nvme)" ]; then
                ln -s $(command -v nvme 2> /dev/null) /usr/bin/nvme
            fi
        fi
    fi
}

function manual_keyin
{
    # 交互参数
    if [ -z $fio_delay ]; then
        more << EOF
======================================================================================
Please input delay time before reboot, You can stop test during this time(Unit: minute)
======================================================================================
EOF
        while true
        do
            read -p "Please input pure number range from 1 to 10.(Default 3 minutes when press 'Enter' directly):" fio_delay
            if [ -z $fio_delay ]; then
                fio_delay=3
                break
            elif [ -z "`echo $fio_delay | grep -iP '^\d+$'`" ]; then
                echo "Invalid input, please input pure number"
                continue
            else
                if [ $fio_delay -le 10 -a $fio_delay -ge 1 ]; then
                    break
                else
                    echo "Invalid input, please input pure number range from 1 to 10"
                    continue
                fi
            fi
        done
    fi
    fio_delay_time=$(( $fio_delay * 60 ))

    # If sdr would ready after a few minutes, sleep sdr_delay time
    if [ -z $sdr_delay ]; then
        sdr_delay=0
    fi
}

function gene_env_set
{
    if [ -f $main_path/libs/set_env.sh ]; then
        rm -rf $main_path/libs/set_env.sh
    fi
    cat > $main_path/libs/set_env.sh << EOF
assumeyes=$assumeyes
fio_delay_time=$fio_delay_time
cycle_mode=$cycle_mode
sdr_delay=$sdr_delay
dev_list="$dev_list"
main_args="$main_args"
total_cycle=$total_cycle
ping_ip="$ping_ip"
fio_mode=$fio_mode
fio_args="$fio_dev_args $fio_args"
summary_log=$summary_log
summary_fail_log=$summary_fail_log
nic_log_path=$nic_log_path
disk_log_path=$disk_log_path
smart_log_path=$smart_log_path
sdr_log_path=$sdr_log_path
fio_log_path=$fio_log_path
stop_cycle=$stop_cycle
result_path=$result_path
sys_log_path=$sys_log_path
main_path=$main_path
sel_log_path=$sel_log_path
msg_log_path=$msg_log_path
dmesg_log_path=$dmesg_log_path
lspci_log=$lspci_log
lspci_raw_num=$lspci_raw_num
tmp_log_path=$tmp_log_path
fail_log_path=$fail_log_path
count_file=$count_file
interact_mode=$interact_mode
avme_log_path=$avme_log_path
serial_mode=$serial_mode
serial_log_path=$serial_log_path
bmc_ip=$bmc_ip
bmc_user=$bmc_user
bmc_passwd=$bmc_passwd
EOF

chmod +x $main_path/libs/set_env.sh
}

function global_path
{
    # difine global path vars
    result_path=$main_path/reports
    tmp_log_path=$main_path/tmp
    fio_log_path=$result_path/fio_log/$cycle_mode
    disk_log_path=$result_path/disk_log
    smart_log_path=$disk_log_path/smart_log
    nic_log_path=$result_path/nic_log
    sdr_log_path=$result_path/sdr_log
    fail_log_path=$result_path/fail_log
    lspci_log=$result_path/device_log
    sel_log_path=$result_path/sel_log
    msg_log_path=$result_path/messages_log
    dmesg_log_path=$result_path/dmesg_log
    sys_log_path=$result_path/system_log
    avme_log_path=$result_path/avme_log
    serial_log_path=$result_path/serial_log
    create_path $result_path \
                $tmp_log_path \
                $fio_log_path \
                $disk_log_path \
                $smart_log_path \
                $nic_log_path \
                $sdr_log_path \
                $fail_log_path \
                $lspci_log \
                $sel_log_path \
                $msg_log_path \
                $dmesg_log_path \
                $sys_log_path\
                $avme_log_path\
                $serial_log_path
    stop_cycle=$main_path/"stop_cycle.sh"
    summary_log=$result_path/${cycle_mode}.log
    summary_fail_log=$fail_log_path/summary_fail.log
    count_file=$tmp_log_path/count.log
}
