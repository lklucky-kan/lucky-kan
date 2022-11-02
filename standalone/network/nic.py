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
            print('run this script use: python3 nic.py')
        else:
            print('please use -h to print help info.')
            sys.exit('wrong cli params.')
        


    log_file = 'nic_output.log'

    logger = Logger(log_file=log_file, log_formatter='%(message)s', stdoutput=False)
    local_os = Local(logger=logger)

    prefix_cmd = "lspci|grep -i eth | cut -f1 -d ' ' |xargs -I {} "
   
    cmd_map = {
        'NIC PCIe IOV':prefix_cmd + 'lspci -vvv -s {}|grep "Initial VF"',
        'NIC PCIe ASPM':prefix_cmd + 'lspci -vvv -s {}|grep "ASPM"|grep LnkCtl',
        'NIC PCIe ErrReport':prefix_cmd + 'lspci -vvv -s {}|grep -E "Report errors|UEMsk|CEMsk"',
        'NIC PCIe IO addr':prefix_cmd + 'lspci -vvv -s {}|grep "I/O port"',
        'NIC PCIe Speed':prefix_cmd + 'lspci -vvv -s {}|grep LnkSta: |cut -f 2,4 -d " "',
        'NIC PCIe VPD':prefix_cmd + 'lspci -vvv -s {}|grep "Product Name"|cut -f 2 -d ":"',
        'NIC offload feature':'ifconfig | grep -E "^e" | cut -f1 -d ":" | xargs -I {} ethtool -k {}', #need verify this.
         
    }

    local_os.cmd('lspci|grep -i eth')

    for case, cmd in cmd_map.items():
        logger.info('\n'+ '*'*30 + case + '*'*30)
        local_os.cmd(cmd)
    
    print(logger.log_file + ' is generated for your reference.')


    

