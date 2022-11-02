#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
from macpath import split
import sys, os, re
c_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(c_path)
from sys import argv
from time import sleep
from shutil import copy, rmtree
from re import search, sub
from platform import platform
from os import popen, mkdir, chmod, listdir, remove, system
from os.path import join, isfile, isdir, basename, splitext
from argparse import ArgumentParser, RawTextHelpFormatter
from itertools import groupby
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir,
        os.pardir
        )
)
sys.path.insert(0, tea_path)
from common.other.log import Logger
from common.file.json_rw import fopen

# Import own modules
sys.path.append('./lib')
from pci_chk import checkpci
from sys_chk import checksys
from disk_chk import Disk_Check



class LogParser(object):

    def __init__(self):
        self.status = 'ERROR'
        self.regex = r'^\[(Lspci|Moclog|Sellog|Sdrlog|Dmesg|Messages)\]\:\s'
        if not isdir('reports'):
            mkdir('reports')

    def clean_syslog(self, blact_white_dict):
        logger.info('Clear system log before test begin...')
        for k, v in blact_white_dict.items():
            if k in ['pci']:
                continue
            logger.info(
                'Starting clear %s logs by running cmd:\n' %k +
                '    %s' %v['clear_cmd']
            )
            log = popen(v['clear_cmd']).read()
            logger.info('Result:\n%s' %log)
            # clear messages while it empty
            if k == 'messages':
                msg_log = fopen(file='/var/log/messages'). \
                                       replace('\n', '')
                while search(r'\d+|\w+', msg_log):
                    log = popen(v['clear_cmd']).read()

    def collect_syslog(self, logs):
        for k, v in logs.items():
            if 'ipmi_cmd' in v:
                for e in v['ipmi_cmd']:
                    name = e.split(':')[0].strip()
                    cmd = e.split(':')[1].strip()
                    log = popen(cmd).read()
                    fopen(
                        file='reports/{0}.log'.format(name),
                        content=log,
                        mode='w'
                    )
            else:
                log = popen(v['cmd']).read()
                fopen(
                    file='reports/{0}.log'.format(k),
                    content=log,
                    mode='w'
                )

    def sdr_check(self):
        sdr_logs = fopen(file='reports/sdr.log').splitlines()
        sdr_logs = [ e.strip() for e in sdr_logs if e.strip() ]
        err_list = []
        for e in sdr_logs:
            status = e.split('|')[2].strip().lower()
            if status in ['ok', 'ns']:
                continue
            else:
                err_list.append(e)
        if len(err_list) > 0:
            logger.info('SDR log check FAIL')
            fopen(
                file='reports/errors.log',
                content='### Below is SDR error log ###\n' + '\n'.join(err_list),
                mode='a'
            )
        else:
            logger.info('SDR log check PASS')
    def sdr_check_1(self,logfile, logtype):
        err_list = []
        log_list = fopen(file=logfile).splitlines()
        log_list = [ l.strip() for l in log_list if l.strip() ]
        for l in log_list:
            status = l.split('|')[4].strip().lower()
            if status == '':
                continue
            for sdr_err in bw_dict[logtype]['sdr_black_list']:
                if status in sdr_err:
                    err_list.append(l)
                
        if len(err_list) > 0:
            logger.info('SDR log check FAIL')
            fopen(
                file='reports/errors.log',
                content='### Below is SDR error log ###\n' + '\n'.join(err_list),
                mode='a'
            )
        else:
            logger.info('SDR log check PASS')
            
    def raid_check(self,logfile):
        if not os.path.exists("logs/frist.log"):
            raid_logs = fopen(file=logfile).splitlines()
            raid_logs = [ l for l in raid_logs if l.strip() ]
            phy_error_counters = []
            for raid_data in raid_logs:
                if 'Phy_No' in raid_data:
                    num = raid_logs.index(raid_data)
                    phy_error_counters.extend(raid_logs[num:num+10])
                elif 'EID' in raid_data:
                    num0 = raid_logs.index(raid_data)
                    phy_error_counters.extend(raid_logs[num0:num0+28])
                elif 'Drive-ID' in raid_data:  
                    num1 = raid_logs.index(raid_data)
                    phy_error_counters.extend(raid_logs[num1:num1+8])
                        
            for phy_counter in phy_error_counters:
                        # phy_counter.strip()
                print(phy_counter)
                fopen(
                        file='logs/frist.log',
                        content=phy_counter,
                        mode='a'
                    )
        raid_logs = fopen(file=logfile).splitlines()
        raid_logs = [ l for l in raid_logs if l.strip() ]
        phy_error_counters1 = []
        for raid_data in raid_logs:
            if 'Phy_No' in raid_data:
                num = raid_logs.index(raid_data)
                phy_error_counters1.extend(raid_logs[num:num+10])
            elif 'EID' in raid_data:
                num0 = raid_logs.index(raid_data)
                phy_error_counters1.extend(raid_logs[num0:num0+28])
            elif 'Drive-ID' in raid_data:  
                num1 = raid_logs.index(raid_data)
                phy_error_counters1.extend(raid_logs[num1:num1+8])
                        
        for phy_counter in phy_error_counters1:
            fopen(
                    file='reports/other.log',
                    content=phy_counter,
                    mode='a'
                )
        frist_logs = fopen(file="logs/frist.log").splitlines()
        other_logs = fopen(file="reports/other.log").splitlines()
        if len(frist_logs) == len(other_logs):
            for i in range(2,len(other_logs)):
                if frist_logs[i] != other_logs[i]:
                    logger.info('%s log check FAIL' %(os.path.basename(logfile).split('.')[0]))
                    fopen(
                        file='reports/errors.log',
                        content='### Below is %s error log ###\n' %os.path.basename(logfile).split('.')[0] + ''.join(other_logs[i]),
                        mode='a'
                    )
        
        logger.info('%s log check PASS' %(os.path.basename(logfile).split('.')[0]))
          
    def check_log(self, logfile, logtype):
        err_list = []
        log_list = fopen(file=logfile).splitlines()
        log_list = [ l for l in log_list if l.strip() ]
        for l in log_list:
            for err in bw_dict[logtype]['black_list']:
                if re.search(r'\s+%s' % err, l, re.I):
                    err_list.append(l)
                    break
            for wt in bw_dict[logtype]['white_list']:
                if re.search(wt, l, re.I) and l in err_list:
                    err_list.remove(l)
                    break
        if len(err_list) > 0:
            logger.info('%s log check FAIL' %(os.path.basename(logfile).split('.')[0]))
            fopen(
                file='reports/errors.log',
                content='### Below is %s error log ###\n' %os.path.basename(logfile).split('.')[0] + '\n'.join(err_list),
                mode='a'
            )
        else:
            logger.info('%s log check PASS' %(os.path.basename(logfile).split('.')[0]))

    def pci_check(self):
        pci_info = checkpci(keys=bw_dict["pci"]["white_list"])
        if pci_info():
            logger.info('Lspci info check PASS')
        else:
            logger.info('Lspci info check FAIL')

    def disk_check(self):
        diskobjch = Disk_Check(key=other_bw_dict['diskinfo'])
        diskcheckflag,diskchecklog = diskobjch.smartlog_check()
        if diskcheckflag:
            if diskchecklog:
                logger.info('No Disk need check')
            else:
                logger.info('Disk info check PASS')
        else:
            logger.info('Disk info check Fail')
            with open('reports/errors.log',"a") as f:
                f.write("### Below is disk error log ###\n")
                for errinfo in diskchecklog:
                    f.write(errinfo)
                    f.write('\n')

    def disk_collect(self,teststate=None):
        diskobjco = Disk_Check(state=teststate)
        diskobjco.smartlog_save()

    def cleanlog(self, logpath='reports/', dirsave=False):
        if not dirsave:
            rmtree(logpath)
            self.__init__()
        else:
            for r in logname_list:
                if os.path.exists(r) and not os.path.isdir(r):
                    os.remove(r)
            self.__init__()
        
    def logparse(self):
        # check all logs are exist
        logger.info('\nStarting check log in reports folder' + \
              ' log...\n')
        if isfile('reports/errors.log'):
            remove('reports/errors.log')
            self.__init__()

        lnm_list = [ os.path.basename(l) for l in logname_list ]
        for log in os.listdir('reports'):
            if log not in lnm_list and log != 'errors.log':
                print('log "%s" in reports will not parser, please modify it as format "%s"' %(log, lnm_list))
            elif log == 'sel.log':
                self.check_log('reports/sel.log', 'bmc')
            elif log == 'dmesg.log':
                self.check_log('reports/dmesg.log', 'dmesg')
            elif log == 'messages.log':
                self.check_log('reports/messages.log', 'messages')
            elif log == 'sdr.log':
                # self.sdr_check()
                self.sdr_check_1('reports/sdr.log', 'bmc')
            elif log == 'raid.log':
                self.raid_check('reports/raid.log')
            elif log == 'pci.log':
                self.pci_check()
            elif log == 'diskinfo':
                if diskcheck:
                    self.disk_check()
                
            
if __name__ == '__main__':

    # define global variables
    logname_list = [
        'reports/sel.log',
        'reports/sel_vlist.log',
        'reports/sdr.log',
        'reports/pci.log',
        'reports/dmesg.log',
        'reports/messages.log',
        'reports/diskinfo'
        'reports/raid.log'
    ]

    if len(argv) == 1:
        print("Try '-h/--help' for test user guide.")
        raise SystemExit(-1)

    # parse arguments
    parser = ArgumentParser(
        description='Parser Logs',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-a', '--after',
                      action='store_true',
                      help='collect and check system log after normal test finished')
    parser.add_argument('-b', '--before',
                      action='store_true',
                      help='clear system log before normal test begin')
    parser.add_argument('-d', '--diskcheck',
                        action='store_true',
                        help="if want to add disk check must add -d in before and after")
    parser.add_argument('-op', '--onlyparse',
                      action='store_true',
                      help='only parse logs in forder "reports"')
    parser.add_argument('-oc', '--onlycollect',
                      action='store_true',
                      help='only collect system log and not check it')
    parser.add_argument('-otherbwlist', '--otherblackwhitelist',
                      help="if have other black_white list please add -otherbwlist xxxx.json"
                        )

    args = parser.parse_args()
    before = args.before
    after = args.after
    diskcheck = args.diskcheck
    only_par = args.onlyparse
    only_collect = args.onlycollect
    otherbwlist = args.otherblackwhitelist
    logger = Logger(log_file='Result')

    # start test
    chktest = LogParser()

    blk_white_file=os.path.join(c_path, 'data', 'black_white.json')
    # read the black white list table
    with open(blk_white_file) as jrf:
        bw_dict = eval(jrf.read())

    if otherbwlist:
        other_blk_white_file=os.path.join(c_path, 'data', otherbwlist)
        with open(other_blk_white_file) as jrf:
            other_bw_dict = eval(jrf.read())
        bw_dict['bmc']['black_list'].extend(other_bw_dict['bmc']['black_list'])
        bw_dict['bmc']['white_list'].extend(other_bw_dict['bmc']['white_list'])
        bw_dict['bmc']['sdr_black_list'].extend(other_bw_dict['bmc']['sdr_black_list'])

        bw_dict['dmesg']['black_list'].extend(other_bw_dict['dmesg']['black_list'])
        bw_dict['dmesg']['white_list'].extend(other_bw_dict['dmesg']['white_list'])

        bw_dict['messages']['black_list'].extend(other_bw_dict['messages']['black_list'])
        bw_dict['messages']['white_list'].extend(other_bw_dict['messages']['white_list'])

        if 'byte' in otherbwlist:
            bw_dict['pci']['white_list'] = other_bw_dict['pci']['white_list']
    
    # check args
    if before + after + only_par + only_collect != 1:
        print("argument [-b/-a/-op/oc] can only choose one")
        raise SystemExit(-1)

    # parser log in reports only
    if only_par:
        ret = chktest.logparse()
        raise SystemExit(ret)

    # check ipmitool
    '''
    ipmi_log = popen('command -v ipmitool').read().replace('\n', '')
    ipmi_stout = popen('ipmitool 2>&1').read().replace('\n', '')
    if not ipmi_log:
        print("Please install tool 'ipmitool' first")
        raise SystemExit(-1)
    elif 'Could not open device' in ipmi_stout:
        print(ipmi_stout)
        raise SystemExit(-1)
    '''
    # chean reports path
    if before or only_collect:
        chktest.cleanlog()
    elif after:
        chktest.cleanlog(dirsave=True)

    # clear sel/dmesg/message log
    if before:
        chktest.clean_syslog(bw_dict)
        if diskcheck:
            chktest.disk_collect(teststate='before')
    # only collect system logs
    elif only_collect:
        chktest.collect_syslog(bw_dict)
        if diskcheck:
            chktest.disk_collect()
    # only parser logs in reports dir
    elif only_par:
        chktest.logparse()
    # collect and check all system logs
    elif after:
        chktest.collect_syslog(bw_dict)
        if diskcheck:
            chktest.disk_collect(teststate='after')
        chktest.logparse()
