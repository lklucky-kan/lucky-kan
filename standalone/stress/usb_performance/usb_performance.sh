#!/bin/bash
#****************************************************************#
# ScriptName: USB_performance_test.sh
# Author: Mark.Chu
# Version:1.0
#***************************************************************#

#define global variables
cwd=$PWD
script_file=$(basename $0)
default_cycles=100

function usage() {
	more << EOF
	option to run USB_performance_test
	-h, --help   print the help messages and exit
	-c, --cycles  select run cycles(default: ${default_cycles})
	-d, --device  select run test USB device
	exaple: sh USB_performance_test.sh -c 100 -d /dev/sdb1
EOF
	exit 1
}

function keyboard() {
	echo "kill test script"
	if [ $(ps -aux |grep -i ${script_file} |grep -v grep |wc -l ) -ne 0 ]; then
		local p_id=$(ps -aux |grep -i ${script_file} |grep -v grep |awk -F " " '{print $2}')
		kill -9 $p_id
	fi
	exit 9
}

function prepareTest() {
    if [ "$(command -v hdparm)" != "" ]; then
	    echo "hdparm tool already install"
	else
	    unzip $cwd/tool/hdparm.zip -d $cwd/tool/
	    cd  $cwd/tool/hdparm
		./configure ;make ;make install
		sleep 1
		check_cmd hdparm
		cd $cwd
    fi		
}

function check_cmd() {
	local cmd=$1
	if [ "$(command -v $i)" == "" ]; then
	    echo "${cmd} install failed"
		exit 9
	else
		echo "${cmd} install success"
	fi
}

function main() {
	local num=1
	
	if [ "$run_cycles" != "" ]; then
		local test_cycles=${run_cycles}
	else
		local test_cycles=${default_cycles}
	fi
	
	while [ $num -le ${test_cycles} ]
	do
	echo "##########################"
	echo "Now going USB performance test $num"
	echo "##########################"
	
	hdparm -t ${run_device} >>hdparm.txt
	let 'num+=1'
	done
	echo "Test Finished"
}

if [ "$#" -eq 0 ]; then
    echo "Invalid arguments, try '-h/--help' for more information."
	exit 9
fi

while [ "$1" != "" ]
do
	case "$1" in 
		-h|--help)
			usage
			exit 0
			;;
		-c|--cycles)
			shift
			run_cycles=$1
			;;
		-d|--device)
			shift
			run_device=$1
			;;
		*)
			echo "Invalid arguments, try '-h,--help' for more information"
			exit 1
			;;
	esac
	shift
done

#kill script
trap keyboard 2

#test tool check
prepareTest

#test
main
		
