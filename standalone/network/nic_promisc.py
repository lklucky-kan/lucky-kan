#!/usr/bin/python3

import sys, os, time, re, subprocess
from argparse import ArgumentParser, RawTextHelpFormatter
from os import popen, system
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
        )
)
sys.path.append(tea_path)
from common.other.log import Logger
from common.file.json_rw import fopen
from autotest.testLib.nic_lib import get_nic_ip
from autotest.testLib.log_chk import Logchk



class NIC_promisc_test():
    '''
    description: this is used to test NIC promisc test.
    author: Kail
    '''
    def __init__(self, **kwargs):
        '''
        description: init the class vars
        author: Kail
        params: logger, the logfile
                ip, the ping ip
                cycles, the NIC promisc test cycle number
        return: None
        '''
        self.logger = kwargs.get('logger', Logger(log_file='nic_promisc'))
        self.cycles = kwargs.get('cycles')
        self.ip = kwargs.get('ip')


    def promisc_test(self):
        '''
        description: NIC promisc cycle test
        author: Kail
        params: None
        return: None
        '''
        ping_process = subprocess.Popen('ping %s > ping.log' %self.ip, shell=True)
        nic_info_dict = get_nic_ip()
        nic_list = [ nic for nic in nic_info_dict.keys()]
        for c in range(1, cycles + 1):
            self.logger.info(
                "\n" + "-" * 80 + "\n" +
                "Starting cycle %s promisc test..." %c +
                "\n" + "-" * 80
            )
            for nic in nic_list:
                cmd_list = [
                    'ifconfig %s promisc' %nic,
                    'ifconfig %s up' %nic,
                    'ifconfig %s -promisc' %nic
                ]
                for cmd in cmd_list:
                    self.logger.info(cmd)
                    res = popen(cmd).read().strip()
                    self.logger.info('result:\n' + res)
        os.killpg(os.getpgid(ping_process.pid), 9)

                
if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(
        description='NIC promisc test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-c', '--cycle', 
                        type=int, default=100,
                        help='the NIC promisc test cycles number'
    )
    parser.add_argument('-ip', '--pingip',
                        type=str, default='10.67.13.194',
                        help='the client IP which to ping with'
    )

    group1 = parser.add_argument_group(
        'Ping ip 10.67.13.50, run 3000 cycle',
        'python %(prog)s ' +
        '-ip 10.67.13.50 ' +
        '-c 3000'
    )

    args = parser.parse_args()
    pingip = args.pingip
    cycles = args.cycle
    
    result = dict()
    result['err_msg'] = []

    test = NIC_promisc_test(cycles=cycles, ip=pingip)
    test.promisc_test()
#    summary_res = 'fail' if result['err_msg'] else 'pass'
#    result['Summary'] = summary_res
#    result['Logfile'] = test.logger.log_file

#    fopen(file='summary.log', content=result, mode='w', json=True)
