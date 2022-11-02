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


class AMD_SPECPower():
    '''
    description: this is used to test AMD CPECPower test.
    author: Kail
    '''
    def __init__(self, **kwargs):
        '''
        description: init the class vars
        author: Kail
        params: logger, the logfile
                rtime, the run time of monitor CPU Spec Power
        return: None
        '''
        self.logger = kwargs.get('logger', Logger(log_file='amd_specpower'))
        self.rt = kwargs.get('runtime')


    def check_env(self):
        '''
        description: check the reqired environment
        author: Kail
        params: None
        return: None
        '''
        if not os.path.isfile('/opt/AMD/AVT/AVT'):
            self.logger.warn('can not fAVT not installed, please install it manully')
            sys.exit(-1)

    def test(self):
        '''
        description: start AMD SPECPower test
        author: Kail
        params: None
        return: None
        '''
        self.check_env()
#        avt_pow = self.get_avt_power()
#        cpu_usage = popen('top -b -n 1 | grep Cpu').read().split(':')[1].split(',')[0].strip().split()[0]
#        # total_power = popen("ipmitool sdr elist | grep -iE 'Total_Power|Total_PWR' | awk -F '|' '{print $NF}'").read().split()[0].strip()
#        total_power = '500 Watts'
#        print(cpu_usage)
#        print(avt_pow)
#        res_title = 'CPU_UTIL\tSYS_PWR'
#        for i in range(len(avt_pow)):
#            res_title = res_title + '\tCPU%s_PWR' %i
#        for i in range(len(avt_pow)):
#            res_title = res_title + '\tMEM%s_PWR' %i
        cpu_num = len(self.get_avt_power())
        wait_process = subprocess.Popen('sleep %s' %self.rt, shell=True)
        res_title = ['TIME', 'CPU_UTIL', 'SYS_PWR'] + \
                    [ 'CPU%s_PWR' %i for i in range(cpu_num) ] + \
                    [ 'MEM%s_PWR' %i for i in range(cpu_num) ]
        self.logger.info(str(res_title))
        res_list = []
        res_list.append(res_title)
        while wait_process.poll() is None:
            avt_pow = self.get_avt_power()
            cpu_usage = popen('top -b -n 1 | grep Cpu').read().split(':')[1].split(',')[0].strip().split()[0]
            # total_power = '500 Watts'
            total_pow_cmd = "ipmitool sdr elist | grep -iE 'Total_Power|Total_PWR' | awk -F '|' '{print $NF}'"
            try:
                total_power = popen(total_pow_cmd).read().split()[0].strip()
            except:
                self.logger.error('Total power can not be get by runing cmd:\n' + total_pow_cmd)
                sys.exit(-1)
            stime = time.strftime("%Y-%m-%d %X")
            res_list.append(
                [stime, cpu_usage, total_power] +
                [ avt_pow['cpu' + str(i)][0] for i in range(cpu_num) ] +
                [ avt_pow['cpu' + str(i)][1] for i in range(cpu_num) ]
            )
            self.logger.info(str(res_list[-1]))
        res_full = 'full_data.log'
        if os.path.isfile(res_full):
            os.remove(res_full)
        for i in res_list:
            fopen(file=res_full, content=("%-25s" + "%-15s" * (len(i) - 1)) %tuple(i), mode='a')
        res_list.remove(res_title)
        rep_list = []
        for i in range(len(res_list)):
            if i % interval == 0:
                if i != 0:
                    rep_list.append(self.cacul_average(res_tmp))
                res_tmp = []
            res_tmp.append(res_list[i])
        rep_list.append(self.cacul_average(res_tmp))
        rep_list.insert(0, res_title)
        res_log = 'result.log'
        if os.path.isfile(res_log):
            os.remove(res_log)
        for i in rep_list:
            fopen(file=res_log, content=("%-25s" + "%-15s" * (len(i) - 1)) %tuple(i), mode='a')


        
    def cacul_average(self, data):
        if len(data) == 1:
            return data[0]
        avg_list = [[] for i in range(len(data[0]))]
        for d in data:
            for i in d:
                avg_list[d.index(i)].append(i)
        res = []
        for i in range(len(avg_list)):
            if i == 0:
                # 时间取最后一个
                res.append(avg_list[0][-1])
#            elif i == 2:
#                # 功率含单位 Watts
#                pure_num_list = [ float(wa.split()[0].strip()) for wa in avg_list[2] ]
#                res.append(self.max_num(pure_num_list))
            else:
                pure_num_list = [ float(num) for num in avg_list[i] ]
                res.append(self.max_num(pure_num_list))
        return res
    
    def max_num(self, dt_lis):
        sum = 0
        for i in dt_lis:
            sum += i
        return float('%.2f' %(sum / len(dt_lis)))


    def get_avt_power(self):
        res = popen('/opt/AMD/AVT/AVT -module pmm "get_pmdata()"').read().strip().splitlines()
        cpower_dict = {}
        for line in res:
            if 'SktPwr' in line:
                cpu_id = line.split(',')[0].strip().split(':')[1].rstrip(']')
                cpu_power = line.split(',')[1].strip().split(':')[1].strip()
                mem_power = line.split(',')[2].strip().split(':')[1].strip()
                cpower_dict['cpu' + cpu_id] = [cpu_power, mem_power]
        return cpower_dict
            


if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(
        description='AMD CPU Spec Power Test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-rt', '--runtime',
                        type=int, required=True,
                        help='the client IP which to ping with'
    )
    parser.add_argument('-it', '--interval',
                        type=int,
                        default=10,
                        help='the interval of taking the average value'
    )


    group1 = parser.add_argument_group(
        'run time 300s, take the average value every 10 lines',
        'python %(prog)s ' +
        '-rt 300 -it 10'
    )
    

    args = parser.parse_args()
    rtime = args.runtime
    interval = args.interval

    result = dict()
    result['err_msg'] = []

    start = AMD_SPECPower(runtime=rtime)
    start.test()
