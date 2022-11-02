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
from re import search


class NVME_Link_Reset():
    '''
    description: this is used to test nvme link reset with IO.
    author: Kail
    '''
    def __init__(self, **kwargs):
        '''
        description: init the class vars
        author: Kail
        params: logger, the logfile
                cycles, the link reset cycle
        return: None
        '''
        self.logger = kwargs.get('logger')
        self.cycles = kwargs.get('cycles')


    def linkreset_test(self):
        '''
        description: nvme link reset test
        author: Kail
        params: None
        return: None
        '''
        nvme_pci_ls = [
            '0000:' + e.split()[0]
            if not search(r'^\w{4,5}\:', e.split()[0])
            else
            e.split()[0]
            for e in popen('lspci | grep -i Non-vol'). \
                           read().splitlines()
        ]
        nvme_bdfs_dic = {
            for p in nvme_pci_ls
        }
        input(nvme_pci_ls)
        for c in range(1, self.cycles + 1):
            logger.info('-' * 20 + 'cycle %s link reset start' %c + '-' * 20 )
            # echo 0 到每个NVMe /sys/bus/pci/slots/${slotID}/power
            self.setPciBus(nvme_pci_ls, 'remove', False)
            time.sleep(10)
            # echo 1 到每个NVMe /sys/bus/pci/slots/${slotID}/power
            self.setPciBus(nvme_pci_ls, 'insert', False)
            time.sleep(10)


    def setPciBus(self, bdfs, operation, display):
        if operation == 'remove':
            opt_val = '0'
        else:
            opt_val = '1'
        bdf_ls = bdfs
        if not isinstance(bdfs, list):
            bdf_ls = [bdfs]
        for e in bdf_ls:
            slot = popen('lspci -s {0} -vvvv | grep -i "physical slot"'.format(e)).read()
            slot_id = slot.replace('\n', '').split(':')[-1].strip()
            if display:
                logger.info('---> set /sys/bus/pci/slots/{0}/power to {1}.'. \
                       format(slot_id, operation))
            fopen(file='/sys/bus/pci/slots/{0}/power'.format(slot_id),
                  content=opt_val,
                  mode='w')


if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(
        description='Nvme Link Reset Test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-c', '--cycle',
                        type=int, default=1000,
                        help='nvme link reset cycle, default 1000'
    )

    parser.add_argument('-d', '--disklist',
                        type=str,
                        help='define the test nvme disk list'
    )


    group1 = parser.add_argument_group(
        'run nvme link reset test with 1000 cycle',
        'python %(prog)s -d "nvme0n1 nvme1n1"'
    )

    args = parser.parse_args()
    cycles = args.cycle
    nvme_list = args.disklist

    result = dict()
    result['err_msg'] = []

    if not nvme_list:
        nvme_list = popen('nvme list | grep -Po "/dev/nvme\d+n\d+"').read().split()

    else:
        nvme_list = [ '/dev/' + i for i in nvme_list.split() ]


    # nvme_info_dic
    for dev in nvme_list:
        bdf = popen('readlink -f /sys/block/' + dev).read().replace('\n', '')
        input(bdf)
    logger = Logger(log_file='link_reset')
    test = NVME_Link_Reset(cycles=cycles, logger=logger)
    test.linkreset_test()
#    summary_res = 'fail' if result['err_msg'] else 'pass'
#    result['Summary'] = summary_res
#    result['Logfile'] = test.logger.log_file

#    fopen(file='summary.log', content=result, mode='w', json=True)
