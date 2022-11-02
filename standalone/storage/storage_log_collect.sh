#!/bin/bash
#***************************************************************#
# ScriptName: Storage_Log_Collect.sh
# Author: Guo.Buehen
# Function: Collect HDD SSD NVME ocssd vhost RAID Log and check result
#***************************************************************#

path=`pwd`
cd $(dirname $0)

#***************************************************************************************#
# For SATA #
#***************************************************************************************#
function sata_collect
{
for j in {"Raw_Read_Error_Rate","Reallocated_Sector_Ct","UDMA_CRC_Error_Count","Program_Fail_Count","Erase_Fail_Count","Runtime_Bad_Block","End-to-End_Error","Reported_Uncorrect","Offline_Uncorrectable","Command_Timeout","Current_Pending_Sector","Reallocated_Event_Count"}
do
    value1=`cat ./sata_log/$value0 | grep -i $j | awk '{print $1,$2,$NF}'`
        echo -e  "$value1 \t" >> check.log
    value2=`cat ./sata_log/$value0 | grep -i $j | awk '{print $NF}'`
    if  [ -z "$value2"  ];then
        echo -ne "null \t" >> result.log
    elif  [ "$value2" = "0"  ];then
        echo -ne "pass \t" >> result.log
    elif  [ "$value2" != "0"  ];then
        echo -ne "$value2 \t" >> result.log
    fi  
done
#################################################  
value3=`cat ./sata_log/$value0 | grep -C1 "SMART Error Log Version: 1"`
echo -e "$value3 \t" >> check.log
result=$(echo $value3 | grep "No Errors Logged")
if [ -n "$result"  ];then
    echo -ne "pass \t" >> result.log
else
    echo -ne "fail \t" >> result.log
fi
echo -e "\n" >> result.log   
echo >> check.log
echo ------------------------------------------------------------ >> check.log
echo >> check.log
}

function sata_log_check
{
numf=`ls | wc -l`
floder1=`readlink -f  $(dirname $0) | awk -F '/' '{print $NF}'`
if [  "$floder1" != storage_sata_log ];then
    mkdir -p storage_sata_log storage_sata_log/before
    mkdir -p storage_sata_log/before/sata_log 
    cp $(basename $0) ./storage_sata_log
    cd storage_sata_log/before
    sata_log
else
    mkdir -p after after/sata_log
    cd ./after
    sata_log
    cd ../
    diff ./before/result.log  ./after/result.log > check.log
    if  diff ./before/result.log  ./after/result.log ;then
        echo "sata log check pass"
        mv check.log sata_log_check_pass
    else
        echo "sata log check fail"
        mv check.log sata_log_check_fail
        
    fi
fi
}

function sata_log
{
if [[ "$DEV" =~ "sd" ]];then
    value0=$DEV
    echo -e "[Disk]\t\t[ID_1]\t\t[ID_5]\t\t[ID_199]\t\t[ID_171]\t\t[ID_172]\t\t[ID_183]\t\t[ID_184]\t\t[ID_187]\t\t[ID_198]\t\t[ID_188]\t\t[ID_197]\t\t[ID_196]\t\t[SMART_Error_Log]" >> result.log
    touch check.log
    echo -e "$value0\t" >> check.log
    echo -ne "$value0\t" >> result.log    
    #################################################
    touch ./sata_log/$value0
    smartctl -a /dev/$value0>> ./sata_log/$value0
    sata_collect
else
    os_driver=`df | grep -i /boot | awk '{print $1}' | tr -s '1' ' '`
    dev_list=`lsscsi -t | awk '{print $NF}' | tr -s '-' ' ' | tr -s '\n' ' ' `
    echo -e "[Disk]\t\t[ID_1]\t\t[ID_5]\t\t[ID_199]\t\t[ID_171]\t\t[ID_172]\t\t[ID_183]\t\t[ID_184]\t\t[ID_187]\t\t[ID_198]\t\t[ID_188]\t\t[ID_197]\t\t[ID_196]\t\t[SMART_Error_Log]" >> result.log
    touch check.log
    for i in $dev_list
    do
    value0=`basename $i`
    echo -e "$value0\t" >> check.log
    echo -ne "$value0\t" >> result.log    
    #################################################
    touch ./sata_log/$value0
    smartctl -a $i >> ./sata_log/$value0
    sata_collect
    done
fi
mv result.log 1.txt
column -t 1.txt > result.log
rm -f 1.txt
}


#***************************************************************************************#
# For NVME #
#***************************************************************************************#
function nvme_collect
{
for j in {"critical_warning","media_errors","Warning","num_err_log_entries"}
do
    if [[ "$j" =~ "Warning" ]];then
    value1=`cat ./nvme_log/$value | grep -i $j |grep -v critical | awk '{print $1,$2,$3,$NF}'`
    value2=`cat ./nvme_log/$value | grep -i $j |grep -v critical | awk '{print $NF}'`
    else
    value1=`cat ./nvme_log/$value | grep -i $j | awk '{print $1,$NF}'`
        value2=`cat ./nvme_log/$value | grep -i $j | awk '{print $NF}'`
    fi
    echo -e  "$value1 \t" >> check.log
    if  [ -z "$value2"  ];then
    echo -ne "null \t" >> result.log
    elif [ "$value2" = "0" ];then
    echo -ne "pass \t" >> result.log
    elif [ "$value2" != "0" ];then
    echo -ne "$value2 \t" >> result.log
    fi
done
if [[ "$Vendor" =~ "Memblaze" ]];then
    echo > ./nvme_log/$value\(Memblaze_None\)
    echo "NA" >> result.log
    echo -e "CRC:\t\tNA" >> check.log
elif [[ "$Vendor" =~ "INTEL" ]];then
    value3=`nvme intel smart-log-add /dev/$value | grep 'crc_error_count' | awk '{print $1,$NF}'`
    echo $value3 |awk '{print $NF}' >> result.log
    echo -e "$value3" >> check.log
elif [[ "$Vendor" =~ "SAMSUNG" ]];then
    value4=`nvme intel smart-log-add /dev/$value | grep 'crc_error_count' | awk '{print $1,$NF}'`
    echo $value4 |awk '{print $NF}' >> result.log
    echo -e "$value4" >> check.log
elif [[ "$Vendor" =~ "Micron" ]];then
    value5=`nvme intel smart-log-add /dev/$value | grep 'crc_error_count' | awk '{print $1,$NF}'`
    echo $value5 |awk '{print $NF}' >> result.log
    echo -e "$value5" >> check.log
fi
echo -e "\n" >> result.log
echo >> check.log
echo >> check.log
echo >> check.log
}

function nvme_log_check
{
numf=`ls | wc -l`
floder1=`readlink -f  $(dirname $0) | awk -F '/' '{print $NF}'`
if [  "$floder1" != storage_nvme_log ];then
    mkdir -p storage_nvme_log storage_nvme_log/before 
    mkdir -p storage_nvme_log/before/nvme_log storage_nvme_log/before/lspci_log
    cp $(basename $0) ./storage_nvme_log
    cd storage_nvme_log/before
    nvme_log
else
    mkdir -p after after/lspci_log  after/nvme_log 
    cd ./after
    nvme_log
    cd ../
    diff ./before/result.log  ./after/result.log > check.log
    if  diff ./before/result.log  ./after/result.log ;then
        echo "nvme Log check Pass"
        mv check.log  nvme_Log_check_pass
    else
        echo "nvme log check fail"
        mv check.log  nvme_log_check_fail
    fi
fi
}

function nvme_log
{
if [[ "$DEV" =~ "nvme" ]];then
    echo -e "[Disk]\t\t[Vendor]\t\t[Width]\t\t[UE/CE]\t\t[Critical_warning]\t\t[Media_error]\t\t[Warning_Temperature]\t\t[num_err_log]\t\t[CRC]" >> result.log
    touch check.log
    value=${DEV%%n1*}
    echo -e ""$value"n1\t" >> check.log
    echo -ne ""$value"n1\t" >> result.log
    Vendor=`nvme list | grep -i "$value"n1 | awk '{print $3}'`
    echo -ne "$Vendor\t\t" >> result.log   
#################################################
    address=`readlink -f /sys/block/"$value"n1 | cut -d '/' -f 6 | sed -n 's/:00//p'`
    busid=`echo $address |tr -s ':' '_'`
        if [[ "$address" =~ "pci" ]];then
        address=`readlink -f /sys/block/"$value"n1 | cut -d '/' -f 8`
    busid=`echo $address |tr -s ':' '_'`
        lspci -s $address -vvv > ./lspci_log/$busid\($value\).log
        else
    address=`readlink -f /sys/block/"$value"n1 | cut -d '/' -f 6 | sed -n 's/0000://p'`
    busid=`echo $address |tr -s ':' '_'`
    lspci -s $address -vvv > ./lspci_log/$busid\($value\).log
    fi
    echo -e ""$value"($Vendor)\nWidth" >> check.log
    Cap=`cat ./lspci_log/$busid\("$value"\).log | grep -iw lnkcap |tee -a check.log| cut -d ',' -f 2,3 | sed 's/\\s//g' | sed 's,^\s*,,g;s,\s*$,,g'`
    Sta=`cat ./lspci_log/$busid\("$value"\).log | grep -iw lnksta |tee -a check.log| cut -d ':' -f 2 | cut -d ',' -f 1,2 | sed 's/\\s//g' |sed 's/\s*(ok)//g' | sed 's,^\s*,,g;s,\s*$,,g'`
    if [ "x${Cap}x" = "x${Sta}x" ];then
        echo -en "pass\t\t" >> result.log
    else
        echo -en "fail\t\t" >> result.log
    fi
#################################################
    echo "UESta/CESta" >> check.log
    if grep -iwE "uesta|cesta" ./lspci_log/$busid\("$value"\).log |tee -a check.log| sed 's/NonFatalErr.//g' | grep "+" &> /dev/null;then
        echo -ne "fail\t\t" >> result.log
    else
        echo -ne "pass\t\t" >> result.log
    fi
#################################################
    nvme smart-log /dev/"$value"n1 >> ./nvme_log/"$value"
    nvme_collect
else
    num=`ls -l /dev | grep -iE "nvme[0-9]*$" | wc -l`
    numl=$(($num - 1))
    echo -e "[Disk]\t\t[Vendor]\t\t[Width]\t\t[UE/CE]\t\t[Critical_warning]\t\t[Media_error]\t\t[Warning_Temperature]\t\t[num_err_log]\t\t[CRC]" >> result.log
    touch check.log
    for i in $(seq 0 $numl )
    do
        value=nvme$i
        echo -ne "$value\t\t" >> result.log
        Vendor=`nvme list | grep -i ""$value"n1" | awk '{print $3}'`
        echo -ne "$Vendor\t\t" >> result.log
#################################################
        address=`readlink -f /sys/block/"$value"n1 | cut -d '/' -f 6 | sed -n 's/:00//p'`
        busid=`echo $address |tr -s ':' '_'`
                if [[ "$address" =~ "pci" ]];then
                address=`readlink -f /sys/block/"$value"n1 | cut -d '/' -f 8`
        busid=`echo $address |tr -s ':' '_'`
                lspci -s $address -vvv > ./lspci_log/$busid\($value\).log
                else
        address=`readlink -f /sys/block/"$value"n1 | cut -d '/' -f 6 | sed -n 's/0000://p'`
        busid=`echo $address |tr -s ':' '_'`
        lspci -s $address -vvv > ./lspci_log/$busid\($value\).log
                fi
        echo -e ""$value"($Vendor)\nWidth" >> check.log
        Cap=`cat ./lspci_log/$busid\($value\).log | grep -iw lnkcap |tee -a check.log| cut -d ',' -f 2,3 | sed 's/\\s//g' | sed 's,^\s*,,g;s,\s*$,,g'`
        Sta=`cat ./lspci_log/$busid\($value\).log | grep -iw lnksta |tee -a check.log|cut -d ':' -f 2 | cut -d ',' -f 1,2 | sed 's/\\s//g' | sed 's/\s*(ok)//g' | sed 's,^\s*,,g;s,\s*$,,g'`
        if [ "$Cap" = "$Sta" ];then
            echo -en "pass\t\t" >> result.log
        else
            echo -en "fail\t\t" >> result.log
        fi
#################################################
        echo "UESta/CESta" >> check.log
        if grep -iwE "uesta|cesta" ./lspci_log/$busid\($value\).log |tee -a check.log| sed 's/NonFatalErr.//g' | grep "+" &> /dev/null;then
            echo -ne "fail\t\t" >> result.log
        else
            echo -ne "pass\t\t" >> result.log
        fi
#################################################
        nvme smart-log /dev/"$value"n1 >> ./nvme_log/$value
        nvme_collect
    done
fi
mv result.log 1.txt
column -t 1.txt > result.log
rm -f 1.txt
}


#***************************************************************************************#
# For OCSSD #
#***************************************************************************************#
function ocssd_collect
{
if [[ "$component" =~ "ocssd" ]];then
for j in {"Critical_warning","media_errors","num_err_log","Temperature","CRC"}
do
    if [[ "$j" =~ "Critical_warning" ]];then
    value1=`cat ./ocssd_log/smart-log_$value | grep -i $j | awk '{print $1,$NF}'`
        value2=`cat ./ocssd_log/smart-log_$value | grep -i $j | awk '{print $NF}'`
    elif [[ "$j" =~ "media_errors" ]];then
    value1=`cat ./ocssd_log/smart-log_$value | grep -i $j | grep -v 'host\|bg' | awk '{print $1,$NF}'`
        value2=`cat ./ocssd_log/smart-log_$value | grep -i $j | grep -v 'host\|bg' | awk '{print $NF}'`
    elif [[ "$j" =~ "num_err_log" ]];then
    value1=`cat ./ocssd_log/smart-log_$value | grep -i $j | awk '{print $1,$NF}'`
        value2=`cat ./ocssd_log/smart-log_$value | grep -i $j | awk '{print $NF}'`
    elif [[ "$j" =~ "Temperature" ]];then
    value1=`cat ./ocssd_log/smart-log_$value | grep -i $j | grep -v 'Sensor\|Composite\|C' |awk '{print $1,$2,$3,$NF}'`
        value2=`cat ./ocssd_log/smart-log_$value | grep -i $j | grep -v 'Sensor\|Composite\|C' |awk '{print $NF}'`
    elif [[ "$j" =~ "CRC" ]];then
    value1=`cat ./ocssd_log/smart-log-add_$value | grep -i $j | awk '{print $1,$NF}'`
        value2=`cat ./ocssd_log/smart-log-add_$value | grep -i $j | awk '{print $NF}'`
    fi
       echo -e  "$value1 \t" >> check.log
    if  [ -z "$value2"  ];then
       echo -ne "null \t" >> result.log
    elif [ "$value2" = "0" ];then
       echo -ne "pass \t" >> result.log
    elif [ "$value2" != "0" ];then
       echo -ne "$value2 \t" >> result.log
    fi
done
echo -e "\n" >> result.log
elif [[ "$component" =~ "vhost" ]];then
for j in {"critical_warning","media_errors","Temperature","num_err_log_entries","CRC","thermal_throttle_status","program_fail_count","erase_fail_count"}
do
    if [[ "$j" =~ "critical_warning" ]];then
    value1=`cat ./ocssd_log/smart-log_$value | grep -i $j | awk '{print $1,$NF}'`
        value2=`cat ./ocssd_log/smart-log_$value | grep -i $j | awk '{print $NF}'`
    elif [[ "$j" =~ "media_errors" ]];then
    value1=`cat ./ocssd_log/smart-log_$value | grep -i $j | grep -v 'host\|bg' | awk '{print $1,$NF}'`
    value2=`cat ./ocssd_log/smart-log_$value | grep -i $j | grep -v 'host\|bg' | awk '{print $NF}'`
    elif [[ "$j" =~ "Temperature" ]];then
    value1=`cat ./ocssd_log/smart-log_$value | grep -i $j | grep -i warning | awk '{print $1,$2,$3,$NF}'`
    value2=`cat ./ocssd_log/smart-log_$value | grep -i $j | grep -i warning | awk '{print $NF}'`
    elif [[ "$j" =~ "num_err_log_entries" ]];then
    value1=`cat ./ocssd_log/smart-log_$value | grep -i $j | awk '{print $1,$NF}'`
    value2=`cat ./ocssd_log/smart-log_$value | grep -i $j | awk '{print $NF}'`
    elif [[ "$j" =~ "CRC" ]];then
    value1=`cat ./ocssd_log/smart-log-add_$value | grep -i $j | awk '{print $1,$NF}'`
    value2=`cat ./ocssd_log/smart-log-add_$value | grep -i $j | awk '{print $NF}'`
    elif [[ "$j" =~ "thermal_throttle_status" ]];then
    value1=`cat ./ocssd_log/smart-log-add_$value | grep -i $j | awk '{print $1,$NF}'`
    value2=`cat ./ocssd_log/smart-log-add_$value | grep -i $j | awk '{print $NF}'`
    elif [[ "$j" =~ "program_fail_count" ]];then
    value1=`cat ./ocssd_log/smart-log-add_$value | grep -i $j | awk '{print $1,$NF}'`
    value2=`cat ./ocssd_log/smart-log-add_$value | grep -i $j | awk '{print $NF}'`
    elif [[ "$j" =~ "erase_fail_count" ]];then
    value1=`cat ./ocssd_log/smart-log-add_$value | grep -i $j | awk '{print $1,$NF}'`
    value2=`cat ./ocssd_log/smart-log-add_$value | grep -i $j | awk '{print $NF}'`  
    fi
       echo -e  "$value1 \t" >> check.log
    if  [ -z "$value2"  ];then
       echo -ne "null \t" >> result.log
    elif [ "$value2" = "0" ];then
       echo -ne "pass \t" >> result.log
    elif [ "$value2" != "0" ];then
       echo -ne "$value2 \t" >> result.log
    fi
done
echo -e "\n" >> result.log
fi
echo >> check.log
echo >> check.log
echo >> check.log
}

function ocssd_log_check
{
numf=`ls | wc -l`
floder1=`readlink -f  $(dirname $0) | awk -F '/' '{print $NF}'`
if [  "$floder1" != storage_ocssd_log ];then
    mkdir -p storage_ocssd_log storage_ocssd_log/before 
    mkdir -p storage_ocssd_log/before/ocssd_log storage_ocssd_log/before/lspci_log
    cp $(basename $0) ./storage_ocssd_log
    cd storage_ocssd_log/before
    ocssd_log
else
    mkdir -p after after/lspci_log  after/ocssd_log 
    cd ./after
    ocssd_log
    cd ../
    diff ./before/result.log  ./after/result.log > check.log
    if  diff ./before/result.log  ./after/result.log ;then
        echo "ocssd log check pass"
        mv check.log ocssd_log_check_pass
    else
        echo "ocssd log check fail"
        mv check.log ocssd_log_check_fail
    fi
fi
}

function ocssd_log
{
if [[ "$DEV" =~ "os" ]];then
    echo -e "[Disk]\t\t[Vendor]\t\t[Width]\t\t[UE/CE]\t\t[Critical_warning]\t\t[Media_error]\t\t[num_err_log]\t\t[Warning_Temperature]\t\t[CRC]" >> result.log
    touch check.log
    which "aocnvme" > /dev/null
    if [ $? -eq 0 ];then
    value=`aocnvme lnvm list |grep -i $DEV | awk '{print $1}'`
        aocnvme smart-log /dev/$DEV >> ./ocssd_log/smart-log_$value
    aocnvme lnvm smart-log-add /dev/$DEV >> ./ocssd_log/smart-log-add_$value
    address=`aocnvme lnvm list |grep -i $value | awk '{print $NF}'`
    busid=`echo $address |tr -s ':' '_'`
    else
    value=`ocnvme lnvm list |grep -i $DEV | awk '{print $1}'`
        ocnvme smart-log /dev/$DEV >> ./ocssd_log/smart-log_$value
    ocnvme lnvm smart-log-add /dev/$DEV >> ./ocssd_log/smart-log-add_$value
    address=`ocnvme lnvm list |grep -i $value | awk '{print $NF}'`
    busid=`echo $address |tr -s ':' '_'`
    fi
#################################################
    echo -ne "$value\t\t" >> result.log
    which "aocnvme" > /dev/null
    if [ $? -eq 0 ];then
    Vendor=`aocnvme lnvm list | grep -i $value | awk '{print $3}'`
    else
    Vendor=`ocnvme lnvm list | grep -i $value | awk '{print $3}'`   
    fi
    echo -ne "$Vendor\t\t" >> result.log    
    lspci -s $address -vvv > ./lspci_log/$busid\($value\).log
    echo -e "$value\nWidth" >> check.log
    Cap=`cat ./lspci_log/$busid\($value\).log | grep -iw lnkcap |tee -a check.log| cut -d ',' -f 2,3 | sed 's/\\s//g'`
    Sta=`cat ./lspci_log/$busid\($value\).log | grep -iw lnksta |tee -a check.log| cut -d ':' -f 2 | cut -d ',' -f 1,2 | sed 's/\\s//g'`
    if [ "$Cap" = "$Sta" ];then
        echo -en "pass\t\t"  >> result.log
    else
        echo -en "fail\t\t"  >> result.log
    fi
#################################################
    echo "UESta/CESta" >> check.log
    if grep -iwE "uesta|cesta" ./lspci_log/$busid\($value\).log |tee -a check.log| sed 's/NonFatalErr.//g' | grep "+" &> /dev/null;then
        echo -ne "fail\t\t"  >> result.log
    else
        echo -ne "pass\t\t" >> result.log
    fi
    ocssd_collect
else
device_list=`ls /dev/lnvm*`
device_num=`ls /dev/lnvm* |wc -w`
device_num1=$(($device_num - 1))
echo -e "[Disk]\t\t[Vendor]\t\t[Width]\t\t[UE/CE]\t\t[Critical_warning]\t\t[Media_error]\t\t[num_err_log]\t\t[Warning_Temperature_Time]\t\t[CRC]" >> result.log
touch check.log
for i in $(seq 0 $device_num1 )
do   
    value=lnvm$i
    which "aocnvme" > /dev/null
    if [ $? -eq 0 ];then
        aocnvme smart-log /dev/$value >> ./ocssd_log/smart-log_$value
    device=`aocnvme lnvm list |grep $value |awk '{print $(NF-1)}'`
    aocnvme lnvm smart-log-add $device >> ./ocssd_log/smart-log-add_$value
    address=`aocnvme lnvm list |grep -i lnvm"$i"n1 | awk '{print $NF}'`
    busid=`echo $address |tr -s ':' '_'`
    else
        ocnvme smart-log /dev/$value >> ./ocssd_log/smart-log_$value
    device=`ocnvme lnvm list |grep $value |awk '{print $(NF-1)}'`
    ocnvme lnvm smart-log-add $device >> ./ocssd_log/smart-log-add_$value
    address=`ocnvme lnvm list |grep -i "$value"n1 | awk '{print $NF}'`
    busid=`echo $address |tr -s ':' '_'`
    fi
#################################################
    echo -ne "$value\t\t" >> result.log 
    which "aocnvme" > /dev/null
    if [ $? -eq 0 ];then
    Vendor=`aocnvme lnvm list | grep -i "$value"n1 | awk '{print $3}'`
    else
    Vendor=`ocnvme lnvm list | grep -i "$value"n1 | awk '{print $3}'`   
    fi
    echo -ne "$Vendor\t\t" >> result.log    
    lspci -s $address -vvv > ./lspci_log/$busid\($value\).log
    echo -e "$value\nWidth" >> check.log
    Cap=`cat ./lspci_log/$busid\($value\).log | grep -iw lnkcap |tee -a check.log| cut -d ',' -f 2,3 | sed 's/\\s//g'`
    Sta=`cat ./lspci_log/$busid\($value\).log | grep -iw lnksta |tee -a check.log| cut -d ':' -f 2 | cut -d ',' -f 1,2 | sed 's/\\s//g'`
    if [ "$Cap" = "$Sta" ];then
        echo -en "pass\t\t"  >> result.log
    else
        echo -en "fail\t\t"  >> result.log
    fi
#################################################
    echo "UESta/CESta" >> check.log
    if grep -iwE "uesta|cesta" ./lspci_log/$busid\($value\).log |tee -a check.log| sed 's/NonFatalErr.//g' | grep "+" &> /dev/null;then
        echo -ne "fail\t\t"  >> result.log
    else
        echo -ne "pass\t\t" >> result.log
    fi
    ocssd_collect
done
fi
mv result.log 1.txt
column -t 1.txt > result.log
rm -f 1.txt
}

function vhost_log_check
{
numf=`ls | wc -l`
floder1=`readlink -f  $(dirname $0) | awk -F '/' '{print $NF}'`
if [  "$floder1" != storage_ocssd_log ];then
    mkdir -p storage_ocssd_log storage_ocssd_log/before 
    mkdir -p storage_ocssd_log/before/ocssd_log storage_ocssd_log/before/lspci_log
    cp $(basename $0) ./storage_ocssd_log
    cd storage_ocssd_log/before
    vhost_log
else
    mkdir -p after after/lspci_log  after/ocssd_log 
    cd ./after
    vhost_log
    cd ../
    diff ./before/result.log  ./after/result.log > check.log
    if  diff ./before/result.log  ./after/result.log ;then
        echo "ocssd log check pass"
        mv check.log ocssd_log_check_pass
    else
        echo "ocssd log check fail"
        mv check.log ocssd_log_check_fail
    fi
fi
}

function vhost_log
{
if [[ "$DEV" =~ "oc" ]];then
    echo -e "[Disk]\t\t[Vendor]\t\t[Width]\t\t[UE/CE]\t\t[Critical_warning]\t\t[Media_error]\t\t[Warning_Temperature]\t\t[num_err_log_entries]\t\t[CRC]\t\t[thermal_throttle]\t\t[program_fail]\t\t[erase_fail]" >> result.log
    touch check.log
    which "aocnvme" > /dev/null
    if [ $? -eq 0 ];then
    value=`aocnvme list |grep -i $DEV | awk '{print $1}'`
        aocnvme smart-log $DEV >> ./ocssd_log/smart-log_$value
    aocnvme lnvm smart-log-add $DEV >> ./ocssd_log/smart-log-add_$value
    address=`cat /var/spdk/ocssd.conf |grep -w "${value%%n1*}" |grep -v Dev |awk '{print $3}'|cut -d : -f 3,4 |cut -d '"' -f 1`
    busid=`echo $address |tr -s ':' '_'`
    else
    value=`ocnvme list |grep -i $DEV | awk '{print $1}'`
        ocnvme smart-log $DEV >> ./ocssd_log/smart-log_$value
    ocnvme lnvm smart-log-add $DEV >> ./ocssd_log/smart-log-add_$value
    address=`cat /var/spdk/ocssd.conf |grep -w "${value%%n1*}" |grep -v Dev |awk '{print $3}'|cut -d : -f 3,4 |cut -d '"' -f 1`
    busid=`echo $address |tr -s ':' '_'`
    fi
#################################################
    echo -ne "$value\t\t" >> result.log
    which "aocnvme" > /dev/null
    if [ $? -eq 0 ];then    
    Vendor=`aocnvme list | grep -i "$value" | awk '{print $3}'`
    else
    Vendor=`ocnvme list | grep -i "$value" | awk '{print $3}'`
    fi
    echo -ne "$Vendor\t\t" >> result.log
#################################################   
    lspci -s $address -vvv > ./lspci_log/$busid\($value\).log
    echo -e "$value\nWidth" >> check.log
    Cap=`cat ./lspci_log/$busid\($value\).log | grep -iw lnkcap |tee -a check.log| cut -d ',' -f 2,3 | sed 's/\\s//g'`
    Sta=`cat ./lspci_log/$busid\($value\).log | grep -iw lnksta |tee -a check.log| cut -d ':' -f 2 | cut -d ',' -f 1,2 | sed 's/\\s//g'`
    if [ "$Cap" = "$Sta" ];then
        echo -en "pass\t\t"  >> result.log
    else
        echo -en "fail\t\t"  >> result.log
    fi
#################################################
    echo "UESta/CESta" >> check.log
    if grep -iwE "uesta|cesta" ./lspci_log/$busid\($value\).log |tee -a check.log| sed 's/NonFatalErr.//g' | grep "+" &> /dev/null;then
        echo -ne "fail\t\t"  >> result.log
    else
        echo -ne "pass\t\t" >> result.log
    fi
    ocssd_collect
else 
device_list=`aocnvme list |grep -i ocssd | awk '{print $1}'`
echo -e "[Disk]\t\t[Vendor]\t\t[Width]\t\t[UE/CE]\t\t[Critical_warning]\t\t[Media_error]\t\t[Warning_Temperature]\t\t[num_err_log_entries]\t\t[CRC]\t\t[thermal_throttle]\t\t[program_fail]\t\t[erase_fail]" >> result.log
touch check.log
for value in $device_list
do   
    which "aocnvme" > /dev/null
    if [ $? -eq 0 ];then
    value=`aocnvme list |grep -i $value | awk '{print $1}'`
        aocnvme smart-log $value >> ./ocssd_log/smart-log_$value
    aocnvme lnvm smart-log-add $value >> ./ocssd_log/smart-log-add_$value
    address=`cat /var/spdk/ocssd.conf |grep -w "${value%%n1*}" |grep -v Dev |awk '{print $3}'|cut -d : -f 3,4 |cut -d '"' -f 1`
    busid=`echo $address |tr -s ':' '_'`
    else
    value=`ocnvme list |grep -i $value | awk '{print $1}'`
        ocnvme smart-log $value >> ./ocssd_log/smart-log_$value
    ocnvme lnvm smart-log-add $value >> ./ocssd_log/smart-log-add_$value
    address=`cat /var/spdk/ocssd.conf |grep -w "${value%%n1*}" |grep -v Dev |awk '{print $3}'|cut -d : -f 3,4 |cut -d '"' -f 1`
    busid=`echo $address |tr -s ':' '_'`
    fi
#################################################
    echo -ne "$value\t\t" >> result.log
    which "aocnvme" > /dev/null
    if [ $? -eq 0 ];then    
    Vendor=`aocnvme list | grep -i "$value" | awk '{print $3}'`
    else
    Vendor=`ocnvme list | grep -i "$value" | awk '{print $3}'`
    fi
    echo -ne "$Vendor\t\t" >> result.log  
    lspci -s $address -vvv > ./lspci_log/$busid\($value\).log
    echo -e "$value\nWidth" >> check.log
    Cap=`cat ./lspci_log/$busid\($value\).log | grep -iw lnkcap |tee -a check.log| cut -d ',' -f 2,3 | sed 's/\\s//g'`
    Sta=`cat ./lspci_log/$busid\($value\).log | grep -iw lnksta |tee -a check.log| cut -d ':' -f 2 | cut -d ',' -f 1,2 | sed 's/\\s//g'`
    if [ "$Cap" = "$Sta" ];then
        echo -en "pass\t\t"  >> result.log
    else
        echo -en "fail\t\t"  >> result.log
    fi
#################################################
    echo "UESta/CESta" >> check.log
    if grep -iwE "uesta|cesta" ./lspci_log/$busid\($value\).log |tee -a check.log| sed 's/NonFatalErr.//g' | grep "+" &> /dev/null;then
        echo -ne "fail\t\t"  >> result.log
    else
        echo -ne "pass\t\t" >> result.log
    fi
    ocssd_collect
done
fi
mv result.log 1.txt
column -t 1.txt > result.log
rm -f 1.txt
}


#***************************************************************************************#
# For RAID #
#***************************************************************************************#
function raid_log_check
{
numf=`ls | wc -l`
floder1=`readlink -f  $(dirname $0) | awk -F '/' '{print $NF}'`
if [  "$floder1" != storage_raid_log ];then
    mkdir -p storage_raid_log storage_raid_log/before
    mkdir -p storage_raid_log/before/raid_log 
    cp $(basename $0) ./storage_raid_log
    cd storage_raid_log/before
    raid_log
else
    mkdir -p after after/raid_log
    cd ./after
    raid_log
    cd ../
    diff ./before/result.log  ./after/result.log > check.log
    if  diff ./before/result.log  ./after/result.log ;then
        echo "raid log check pass"
        mv check.log raid_log_check_pass
    else
        echo "raid log check fail"
        mv check.log raid_log_check_fail
    fi
fi
}

function raid_log
{
echo -e "[Disk]\t\t[ID_1]\t\t[ID_5]\t\t[ID_199]\t\t[ID_171]\t\t[ID_172]\t\t[ID_183]\t\t[ID_184]\t\t[ID_187]\t\t[ID_198]\t\t[ID_188]\t\t[ID_197]\t\t[ID_196]\t\t[SMART_Error_Log]" > result.log
touch check.log
dev_id=`megacli -PDList -aALL |grep "^Device Id" | awk '{print $NF}' | tr -s '-' ' ' | tr -s '\n' ' ' `
for i in $dev_id
do
    echo -e "$i\t" >> check.log
    echo -ne "$i\t" >> result.log
    
#################################################
    touch ./raid_log/$i
    if [ `smartctl -a -d megaraid,$i $DEV | grep -ic sat+megaraid` -eq 1 ];then
    smartctl -a -d sat+megaraid,$i $DEV >> ./raid_log/hdd_smart_$i.log
    else
        smartctl -a -d megaraid,$i $DEV >> ./raid_log/hdd_smart_$i.log
    fi  
    for j in {"Raw_Read_Error_Rate","Reallocated_Sector_Ct","UDMA_CRC_Error_Count","Program_Fail_Count","Erase_Fail_Count","Runtime_Bad_Block","End-to-end_Error","Reported_Uncorrect","Offline_Uncorrectable","Command_Timeout","Current_Pending_Sector","Reallocated_Event_Count"}
    do
        value1=`cat ./raid_log/hdd_smart_$i.log | grep -i $j | awk '{print $1,$2,$NF}'`
        echo -e  "$value1 \t" >> check.log
    value2=`cat ./raid_log/hdd_smart_$i.log | grep -i $j | awk '{print $NF}'`
    if  [ -z "$value2"  ];then
    echo -ne "null \t" >> result.log
        elif [ "$value2" = "0" ];then
        echo -ne "pass \t" >> result.log
        elif [ "$value2" != "0" ];then
        echo -ne "$value2 \t" >> result.log
        fi
    done
#################################################  
    value3=`cat ./raid_log/hdd_smart_$i.log | grep -C1 "SMART Error Log Version: 1"`
    echo -e "$value3 \t" >> check.log
    result=$(echo $value3 | grep "No Errors Logged")
    if [ "$result" != "" ];then
    echo -ne "pass \t" >> result.log
    else
    echo -ne "fail \t" >> result.log
    fi
    echo -e "\n" >> result.log   
echo >> check.log
echo ------------------------------------------------------------ >> check.log
echo >> check.log
done
mv result.log 1.txt
column -t 1.txt > result.log
rm -f 1.txt
}

#***************************************************************************************#
function log_check
{
case $component in
    sata)
        sata_log_check
        ;;
    nvme)
        nvme_log_check
        ;;
    ocssd)
        ocssd_log_check
        ;;
    raid)
        raid_log_check
        ;;
    vhost)
        vhost_log_check
        ;;
esac
}


#***************************************************************************************#
function main
{
log_check
}


#***************************************************************************************#
function usage
{
   more << EOF
Usage: 
Single disk¿$0 [option] argv [option] argv
Multi disk¿$0 [option] argv

options:
  -V, --version         display the script version
  -h, --help            display help info
  -c, --component       set disk type
  -d, --device          specify a disk symbol

HDD SSD:
  $0 -c sata
  $0 -c sata -d sdb
NVME¿
  $0 -c nvme 
  $0 -c nvme -d nvme0n1
OCSSD¿
  $0 -c ocssd 
  $0 -c ocssd -d osa
RAID¿
  $0 -c raid -d sda
Vhost:
  $0 -c vhost
  $0 -c vhost -d ocssd0n1
EOF
    exit 0
}


#***************************************************************************************#
# parse arguments #
if [ "$#" -eq 0 ];then
    echo "Invalid arguments, try '-h/--help' for more information."
    exit 1
fi
while [ "$1" != "" ]
do
    case $1 in
        -h|--help)
            usage
            ;;
        -c|--compoent)
            shift
            component=$1
            ;;
    -d|--device)
        shift
        DEV=$1
        ;;
        * ) echo "Invalid arguments, try '-h/--help' for more information."
            exit 1
            ;;
    esac
    shift
done

#***************************************************************************************#
# main #
main
