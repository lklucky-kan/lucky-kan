#!/bin/bash

# Change to script path
main_path=$(cd `dirname $0` && pwd)
cd $main_path

repo_path=$main_path/reports
if [ ! -d $repo_path ]; then
    mkdir -p $repo_path
else
    rm -rf $repo_path/*
fi
ac_log=$repo_path/AC.log
sel_log=$repo_path/Sel.log

# Import Libs
chmod +x libs/*
. libs/arg_parser.sh
. libs/common.sh
. libs/global_env.sh
. libs/full_cycle.sh

# Prepare Env
arg_parse "$@"

if [ -f $config_file ]; then
    source $config_file
else
    echo "Config file $config_file not exist，please refer sample.ini and modift the relate config"
    exit 1
fi

function main
{
quebec_show_config
args_check
single_quebec_cycle
}

main | tee $ac_log
