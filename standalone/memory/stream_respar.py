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
from common.other.log import Logger, Log_Manage
from common.file.json_rw import fopen, init_paths
from common.communication.local import Local
from autotest.testLib.nic_lib import get_nic_ip
from autotest.testLib.log_chk import Logchk
import numpy as np
np.set_printoptions(suppress=True)


class Strem_Logparser():
    '''
    description: this is used to parser stream test log.
    author: Kail
    '''
    def __init__(self, **kwargs):
        '''
        description: init the class vars
        author: Kail
        params: logger, the log obj
        return: None
        '''
        self.logger = kwargs.get('logger') if kwargs.get('logger') else Logger(log_file='stream_res_parser')


    def log_parser(self, logs):
        '''
        description: parser logs in log_files list.
        author: Kail
        params: log_files the logs file list
        return: None
        '''
        sum_res = np.zeros(shape=(4,4))
        count = 0
        for log in logs:
            logger.info('start parser log ' + str(log))
            count += 1
            msg = fopen(log).splitlines()
            for line in msg:
                if re.match('Function\s*Best', line):
                    idx = msg.index(line)
            val_list = []
            for m in msg[idx+1:idx+5]:
                val_list.append([float(i) for i in m.split()[1:]])
            val_list = np.array(val_list)
            sum_res += val_list
            avg_val = sum_res/count
            logger.info('current average value\n' + str(avg_val))
        show_info = self.trans_res(avg_val)
        logger.info('Summary average value as below:\n' + str(show_info))
        fopen(file=res_logfile, content=show_info, mode='w')

    def trans_res(self, res_array):
        title_msg = ['Function', 'Best Rate MB/s', 'Avg time', 'Min time', 'Max time']
        head_list = ['Copy:', 'Scale:', 'Add:', 'Triad:']
        array_list = [title_msg]
        for i in range(len(res_array)):
            array_list.append([head_list[i]] + list((('%.1f ' + '%.6f '*(len(res_array[i]) -1))%tuple(res_array[i])).split()))
        show_msg = ('\n'.join([ ("%-15s" + "%-25s" + "%-20s"*3) %tuple(line) for line in array_list]))
        return show_msg



if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(
        description='Strem log parser test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-p', dest='strem_path',
                        type=str,
                        help="the path where 'run_stream_dynamic.py' build in"
    )
    parser.add_argument('-c', dest='cycle',
                        type=int,
                        help="the cycle number strem run"
    )

    group1 = parser.add_argument_group(
        'Run stream 100 cycle, stream buildin path "/root/stream_aocc"',
        'python %(prog)s -c 100 -p /root/stream_aocc'
    )

    args = parser.parse_args()
    cycle = args.cycle
    spath = args.strem_path
    logger = Logger(log_file='stream_res_parser')

    stream_path = os.path.realpath(os.path.join(os.getcwd(), spath))
    stream_tool = os.path.join(stream_path, 'run_stream_dynamic.py')
    report_path = os.path.realpath(os.path.join(os.getcwd(), 'reports'))
    stream_logpath = os.path.realpath(os.path.join(report_path, 'stream_log'))
    res_logfile = os.path.join(report_path, 'result.log')

    local_os = Local(logger=logger)
    init_paths(report_path, stream_logpath)
    Log_Manage(logger=logger).clear_log(report_path, 'y')
    if not os.path.isfile(stream_tool):
        logger.error('run_stream_dynamic.py not found in %s' %spath)
        sys.exit(-1)

    result = dict()
    result['err_msg'] = []

    for c in range(1, cycle + 1):
        logger.info('=' * 30 + 'Start %s cycle test' %c + '=' * 30)
        local_os.cmd('cd %s;./run_stream_dynamic.py > %s' %(stream_path, os.path.join(stream_logpath, 'stream_cycle%s.log' %c)))
    logfiles = [ os.path.join(path, f) for path, dirs, files in os.walk(stream_logpath) for f in files if not f.endswith('.initial')]
    logger.info('\n' + '-' * 80 + '\nStart parser stream logs in folder %s\n' %stream_logpath + '-' * 80)
    test = Strem_Logparser(logger=logger)
    test.log_parser(logs=logfiles)
