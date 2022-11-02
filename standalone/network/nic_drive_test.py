#!/usr/bin/python3

import sys, os, time, re
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



class NIC_drive_test():
    '''
    description: this is used to test NIC drive self test.
    author: Kail
    '''
    def __init__(self, **kwargs):
        '''
        description: init the class vars
        author: Kail
        params: logger, the logfile
                ip, the ping ip
                cycles, the drive selftest cycle number
        return: None
        '''
        self.logger = kwargs.get('logger', Logger(log_file='nic_drive_selftest'))
        self.cycles = kwargs.get('cycles')
        self.ip = kwargs.get('ip')


    def run_test(self):
        '''
        description: single function up/down test
        author: Kail
        params: None
        return: None
        '''
        self.logger.info("clear demsg log...")
        ret = system('dmesg -c')
        nic_info_dict = get_nic_ip()
        nic_list = [ nic for nic in nic_info_dict.keys()]
        for c in range(1, cycles + 1):
            self.logger.info(
                "\n" + "-" * 80 + "\n" +
                "Starting cycle %s test..." %c +
                "\n" + "-" * 80
            )
            for nic in nic_list:
                self.logger.info("NIC %s drive selftest..." %nic)
                res = popen('ethtool -t %s' %nic).read().strip()
                time.sleep(2)
                self.logger.info('\n' + res)
                chk_res = self.nic_drive_test(res)
                if chk_res:
                    self.logger.info('NIC %s drive check pass\n' %nic)
                else:
                    result['err_msg'].append('NIC %s drive cycle %s check fail' %(nic, c))
                    self.logger.error(result['err_msg'][-1])
            ret = system('ping -c 4 ' + self.ip)
            if ret:
                result['err_msg'].append('ping ip %s fail' %self.ip)
                self.logger.error(result['err_msg'][-1])
            else:
                self.logger.info('ping ip %s pass' %self.ip)
        dmesg_err_msg = Logchk().chk_dmesg()
        if dmesg_err_msg:
            result['err_msg'].append('dmesg check fail')
            self.logger.error(result['err_msg'][-1] + ':\n' + dmesg_err_msg)
        else:
            self.logger.info('dmesg check pass')

                
    def nic_drive_test(self, res):
        '''
        description: check the result of cmd 'ethtool -t NIC'
        author: Kail
        params: res, the output of cmd 'ethtool -t NIC', eg:
            The test result is PASS
            The test extra info:
            nvram test        (online)       0
            link test         (online)       0
            register test     (offline)      0
            memory test       (offline)      0
            mac loopback test (offline)      0
            phy loopback test (offline)      0
            ext loopback test (offline)      0
            interrupt test    (offline)      0
        return: [True, False], True is pass and False is fail
        '''
        res_rgx = r'The test result is.*'
        res = re.search(res_rgx, res).group().strip().split()[-1]
        if res.lower() == 'pass':
            return True
        else:
            return False
        


if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(
        description='NIC drive self test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-c', '--cycle', 
                        type=int, default=100,
                        help='the NIC drive selftest cycles number'
    )
    parser.add_argument('-ip', '--pingip',
                        type=str, default='10.67.13.194',
                        help='the client IP which to ping with'
    )

    group1 = parser.add_argument_group(
        'Ping ip 10.67.13.50, run 10 cycle',
        'python %(prog)s ' +
        '-ip 10.67.13.50 ' +
        '-c 10'
    )

    args = parser.parse_args()
    pingip = args.pingip
    cycles = args.cycle
    
    result = dict()
    result['err_msg'] = []

    test = NIC_drive_test(cycles=cycles, ip=pingip)
    test.run_test()
    summary_res = 'fail' if result['err_msg'] else 'pass'
    result['Summary'] = summary_res
    result['Logfile'] = test.logger.log_file

    fopen(file='summary.log', content=result, mode='w', json=True)
