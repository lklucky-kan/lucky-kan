#!/usr/bin/python3

import sys, os, time, re, subprocess
from argparse import ArgumentParser, RawTextHelpFormatter
from os import popen, system
from json import dumps
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
from common.file.excel import Excel


class iostat_parse():
    '''
    description: this is used to test NIC promisc test.
    author: Kail
    '''
#    def __init__(self, **kwargs):
#        '''
#        description: init the class vars
#        author: Kail
#        params: logger, the logfile
#                ip, the ping ip
#                cycles, the NIC promisc test cycle number
#        return: None
#        '''
#        self.logger = kwargs.get('logger', Logger(log_file='nic_promisc'))
#        self.cycles = kwargs.get('cycles')
#        self.ip = kwargs.get('ip')


    def logparse(self):
        '''
        description: parser iostat logs
        author: Kail
        params: None
        return: None
        '''
        log_msg = fopen(logfile)
        log_list = []
        for l in log_msg.splitlines():
            if l.startswith('nvme'):
                log_list.append(l)
        # self.avg_value(log_list)
        nvme_list = popen("grep -iPo '^nvme\d+n\d+' %s | sort | uniq" %logfile).read().strip().splitlines()
        self.avg_value(log_list, nvme_list)


    def avg_value(self, vlist, nvme_list):
        nvme_vdict = {}
        nvme_vlist = []
        nvme_vlist_tmp = [ None for i in nvme_list ]
        for l in vlist:
            nvme_dev = l.split()[0]
            speed = l.split()[rw_idx]
            nvme_vlist_tmp[nvme_list.index(nvme_dev)] = speed
            if nvme_dev == nvme_list[-1]:
                nvme_vlist.append(nvme_vlist_tmp)
                nvme_vlist_tmp = [ None for i in nvme_list ]
        if [ i for i in nvme_vlist_tmp if i ]:
            nvme_vlist.append(nvme_vlist_tmp)
        nvme_valid_list = [ l for i, v in enumerate(nvme_vlist) if v[0] is None and nvme_vlist[i - 1][0] is not None for l in nvme_vlist[i-30:i+10] ]
        # plug_dev = [ [i  for i, v in enumerate(l) if v is None ] for l in nvme_valid_list if None in l ]
        for l in nvme_valid_list:
            if None in l:
                plug_dev_idx = [ i for i, v in enumerate(l) if v is None ]
                break
        plug_dev = [ nvme_list[i] for i in plug_dev_idx ]
        unplug_dev = [ d for d in nvme_list if d not in plug_dev ]
        avg_value_dict = {}
        for l in nvme_valid_list:
            for i, v in enumerate(l):
                if i in plug_dev_idx:
                    continue
                if nvme_list[i] not in avg_value_dict.keys():
                    avg_value_dict[nvme_list[i]] = []
                else:
                    avg_value_dict[nvme_list[i]].append(v)
        for k, v in avg_value_dict.items():
            avg_v = float('%.2f' %(sum([ float(i) for i in v ]) / len(v)))
            avg_value_dict[k] = avg_v
        remove_idx_list = [ i for i, v in enumerate(nvme_valid_list) if v[0] is None and nvme_valid_list[i-1][0] is not None ]
        # print(remove_idx_list)
        count_num = 0
        perent_change_list = []
        ba_plug = []
        for d in unplug_dev:
            ba_plug.append(d)
            ba_plug.append('Before_plug')
            ba_plug.append('After_plug')
        perent_change_list.append(['Hot remove time'] + ba_plug )
        input(perent_change_list)
        for i in remove_idx_list:
            count_num += 1
            change_temp = [ count_num ]
            for idx, v in enumerate(nvme_valid_list[i]):
                if v is None:
                    continue
                v = float(v)
                nvme_valid_list[i-1][idx] = float(nvme_valid_list[i-1][idx])
                change_v = int(v - nvme_valid_list[i-1][idx] if v > nvme_valid_list[i-1][idx] else nvme_valid_list[i-1][idx] - v)
                change_percent = '%.2f%%' %((change_v / nvme_valid_list[i-1][idx]) * 100)
                change_temp.append(change_percent)
                change_temp.append(nvme_valid_list[i-1][idx])
                change_temp.append(v)
            perent_change_list.append(change_temp)
        Excel(xls_nm='Result.xlsx').list_2sheet(list_data=perent_change_list, sheet_name='Result')



if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(
        description='parser iostart logs',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-f', '--file',
                        type=str,
                        help='the iostat log file'
    )
    parser.add_argument_group(
        'Parser iostat log',
        '%(prog)s  -f iostat_1s.log'
    )

    args = parser.parse_args()
    logfile = args.file

    result = dict()
    result['err_msg'] = []

    iostat_title = 'Device            r/s     rMB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wMB/s   wrqm/s  %wrqm w_await wareq-sz     d/s     dMB/s   drqm/s  %drqm d_await dareq-sz  aqu-sz  %util'.split()
    rw_idx = iostat_title.index('w/s')

    test = iostat_parse()
    test.logparse()
#    summary_res = 'fail' if result['err_msg'] else 'pass'
#    result['Summary'] = summary_res
#    result['Logfile'] = test.logger.log_file

#    fopen(file='summary.log', content=result, mode='w', json=True)
