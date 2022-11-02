#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
description: testcase Palos-6384, collect the output nvme output
             for current requirement, tester need to run the script on dut and check the result by themselves.
             In the future this testcase needs to be implemented in test layer in tea if the real server is under test 
             and tester provide the SSD config data like, SSD number, fw file path. currently, we don\'t know the output 
             of each nvme command.
author: houyuhan
'''
import sys
sys.path.insert(0, '..')
from common.infrastructure.server.factory import ServerFactory
from common.communication.local import Local
from common.other.log import Logger


if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '-h':
            print('run this script use: python3 nvme.py')
        else:
            print('please use -h to print help info.')
            sys.exit('wrong cli params.')

    log_file = 'nvme_output.log'

    logger = Logger(log_file=log_file, log_formatter='%(message)s', stdoutput=False)
    local_os = Local(logger=logger)

    # 1、nvme list
    # 2、nvme id-ctrl /dev/nvme0n1
    # 3、nvme id-ns /dev/nvme0n1
    # 4、nvme smart-log /dev/nvme0n1
    # 5、nvme intel smart-log-add /dev/nvme0n1
    # #6、nvme fw-download /dev/nvme0n1 -f fw.bin #需要fw.bin
    # #7、nvme fw-activate /dev/nvme0n1 -s x -a x
    # 8、nvme format /dev/nvme0n1
    # 9、nvme reset /dev/nvme0    
    cmd_list = [
        'nvme list',
        'nvme id-ctrl /dev/nvme0n1',
        'nvme id-ns /dev/nvme0n1',
        'nvme smart-log /dev/nvme0n1',
        'nvme intel smart-log-add /dev/nvme0n1',
        'nvme format /dev/nvme0n1',
        'nvme reset /dev/nvme0'
    ]

    for cmd in cmd_list:
        logger.info('\n' + '*'*50)
        local_os.cmd(cmd)
    
    print(logger.log_file + ' is generated for your reference.')


    

