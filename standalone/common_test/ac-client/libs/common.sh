#!/bin/bash

function ping_test
{
    local ip=$1
    ping -c 1 $ip >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo pass
    else
        echo fail
    fi
}

function showpass
{
    more << EOF
 _____         _____ _____
|  __ \ /\    / ____/ ____|
| |__) /  \  | (___| (___
|  ___/ /\ \  \___ \\___ \
| |  / ____ \ ____) |___) |
|_| /_/    \_\_____/_____/

EOF
}

function showfail
{
    more << EOF
 ______      _____ _
|  ____/\   |_   _| |
| |__ /  \    | | | |
|  __/ /\ \   | | | |
| | / ____ \ _| |_| |____
|_|/_/    \_\_____|______|

EOF
}

function repeat_trycmd
{
    interval_time=$1
    try_time=$2
    cmd=$3
    show_cmd=$4
    debug_mode=$5
    local res=fail

    if [ "$show_cmd" == "y" ]; then
        echo "Run command: $cmd"
    fi

    for i in `seq 1 $try_time`
    do
        eval $cmd
        ret=$?
        if [ $ret -eq 0 ]; then
            res=pass
            break
        else
            if [ "$debug_mode" == "y" ]; then
                echo "command run unsuccess, sleep $interval_time to retry"
            fi
            sleep $interval_time
        fi
    done
    if [ $res == fail ]; then
        return 1
    else
        return 0
    fi
}

function sleep_progress
{
    local rtime=$1
    for i in `seq 1 $rtime`
    do
        sleep 1
        if [ $i == $rtime ]; then
            printf "${i}\n"
        else
            printf "${i},"
        fi
    done
}
