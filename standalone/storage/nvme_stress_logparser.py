#!/usr/bin/python3

import sys, os, time, re
from argparse import ArgumentParser, RawTextHelpFormatter
from os import popen, system, listdir, remove, mkdir, makedirs, chdir
from os.path import join, isdir, isfile, dirname, basename, getsize
from shutil import rmtree, copy2, move
from json import dumps
from re import search, match, findall
from collections import OrderedDict
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
        )
)
sys.path.insert(0, tea_path)
from common.other.log import Logger
from common.file.json_rw import fopen



class Stress_Log_Parser():
    '''
    description: this is used to parser stress log.
    author: Kail
    '''
    def __init__(self, **kwargs):
        '''
        description: init the class vars
        author: Kail
        params: logger, the logfile
        return: None
        '''
        self.logger = kwargs.get('logger') if kwargs.get('logger') else Logger(log_file='stress_parser')


    def full_parser(self, logs):
        '''
        description: start parser stress log.
        author: Kail
        params: light_color, the color of light
                dlist, the disk list
        return: None
        '''
        for stress_log in logs:
            log_msg = fopen(file=stress_log)
            sum_v = 0
            line_num = 0
            value_list = []
            for line in log_msg.splitlines():
                v = int(line.split()[1].strip().rstrip(','))
                value_list.append(v)
                sum_v += v
                line_num += 1
            avg_v = float('%.2f' %(sum_v / line_num))
            high10, high5, low5, low10 = self.percent(avg_v, value_list)


    def gen_result(self, log):
        value_list = [ int(float(l.split(',')[1].strip())) for l in fopen(log).splitlines() ]
        line_num = len(value_list)
        avg_v = float('%.2f' %( sum(value_list) / line_num ))
        high10_list, high5_list, low5_list, low10_list = self.percent(avg_v, value_list)
        high10_per = '%.2f' %((len(high10_list) / line_num) * 100) + '%'
        high5_per = '%.2f' %((len(high5_list) / line_num) * 100) + '%'
        low5_per = '%.2f' %((len(low5_list) / line_num) * 100) + '%'
        low10_per = '%.2f' %((len(low10_list) / line_num) * 100) + '%'
        raw_log_nm = '%s' %log.replace('_iops','')
        result_dict[raw_log_nm] = OrderedDict()
        result_dict[raw_log_nm]['data line num'] = line_num
        result_dict[raw_log_nm]['average value'] = avg_v
        result_dict[raw_log_nm]['percent'] = {}
        result_dict[raw_log_nm]['percent']['10% higher percent'] = high10_per
        result_dict[raw_log_nm]['percent']['5% higher percent'] = high5_per
        result_dict[raw_log_nm]['percent']['5% lower percent'] = low5_per
        result_dict[raw_log_nm]['percent']['10% lower percent'] = low10_per
        result_dict[raw_log_nm]['data'] = {}
        result_dict[raw_log_nm]['data']['10% higher data'] = high10_list
        result_dict[raw_log_nm]['data']['5% higher data'] = high5_list
        result_dict[raw_log_nm]['data']['5% lower data'] = low5_list
        result_dict[raw_log_nm]['data']['10% lower data'] = low10_list
        fopen(result_csv, "{0},{1},{2},{3},{4},{5}".format(log, high10_per, high5_per, low5_per, low10_per, avg_v), 'a')
#            print(dumps(result, indent=4))
#            input(123)
#            fopen('result.log', result, 'a', True)


    def percent(self, avg_vaule, value_list):
        high_10pa = avg_vaule * 1.1
        high_5pa = avg_vaule * 1.05
        low_10pa = avg_vaule * 0.9
        low_5pa = avg_vaule * 0.95
        high_10list = []
        high_5list = []
        low_10list = []
        low_5list = []
        for v in value_list:
            if v >= high_10pa:
                high_10list.append(v)
            elif high_5pa <= v < high_10pa:
                high_5list.append(v)
            elif low_10pa < v <= low_5pa:
                low_5list.append(v)
            elif v <= low_10pa:
                low_10list.append(v)
            high_10list.sort()
            high_5list.sort()
            low_5list.sort()
            low_10list.sort()
        return high_10list, high_5list, low_5list, low_10list

    def iost_res_parser(self, logpath):
        logs = [ i for i in listdir(logpath) if i.endswith('.log') ]
        for log in logs:
            self.gen_result(log)
#            value_list = [ int(float(l.split(',')[1].strip())) for l in fopen(log).splitlines() ]
#            avg_v = float('%.2f' %( sum(value_list) / len(value_list) ))
#            high10, high5, low5, low10 = self.percent(avg_v, value_list)
#            self.gen_result(len(value_list), avg_v, high10, high5, low5, low10)

def nvme_info_dict():
    nvme_infodict = {}
    for line in popen('ls -ld /sys/block/nvme*').read().splitlines():
        dev = re.findall(r'/sys/block/nvme\w+',line)[0].split('/')[-1]
        bdf = re.findall(r'0000:\w{2}:\w+\.\w+',line)[1]
        bus_nb = re.findall(r'0000:\w{2}:\w+\.\w+',line)[0]
        slot_id = popen('lspci -s %s -vvvv | grep -i "Physical Slot"' %bdf).read().split(':')[-1].strip()
        nvme_infodict[dev] = {}
        nvme_infodict[dev]['bdf'] = bdf
        nvme_infodict[dev]['slot'] = slot_id
        nvme_infodict[dev]['bus_nb'] = bus_nb
    return nvme_infodict


def merge_log(log_list):
    cri_head = None
    for log in log_list:
        log_head = '.'.join(log.split('.')[:-2])
        input(log_head)


def iostat_parser(log):
    iostat_ti = [
        'Device',
        'r/s',
        'rMB/s',
        'rrqm/s',
        '%rrqm',
        'r_await',
        'rareq-sz',
        'w/s',
        'wMB/s',
        'wrqm/s',
        '%wrqm',
        'w_await',
        'wareq-sz',
        'd/s',
        'dMB/s',
        'drqm/s',
        '%drqm',
        'd_await',
        'dareq-sz',
        'aqu-sz',
        '%util'
    ]
    logname = basename(log)
    hname = logname.rstrip('.log')
    io_dir = join(parser_logs, hname)
    if not isdir(io_dir):
        makedirs(io_dir)
    chdir(io_dir)
    seqtype = logname.split('_')[4]
    if seqtype not in ['randwrite', 'randread', 'randrw', 'rw', 'write', 'read']:
        logger.error(
            'log %s name format not right, please rename it, eg:\n' +
            '   nvme9n1_4kb_8job_128qd_randwrite_iostat.log'
        )
        return False
    if seqtype == 'read':
        col = ['rMB/s']
    elif seqtype == 'write':
        col = ['wMB/s']
    elif seqtype == 'rw':
        col = ['rMB/s', 'wMB/s']
    elif seqtype == 'randread':
        col = ['r/s']
    elif seqtype == 'randwrite':
        col = ['w/s']
    elif seqtype == 'randrw':
        col = ['r/s', 'w/s']

    # res_log = '_'.join(basename(log).split('_')[:-1])
    rf = fopen(log)
    if len(rf.splitlines()) > 30:
        iost_data = rf.splitlines()[10:-10]
    else:
        logger.error('log %s data is too short, please check it' %log)
        sys.exit(-1)
    iost_data = [ [ j.strip() for j in i.split() ] for i in iost_data ]
    if len(iost_data[0]) != len(iostat_ti):
        logger.error('log %s data format not match, use "iostat -xm 1" to collect it' %log)
        sys.exit(-1)
    for c in col:
        rw_tp = 'Read' if match('r', c) else 'Write'
        seq_tp = 'iops.log' if search('rand', seqtype) else 'bw.log'
        logname = '_'.join( [rw_tp, hname, seq_tp] )
        f_log = join(io_dir, logname)
        logger.info('Start parser log %s' %f_log)
        for i in range(len(iost_data)):
            msg = '%s, %s' %( i * 1000, iost_data[i][iostat_ti.index(c)])
            fopen(f_log, msg, 'a')
    system('fio_generate_plots {0} >/dev/null 2>&1'.format(hname.replace('_iostat', '')))
    pic = hname.replace('_iostat', '')  + '-' + seq_tp.rstrip('.log') + '.svg'
    f_pic = join(io_dir, pic)
    if getsize(f_pic) < 20:
        logger.error('pic %s size too small, please check it' %pic)
    copy2(f_pic, pic_dir)
    popen('rm -rf *.svg')
    lp.iost_res_parser(io_dir)



#    pci_dlist = [ [i + 1, float(v[iostat_ti.index('rMB/s')].strip()) ] for i, v in enumerate(iost_data) ]
#    x_list = [ i[0] for i in pci_dlist ]
#    y_list = [ i[1] for i in pci_dlist ]
#    plt.plot(x_list, y_list, 'ro')
#    plt.savefig('./test2.jpg')


def clearReports(dir, assumeyes=False):
    if not isdir(dir):
        logger.info('mkdir %s' %dir)
        mkdir(dir)
        return True
    if not assumeyes:
        ans = input('WARNING:\n    Continue to remove all files' +
                        ' in {0}/* [Y/n]? '.format(dir))
        if ans:
            if ans.lower()[0] not in ['y', 'Y', '']:
                return True

    for e in listdir(dir):
        file = join(dir, e)
        if isdir(file):
            logger.info('---> remove the dir {0}'.format(file))
            rmtree(file)
        else:
            logger.info('---> remove the file {0}'.format(file))
            remove(file)



if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(
        description='nvme stress log parser',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-lp', '--logpath',
                        type=str,
                        help='define the logpath'
    )

    group1 = parser.add_argument_group(
        'parser log logfile',
        'python %(prog)s ' +
        '-f logfile'
    )


    args = parser.parse_args()
    logpath = args.logpath

    result_dict = OrderedDict()

    logger = Logger(log_file='stress_log_parser')
    rep_path = join(os.getcwd(), 'reports')
    clearReports(rep_path)
    raw_logpath = join(rep_path, 'raw_log')
    raw_fiopath = join(raw_logpath, 'fio')
    raw_iostpath = join(raw_logpath, 'iostat')
    parser_logs = join(rep_path, 'parser_log')
    makedirs(parser_logs)
    pic_dir = join(rep_path, 'pic')
    makedirs(pic_dir)
    result_log = join(rep_path, 'result.log')
    result_csv = join(rep_path, 'result.csv')


    stress_log_list = []
    iostat_log_list = []
    # deal raw logs
    logpath = join(os.getcwd(), logpath)
    for path, dlist, flist in os.walk(logpath):
        logs = [ os.path.join(path, d) for d in flist ]
        for l in logs:
            if re.search(r'\.\d+\.log$', l):
                if not isdir(raw_fiopath):
                    makedirs(raw_fiopath)
                logger.info('copy file %s to dir %s' %(l, raw_fiopath))
                copy2(l, raw_fiopath)
                stress_log_list.append(join(raw_fiopath, basename(l)))
            elif re.search(r'iostat.log$', l):
                if not isdir(raw_iostpath):
                    makedirs(raw_iostpath)
                logger.info('copy file %s to dir %s' %(l, raw_iostpath))
                copy2(l, raw_iostpath)
                iostat_log_list.append(join(raw_iostpath, basename(l)))

    csv_title = [
        'Name',
        'Average',
        '10% Per'
    ]

    csv_title = 'log_name,greater than 10%,greater than 5%,less than 5%,less than 10%, avg_value'
    fopen(result_csv, csv_title, 'a')
    lp = Stress_Log_Parser(logger=logger)
    for log in iostat_log_list:
        iostat_parser(log)
    fopen(result_log, result_dict, 'w', True)
#    # merge stress log
#    merge_log(stress_log_list)
#
#    # start test
#    start = Stress_Log_Parser(logger=logger)
#    start.full_parser(logs=stress_log_list)
